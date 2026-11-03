# Lets the examples import packages/python without installing it (pip install ./packages/python also works).
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packages", "python", "src"))
