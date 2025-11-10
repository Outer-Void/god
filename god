#!/usr/bin/env python3
"""
GOD CLI - Direct Runner
Allows running god directly without installation: ./god <command>
"""

import sys
from pathlib import Path

# Add src to path to allow direct execution
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from god.cli import main_cli
    
    if __name__ == "__main__":
        main_cli()
        
except ImportError as e:
    print(f"❌ Error: Could not import god.cli")
    print(f"   {e}")
    print()
    print("💡 Solutions:")
    print("  1. Run: ./install_deps.sh")
    print("  2. Or: pip install -e .")
    print("  3. Or: source .venv/bin/activate && pip install -e .")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
