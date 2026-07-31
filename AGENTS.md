# Transparent Gif Loop — Agent Guide

Agent-neutral. Claude and Codex both read this file; `CLAUDE.md` points here.

A **utility, not an asset folder** — an earlier vault note was unsure and it caused confusion.
Python 3 + Pillow, single script. Repo: `github.com/BrinShadewater/Transparent-Gif-Loop-Skill`
(private).

It solves one specific problem: a spinning 3D render or sticker exported onto black that snaps
visibly at the loop point and plays too fast.

`scripts/process_gif.py` has two modes, `animated` and `still`. It removes near-black pixels by
alpha threshold, resizes, retimes, interpolates midpoint frames, and adds an eased
last-to-first bridge at the seam.

## Boundary with webp-me-daddy

`webp-me-daddy` owns the **site image pipeline** and calls this script under the hood for its
`animate` command.

**For website assets, start there.** Use this repo directly only for one-off standalone GIF
cleanup — stickers, reaction GIFs, 3D renders. Reaching for this tool on a site hero or blog
cover means bypassing the recipe system that keeps a site's images consistent.

## The limitation to state rather than tune around

**The bridge can hide a bad seam; it cannot build a real loop from frames that never return to
the same pose.** If tuning `--bridge-frames` is not working, that is a source-asset problem. Say
so and ask for a better export rather than overfitting the parameters — no setting rescues
footage that does not loop.

## This repo is the source for an installed skill

The `transparent-gif-loop` skill derives from this project and is **served to Claude from a
plugin**, existing on disk only under `~\.codex\skills`. Do not copy it into `~\.claude\skills`;
that shadows the live version. Check sync with:

```
python path/to/your/skill-tools/sync_skills.py
```

## Rails

Standard: task branch, no direct commits to `main`, no push without approval, no secrets.
Generic rails come from `Projects\AGENTS.md`.

