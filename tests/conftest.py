"""Make site/ importable as a package root, and point loader at site/data."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "site"))

# Configure the data dir before any test imports.
from energy import optimizer  # noqa: E402

optimizer.set_data_dir(str(ROOT / "site" / "data"))
