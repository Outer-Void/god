<p align="center">
  <img src="./docs/assets/god-logo.png" alt="GOD" width="420">
</p>

# GOD — discovery for the BLUX ecosystem

GOD answers *what exists and what does it declare*: which projects live under a set of directories, which
capabilities they offer, at which versions, through which commands. It reads every `.blux/` through the
canonical BLUX SDK, so it agrees with the BLUX runtime about what is valid.

GOD **owns discovery, not orchestration**. It never runs a capability, never executes a program it finds,
never evaluates a policy, and never routes to other tools. BLUX runs things; GOD tells BLUX (and you) where
they are.

```bash
god capabilities -r ~/src                    # capability.discover
god capability repo.create -r ~/src          # capability.describe
god project lrc -r ~/src                     # project.describe (or: god project path/to/repo)
god compat repo.create --range '^2' -r ~/src # version compatibility lookup
god commands 'lrc*' --declared -r ~/src      # command.discover: PATH, statically, plus entrypoint checks
god index ~/src                              # build/refresh the local registry index
god check ~/src                              # malformed .blux/ and duplicates; exit 1 if any
```

Every command takes `--json` for the machine document. Roots default to `$GOD_ROOTS` (path-separated) or
the current directory. Exit codes: `0` ok, `1` check failed or nothing matched, `2` usage, `3` failed.

## What it reports

- **Problems**: a `.blux/` the SDK rejects (bad YAML with its line, wrong contract, unsupported contract
  version, schema violations, missing files, a capability id repeated inside one project). Each one is a
  finding; every other project is still discovered.
- **Duplicates**: two directories declaring one `project_id`, or one capability id offered by different
  projects. BLUX would refuse to load both, so `describe` asks you to pick a project.
- **Compatibility**: which providers satisfy a semver range (`^2.0.0`, `>=1.4 <3`, `1.*`, `||`) and can
  speak the caller's contract version.
- **Commands**: what is on PATH, which path wins, what it shadows, relative or empty PATH entries, and
  whether each capability's entrypoint resolves. Nothing is executed.

## Index and cache

`god index` and every query keep a local index (`$GOD_INDEX`, default `~/.cache/god/index.json`). The roots
are rescanned on each query; a project is re-read only when its `.blux/` changed (size, mtime, ctime or
inode of any file in it), and the whole cache is dropped when GOD's or the SDK's version changes.
`--no-cache` skips it, `god index --refresh` rebuilds it. See [docs/INDEX.md](docs/INDEX.md).

## Through BLUX

GOD declares six capabilities in [`.blux/`](.blux): five read-only discovery capabilities and
`registry.index`, which writes only GOD's cache. See [docs/BLUX.md](docs/BLUX.md) for the protocol and the
Stage 05 operation chain *GOD discovers LRC → LRC creates a fixture → DAT audits it → BLUX System records it*.

## Install

```bash
# blux-sdk is not on PyPI yet; install the tagged Contract v1 SDK first.
pip install "blux-sdk @ git+https://github.com/Outer-Void/blux.git@blux-sdk-v0.1.0#subdirectory=sdk/python"
pip install god-cli          # or, from a checkout: pip install -e '.[dev]'  /  ./god --help
```

Python 3.11+. GOD 2.0 replaces GOD 1.x's help indexer; see [docs/AUDIT-1.0.md](docs/AUDIT-1.0.md) for why.

## Development

```bash
make ci   # ruff, mypy --strict, pytest, clean-venv wheel check, GOD checks its own .blux/
```

## Licence

MIT, see [LICENSE](LICENSE).
