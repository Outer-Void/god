{
  "metadata": {
    "generated": "2025-11-10T07:10:54.726200",
    "platform": "Linux",
    "total": 2,
    "successful": 2,
    "risk_summary": {
      "low": 2,
      "medium": 0,
      "high": 0,
      "critical": 0
    }
  },
  "commands": [
    {
      "name": "2to3-3.12",
      "path": "/data/data/com.termux/files/usr/bin/2to3-3.12",
      "success": true,
      "output": "Usage: 2to3 [options] file|dir ...\n\nOptions:\n  -h, --help            show this help message and exit\n  -d, --doctests_only   Fix up doctests only\n  -f FIX, --fix=FIX     Each FIX specifies a transformation; default: all\n  -j PROCESSES, --processes=PROCESSES\n                        Run 2to3 concurrently\n  -x NOFIX, --nofix=NOFIX\n                        Prevent a transformation from being run\n  -l, --list-fixes      List available transformations\n  -p, --print-function  Modify the grammar so that print() is a function\n  -e, --exec-function   Modify the grammar so that exec() is a function\n  -v, --verbose         More verbose logging\n  --no-diffs            Don't show diffs of the refactoring\n  -w, --write           Write back modified files\n  -n, --nobackups       Don't write backups for modified files\n  -o OUTPUT_DIR, --output-dir=OUTPUT_DIR\n                        Put output files in this directory instead of overwriting the input\n                        files.  Requires -n.\n  -W, --write-unchanged-files\n                        Also write files even if no changes were required (useful with --output-\n                        dir); implies -w.\n  --add-suffix=ADD_SUFFIX\n                        Append this string to all output filenames. Requires -n if non-empty.\n                        ex: --add-suffix='3' will generate .py3 files.\n",
      "error": "/data/data/com.termux/files/usr/bin/2to3-3.12:3: DeprecationWarning: lib2to3 package is deprecated and may not be able to parse Python 3.10+\n  from lib2to3.main import main\n",
      "exit_code": 0,
      "execution_time": 0.4200553894042969,
      "help_flag": "--help",
      "version": "/data/data/com.termux/files/usr/bin/2to3-3.12:3: DeprecationWarning: lib2to3 package is deprecated and may not be able to parse Python 3.10+",
      "risk_level": "low",
      "category": "network",
      "last_modified": "2025-10-18T00:45:20",
      "file_size": 123
    },
    {
      "name": "2to3",
      "path": "/data/data/com.termux/files/usr/bin/2to3",
      "success": true,
      "output": "Usage: 2to3 [options] file|dir ...\n\nOptions:\n  -h, --help            show this help message and exit\n  -d, --doctests_only   Fix up doctests only\n  -f FIX, --fix=FIX     Each FIX specifies a transformation; default: all\n  -j PROCESSES, --processes=PROCESSES\n                        Run 2to3 concurrently\n  -x NOFIX, --nofix=NOFIX\n                        Prevent a transformation from being run\n  -l, --list-fixes      List available transformations\n  -p, --print-function  Modify the grammar so that print() is a function\n  -e, --exec-function   Modify the grammar so that exec() is a function\n  -v, --verbose         More verbose logging\n  --no-diffs            Don't show diffs of the refactoring\n  -w, --write           Write back modified files\n  -n, --nobackups       Don't write backups for modified files\n  -o OUTPUT_DIR, --output-dir=OUTPUT_DIR\n                        Put output files in this directory instead of overwriting the input\n                        files.  Requires -n.\n  -W, --write-unchanged-files\n                        Also write files even if no changes were required (useful with --output-\n                        dir); implies -w.\n  --add-suffix=ADD_SUFFIX\n                        Append this string to all output filenames. Requires -n if non-empty.\n                        ex: --add-suffix='3' will generate .py3 files.\n",
      "error": "/data/data/com.termux/files/usr/bin/2to3:3: DeprecationWarning: lib2to3 package is deprecated and may not be able to parse Python 3.10+\n  from lib2to3.main import main\n",
      "exit_code": 0,
      "execution_time": 0.6018936634063721,
      "help_flag": "--help",
      "version": "/data/data/com.termux/files/usr/bin/2to3:3: DeprecationWarning: lib2to3 package is deprecated and may not be able to parse Python 3.10+",
      "risk_level": "low",
      "category": "network",
      "last_modified": "2025-10-18T00:45:20",
      "file_size": 123
    }
  ]
}