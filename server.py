"""Run oahelper-mcp from a git clone: python server.py

Kept so existing client configs that point at server.py keep working.
Author: Sirjan Singh (https://github.com/SirjanSingh/oahelper-mcp). MIT license.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from oahelper_mcp.server import *  # noqa: F401,F403  (lets `import server` expose the tools)
from oahelper_mcp.server import main

if __name__ == "__main__":
    main()
