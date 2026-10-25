# Local registry index

`$GOD_INDEX` (default `$XDG_CACHE_HOME/god/index.json`, else `~/.cache/god/index.json`) holds one entry per
project directory GOD has seen:

```json
{"contract": "god.index", "version": 1,
 "generator": {"god": "2.0.0", "sdk": {"name": "blux-sdk", "version": "0.1.0", "contract_versions": ["1.0"]}},
 "entries": {"/abs/project": {"sig": {".": [...], "manifest.yaml": [size, mtime_ns, ctime_ns, inode], ...},
                              "record": {"kind": "project", ...} | {"kind": "problem", ...}}}}
```

Only `.blux/` files are read. Nothing else in a project is opened.

## Invalidation

On every query (unless `--no-cache`):

1. The roots are rescanned for `.blux/manifest.yaml` (directory listings only).
2. A cached entry is reused only if the signature of its `.blux/` is identical: the directory's mtime, ctime
   and inode, and every file's size, mtime, ctime and inode. Editing, adding, removing or renaming any file
   in `.blux/` changes it, and so does replacing the directory.
3. Changed and new projects are re-read through the SDK. Cached entries under the roots that were not found
   are dropped. Entries for other roots are kept untouched.
4. The whole cache is discarded (`reason: generator-changed`) when GOD's version, the SDK's version or the
   SDK's supported contract versions differ from the ones that wrote it, and (`unreadable`, `wrong-format`)
   when it cannot be parsed.

`--refresh` re-reads every project regardless. Statistics are reported in `index.cache`:
`hits`, `reloaded`, `removed`, `rebuilt`, `reason`.

A cached answer equals a fresh one: tests compare them.

Writes are atomic (temporary file and rename). Through BLUX, only `registry.index` uses the cache. The
read-only capabilities always scan fresh, so their declared `read` side effect is exact.
