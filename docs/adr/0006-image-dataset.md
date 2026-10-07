# ADR-0006: Paired image set from Defactify / MS COCOAI + MS COCO licenses

**Status**: Accepted (replaces the dataset example in ADR-0004; ADR-0004's approach — a small curated set from public datasets, no live generation, no scraping — still stands)

## Context

ADR-0004 named CIFAKE as an example source. CIFAKE images are 32×32 pixels — too small to judge by eye, so unplayable.

The game shows **pairs**: a real photo and an AI image of the same subject side by side, and the player picks the real one. Matched subjects mean the content itself never gives the answer away ("AI = fantasy art").

Requirements for the image set:

- Real and AI images of the **same subject**, paired.
- Licenses that allow showing images on a public website, with attribution if needed. "Research only" and NonCommercial-research licenses don't clearly cover a public game.
- Images large enough to inspect (≥ ~400px).
- No file property (size, aspect ratio, format, metadata, filename) that reveals the answer.

Candidates rejected: Synthbuster + RAISE (CC BY-NC-SA; RAISE is non-commercial research/education only), CommunityForensics (CC BY-NC-SA, research only), GenImage (ImageNet real images, research only), web-scraped "CC0" sets (uploader can't grant rights to scraped images), Kaggle Shutterstock set (competition terms, stock copyright), DiffusionDB (CC0 but 2022-era art styles, no real photos), CIFAKE (32×32).

## Decision

- **Source**: Defactify / MS COCOAI (Roy et al., CC BY 4.0 per the paper). It generated AI images from MS COCO captions, so every caption has the real COCO photo plus one image per generator — ready-made pairs, no generation needed.
- **Licensing**: each caption is matched back to its COCO photo via COCO's own annotations to read that photo's Flickr license. Only photos under CC BY 2.0, CC BY-SA 2.0, "No known copyright restrictions", or US Government Work are kept. Ambiguous captions (shared by several photos) are dropped. Credits link to the original Flickr photo page.
- **Pairing**: one AI version per real photo, rotating through Stable Diffusion 2.1, SDXL, SD 3, and Midjourney v6 so each generator gets an even share. A player never sees the same real photo twice.
- **Normalization** (`scripts/build_image_set.py`): center-crop to square, downscale to 432×432, re-encode as WebP quality 85 with no metadata, random filenames. 432 is the smallest kept source size (Midjourney v6 is stored at 436px), so every image is downscaled and none upscaled.
- **Starter set**: 212 pairs (424 images), 53 per generator. Reproducible from a fixed seed.

## Consequences

- Every image carries a license and source link in the manifest; the game will show credits.
- DALL-E 3 is excluded: the dataset stores those images at 270×270, and upscaling them would make them visibly blurrier than the rest — a tell.
- The Defactify Hugging Face page lists no license; the CC BY 4.0 grant comes from the paper. Acceptable for a non-commercial portfolio game with credit; revisit (e.g. generate our own AI twins from COCO captions with an Apache-licensed model) if that ever matters.
- COCO photos have Flickr owners; the credit links to the photo page rather than naming the owner, since COCO's metadata doesn't include owner names. Some old Flickr pages may have been deleted.
- 212 pairs is enough for a starter pool. More can come from Defactify's train/test splits with the same script, or from the planned user-upload feature (user photo + description → generated AI twin → admin approval), which will get its own ADR.
- 432px is modest. Fine on phones and laptops side by side; a larger, newer source could replace this without changing the pipeline.
