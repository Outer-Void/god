# Usage

Common options: `-r/--root DIR` (repeatable; default `$GOD_ROOTS` or `.`), `--json`, `--index FILE`,
`--no-cache`. Projects are directories containing `.blux/manifest.yaml`, found up to 6 levels below a root.
Symlinked directories, `.git`, `node_modules`, virtualenvs, caches, `build`/`dist` and hidden directories are
not entered.

| command | capability | output contract |
|---|---|---|
| `god capabilities [QUERY] [--project P] [--max-side-effects S] [--kind K] [--label K=V]` | `capability.discover` | `god.capabilities` |
| `god capability ID [--project P]` | `capability.describe` | `god.capability` |
| `god project ID_OR_DIR` | `project.describe` | `god.project` |
| `god compat ID [--range R] [--contract MAJOR.MINOR] [--project P]` | `capability.compat` | `god.compatibility` |
| `god commands [GLOB] [--path PATH] [--declared]` | `command.discover` | `god.commands` |
| `god index [ROOT...] [--refresh]` | `registry.index` | `god.index-summary` |
| `god check [ROOT...]` | | `god.check` |
| `god version` | | |

`QUERY` is a capability id, a glob (`repo.*`) or a substring. `--project` takes a project id or a root.

Every document has `contract`, `version`, `tool`, `sdk` (blux-sdk version and supported contract versions)
and, when roots were scanned, `index` (roots, project and problem counts, cache statistics). Lists are
sorted, and nothing depends on the clock. The same tree gives the same document.

`god project DIR` with a directory that contains `.blux/` describes just that directory (no scan).

## Compatibility

`--range` is a semver range: `1.2.3`, `=1.2.3`, `>=`, `>`, `<=`, `<`, `^1.2.3`, `~1.2.3`, partial versions
(`>=2`, `<2.1`, `^1`), wildcards (`1.*`, `1.2.*`, `*`), space for AND and `||` for OR. Prereleases match only
comparators that name a prerelease of the same version. `--contract` is the caller's BLUX contract version
(default: the installed SDK's). A provider matches if its version satisfies the range and
`blux_sdk.versions.negotiate` finds a common contract version. Verdict `incompatible` exits 1.

## Exit codes

| code | meaning |
|---|---|
| 0 | answered |
| 1 | `check` found problems or duplicates; `compat` found no compatible provider; `capability`/`project` found nothing (`NOT_FOUND`) or more than one (`AMBIGUOUS`) |
| 2 | bad command line, or a GOD 1.x command (`build`, `search`, `info`, `stats`, `blux`, `completion`) |
| 3 | GOD could not answer: missing root, bad input, unreadable index, blux-sdk not installed |

With `--json`, failures print `{"error": {"code", "message", "details"}}`.
