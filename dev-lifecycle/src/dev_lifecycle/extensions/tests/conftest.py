import sys
import os

# Compute path relative to this conftest.py
# conftest.py is in src/dev_lifecycle/extensions/tests/
# Need to add src/ to PYTHONPATH
src_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
# Normalize the path
src_dir = os.path.normpath(src_dir)

# Add to sys.path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
