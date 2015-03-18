"""Initializes Sets sys.path for scripts to work."""

import os
import sys

repo_dir = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(repo_dir)
