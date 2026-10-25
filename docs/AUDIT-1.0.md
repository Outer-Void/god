# Audit of GOD 1.0.1 (Stage 05)

Audited at `699c1d0` (main; PyPI `god-cli` 1.0.1; tag `v1.0.0`). Regression tests are in
`tests/test_boundaries.py` unless noted.

## Isolation defects

1. **GOD executed every program on PATH.** `god build`, `god search` (without `--names-only`) and `god info`
   ran each executable with up to five help flags (`--help`, `-h`, `/?`, `-help`, `help`) and five version
   flags (`--version`, `-V`, `-v`, `/version`, `version`), each attempt running until it printed something:
   - in parallel (up to 32 workers);
   - with the caller's full environment (every token and secret in it);
   - in the caller's working directory;
   - with stdin inherited.

   Many programs treat those arguments as real work, not as a request for help. `shutdown -h` schedules a
   halt, `rm help` deletes a file named `help` if there is one, and anything that reads stdin blocks until
   the timeout. The test suite ran `god build --limit 3` and `god info python` on every developer machine and CI
   runner. *GOD 2 imports no process-spawning module; a canary program on PATH is never run.*
2. **"Risk levels" were a hard-coded list of names** (`rm`, `dd` … critical; `sudo` medium). They were
   presented as a security audit but judged only the file name, and a copy named anything else was "low".
   *Removed.*
3. **`god blux q|dat|lrc|scan` routed into other tools.** It imported guessed module names (`outervoid.dat`,
   which do not exist) and called their `app()`/`main()` in-process with GOD's own `sys.argv`, or fell back
   to running a PATH binary with the caller's environment. That is orchestration, not discovery, and it
   bypassed BLUX policy and receipts. *Removed (`blux run` does this under policy).*
4. **Import side effects.** `import god` imported typer and rich, called `logging.basicConfig` (reconfiguring
   the host application's logging) and created a `Console(force_terminal=True)` that wrote ANSI escapes into
   pipes. *GOD 2 imports nothing heavy, configures nothing, and prints plain text or JSON.*
5. **No BLUX coupling despite the claim.** The README promised "BLUX integration", but nothing read `.blux/`
   (Stage 00 baseline). *GOD 2 reads `.blux/` only through blux-sdk, so it agrees with the runtime.*

## Other defects

- Output depended on the clock (`Generated:` timestamps), the platform and thread completion order.
- One exit code (1) for every failure; errors were logged with tracebacks.
- Version drift: help said v1.0.0, the package 1.0.1, the tag v1.0.0, and `test_version_flag` asserted 1.0.0
  (the only failing test).
- `src/__init__.py` made `src` an importable package.
- The README installed with `curl … install_deps.sh | bash` and suggested `sudo pip install`.
- `scripts/publish.sh` uploaded to production PyPI from a developer machine.
- PATH shadowing was silently resolved (first wins) and never reported.
- `CHANGELOG.md` has two identical `[1.0.1]` entries; kept as history.
