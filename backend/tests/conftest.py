import os
from pathlib import Path

# app.main loads the pairs manifest at import time, so point it at the fixture before any test
# module imports the app. Tests never need the real (private) manifest.
os.environ["PAIRS_FILE"] = str(Path(__file__).parent / "fixtures" / "pairs.json")
os.environ["IMAGE_BASE_URL"] = "https://images.test"
