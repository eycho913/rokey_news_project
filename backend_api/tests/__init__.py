import sys
import os

# Get the directory of the current file (backend_api/tests/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (backend_api/)
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)
