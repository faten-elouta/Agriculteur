"""Rend `services/`, `ui/`, `agents/` et `catalog/` importables depuis les tests
quand pytest est invoqué comme script (`pytest -q`, comme en CI) : en mode
d'import « prepend », pytest ajoute seulement le répertoire de chaque module de
test au sys.path, pas la racine du dépôt.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
