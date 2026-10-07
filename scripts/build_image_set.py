"""Build the game's curated set of real/AI image pairs from Defactify / MS COCOAI.

Defactify generated AI images from MS COCO captions, so each caption has the real COCO photo
plus one image per AI generator. Each pair here is one real photo and one of its AI versions.
COCO's own annotations are used to find each real photo's Flickr license, and only photos
whose license allows public reuse with attribution are kept.

Images are normalized so file properties can't give the answer away. Writes:

    <out>/images/<id>.webp     square, same size, same format, no metadata, random name
    <out>/manifest.json        one entry per pair: caption, generator, real + ai image with credits
    <out>/contact_sheet.html   local review page

See docs/adr/0006-image-dataset.md for why these sources and these normalization steps.
"""

import argparse
import html
import io
import json
import random
import re
import sys
import uuid
import zipfile
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

# COCO license ids whose terms allow public reuse with attribution.
# 4 = CC BY 2.0, 5 = CC BY-SA 2.0, 7 = No known copyright restrictions, 8 = US Government Work.
# Excluded: the NonCommercial and NoDerivs licenses (1, 2, 3, 6).
ALLOWED_COCO_LICENSES = {4, 5, 7, 8}

REAL_LABEL = 0

# Defactify Label_B values for AI images. 4 = DALL-E 3 is excluded: the dataset stores those
# at 270x270, and upscaling them would make them visibly blurrier than everything else.
GENERATORS = {
    1: "Stable Diffusion 2.1",
    2: "Stable Diffusion XL",
    3: "Stable Diffusion 3",
    5: "Midjourney v6",
}

DEFACTIFY_CREDIT = {
    "source": "MS COCOAI (Defactify)",
    "license": "CC BY 4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "source_url": "https://huggingface.co/datasets/Rajarshi-Roy-research/Defactify_Image_Dataset",
}

WEBP_QUALITY = 85


def normalize(image: Image.Image, size: int) -> bytes:
    """Center-crop to a square, resize to size x size, and encode as metadata-free WebP."""
    image = image.convert("RGB")
    side = min(image.size)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    if side != size:
        image = image.resize((size, size), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    # No exif/icc arguments are passed, so no source metadata is carried over.
    image.save(out, format="WEBP", quality=WEBP_QUALITY, method=6)
    return out.getvalue()


def new_id(rng: random.Random) -> str:
    """Random but reproducible id, so reruns with the same seed produce the same files."""
    return uuid.UUID(int=rng.getrandbits(128), version=4).hex


def min_side(image_bytes: bytes) -> int:
    with Image.open(io.BytesIO(image_bytes)) as probe:  # reads the header only
        return min(probe.size)


def flickr_page_url(flickr_url: str) -> str | None:
    """Turn COCO's static Flickr image URL into a link to the photo's page (which credits the owner)."""
    match = re.search(r"/(\d+)_[0-9a-f]+", flickr_url)
    return f"https://www.flickr.com/photo.gne?id={match.group(1)}" if match else None


def load_coco_credits(annotations_zip: Path) -> dict[str, dict]:
    """Map each COCO caption to the license credit of its photo, for captions that identify one photo
    with a reuse-allowed license."""
    caption_to_images: dict[str, set[int]] = defaultdict(set)
    images: dict[int, dict] = {}
    licenses: dict[int, dict] = {}
    with zipfile.ZipFile(annotations_zip) as zf:
        for name in ("annotations/captions_train2017.json", "annotations/captions_val2017.json"):
            data = json.loads(zf.read(name))
            licenses.update({lic["id"]: lic for lic in data["licenses"]})
            images.update({img["id"]: img for img in data["images"]})
            for ann in data["annotations"]:
                caption_to_images[ann["caption"].strip()].add(ann["image_id"])

    credits = {}
    for caption, image_ids in caption_to_images.items():
        if len(image_ids) != 1:
            continue  # ambiguous caption: can't tell which photo (and license) it belongs to
        img = images[next(iter(image_ids))]
        if img["license"] not in ALLOWED_COCO_LICENSES:
            continue
        lic = licenses[img["license"]]
        credits[caption] = {
            "source": "MS COCO via Flickr",
            "license": lic["name"],
            "license_url": lic["url"],
            "source_url": flickr_page_url(img["flickr_url"]) or img["flickr_url"],
        }
    return credits


def load_defactify_groups(defactify_dir: Path, size: int) -> dict[str, dict[int, bytes]]:
    """Group Defactify images by caption: {caption: {label: image bytes}}, keeping only images
    large enough to downscale to `size`."""
    groups: dict[str, dict[int, bytes]] = defaultdict(dict)
    for path in sorted(defactify_dir.glob("*.parquet")):
        table = pq.read_table(path, columns=["Caption", "Label_B", "Image"])
        for caption, label, image in zip(
            table["Caption"].to_pylist(), table["Label_B"].to_pylist(), table["Image"].to_pylist()
        ):
            if label != REAL_LABEL and label not in GENERATORS:
                continue
            if min_side(image["bytes"]) >= size:
                groups[(caption or "").strip()][label] = image["bytes"]
    return groups


def build_pairs(annotations_zip: Path, defactify_dir: Path, size: int, limit: int | None,
                rng: random.Random, images_dir: Path) -> list[dict]:
    credits = load_coco_credits(annotations_zip)
    groups = load_defactify_groups(defactify_dir, size)

    eligible = sorted(
        caption for caption, imgs in groups.items()
        if caption in credits and REAL_LABEL in imgs and any(label in imgs for label in GENERATORS)
    )
    print(f"{len(groups)} captions; {len(eligible)} with a reuse-allowed real photo and an AI version")
    rng.shuffle(eligible)
    if limit is not None:
        eligible = eligible[:limit]

    pairs = []
    generator_order = list(GENERATORS)
    for i, caption in enumerate(eligible):
        imgs = groups[caption]
        # Rotate through generators so each gets an even share; fall back to any available one.
        preferred = generator_order[i % len(generator_order)]
        label = preferred if preferred in imgs else next(g for g in generator_order if g in imgs)

        real_id, ai_id = new_id(rng), new_id(rng)
        (images_dir / f"{real_id}.webp").write_bytes(normalize(Image.open(io.BytesIO(imgs[REAL_LABEL])), size))
        (images_dir / f"{ai_id}.webp").write_bytes(normalize(Image.open(io.BytesIO(imgs[label])), size))
        pairs.append(
            {
                "id": new_id(rng),
                "caption": caption,
                "generator": GENERATORS[label],
                "real": {"image_id": real_id, "credit": credits[caption]},
                "ai": {"image_id": ai_id, "credit": DEFACTIFY_CREDIT},
            }
        )
    return pairs


def write_contact_sheet(pairs: list[dict], out: Path) -> None:
    def figure(kind: str, side: dict, tag: str) -> str:
        return (
            f'<figure class="{kind}"><img src="images/{side["image_id"]}.webp" loading="lazy">'
            f"<figcaption><b>{html.escape(tag)}</b> · "
            f'<a href="{html.escape(side["credit"]["source_url"])}">{html.escape(side["credit"]["license"])}</a>'
            f"</figcaption></figure>"
        )

    rows = [
        f'<section><p>{html.escape(p["caption"])} <small>· {p["id"][:8]}</small></p><div>'
        f'{figure("real", p["real"], "REAL")}{figure("ai", p["ai"], "AI · " + p["generator"])}</div></section>'
        for p in pairs
    ]
    page = f"""<!doctype html><meta charset="utf-8"><title>Contact sheet</title>
<style>
body{{font:13px system-ui;margin:16px}} main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:16px}}
section p{{margin:0 0 4px}} section div{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}
figure{{margin:0;border:3px solid;border-radius:6px;overflow:hidden}} .real{{border-color:#1a7f37}} .ai{{border-color:#cf222e}}
img{{width:100%;display:block}} figcaption{{padding:4px 6px}}
</style>
<h1>{len(pairs)} pairs</h1><main>{''.join(rows)}</main>"""
    (out / "contact_sheet.html").write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--coco-annotations", type=Path, required=True, help="annotations_trainval2017.zip")
    parser.add_argument("--defactify-dir", type=Path, required=True, help="folder with Defactify .parquet files")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None, help="max pairs (default: all eligible)")
    # 432 = smallest source size we keep (Midjourney v6 is stored at 436), so every image is downscaled.
    parser.add_argument("--size", type=int, default=432)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    images_dir = args.out / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    pairs = build_pairs(args.coco_annotations, args.defactify_dir, args.size, args.limit, rng, images_dir)

    (args.out / "manifest.json").write_text(json.dumps(pairs, indent=2), encoding="utf-8")
    write_contact_sheet(pairs, args.out)
    print(f"Done: {len(pairs)} pairs ({2 * len(pairs)} images) in {args.out}")


if __name__ == "__main__":
    main()
