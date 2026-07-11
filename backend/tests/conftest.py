import sys
from pathlib import Path

# quant.py / analysis.py zyja w backend/, nie w backend/tests/. Pytest domyslnie
# dodaje do sys.path katalog testu, nie jego rodzica - bez tego "import quant"
# wywala sie niezaleznie od tego, z jakiego katalogu odpalimy `pytest`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
