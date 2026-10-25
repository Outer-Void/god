# GOD through BLUX

GOD's manifest says `role: integrated` (ADR-0002): it reads `.blux/` through `blux-sdk` on its main path. It
needs no BLUX runtime and imports none. BLUX runs GOD's capabilities as subprocesses (ADR-0009,
`god blux-capability ID`).

| capability | side effects | permissions | output |
|---|---|---|---|
| `capability.discover` | read | `fs:read:roots` | `god.capabilities` |
| `capability.describe` | read | `fs:read:roots` | `god.capability` |
| `capability.compat` | read | `fs:read:roots` | `god.compatibility` |
| `project.describe` | read | `fs:read:roots` | `god.project` |
| `command.discover` | read | `fs:read:path`, `fs:read:roots` | `god.commands` |
| `registry.index` | write (GOD's cache only) | `fs:read:roots`, `fs:write:god-cache` | `god.index-summary` |

Input keys mirror the CLI (`roots`, `query`, `project`, `max_side_effects`, `provider_kind`, `labels`,
`capability_id`, `version_range`, `contract_version`, `pattern`, `path`, `declared`, `refresh`, `index`).
Unknown keys are rejected.

- Exit 0, output document. Malformed manifests, duplicates and an empty answer are results: the
  `problems` and `duplicates` fields hold them.
- Exit 1, `{"error": ...}`. GOD could not answer (`NOT_FOUND`, `AMBIGUOUS`, `ROOT_NOT_FOUND`,
  `INVALID_INPUT` …). BLUX records `EXECUTION_FAILED` with GOD's code in `provider_code`.

Outputs carry `linkage` (BLUX operation, parent, session, project and capability ids), so each receipt and the
document it hashes point at each other. GOD writes no receipts itself. Recording is BLUX System's job,
through the runtime.

## What GOD will not do

- run a capability or a discovered program (tests/test_boundaries.py fails if GOD imports `subprocess`);
- decide authorization: `project.describe` reports the declared policy as written and evaluates nothing;
- route, launch or wrap other tools (that is `blux run`, and `ax` for the AXIOM cockpit);
- import the BLUX runtime or CLI.

## Stage 05 hard gate: discover → create → audit

```bash
blux-system init --store truth
blux run capability.discover --project path/to/god --actor-type service --session-id "$S" \
  --input '{"roots": ["path/to/lrc", "path/to/dat"], "query": "repo.create"}' --system-store truth > d.json
ROOT=$(jq -r '.output.capabilities[0].project_root' d.json)        # GOD tells BLUX where LRC is
blux run repo.create --project "$ROOT" --parent-operation-id "$(jq -r .operation_id d.json)" ... > c.json
blux run repo.audit --project path/to/dat --parent-operation-id "$(jq -r .operation_id c.json)" \
  --input "$(jq -c .output.handoff.input c.json)" ...
blux-system graph --store truth --session "$S"     # capability.discover -> repo.create -> repo.audit
```

BLUX's `tests/integration/test_god.py` runs this chain and checks that BLUX System reconstructs it: one root,
three linked nodes, all `SUCCESS`, a complete timeline and a verified log.
