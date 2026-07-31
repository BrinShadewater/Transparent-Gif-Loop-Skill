# Claude Context: Transparent Gif Loop

`AGENTS.md` in this folder is the full guide and is agent-neutral. Read it first.

A single-script utility for standalone GIF cleanup — **not** the site image pipeline.
`webp-me-daddy` owns that and calls this script under the hood via its `animate` command. For
site heroes, covers, logos or avatars, start there.

The limitation worth stating rather than tuning around: the seam bridge can hide a bad loop, it
cannot build one from frames that never return to the same pose. If `--bridge-frames` is not
working, ask for a better export.

