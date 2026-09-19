# Pattern Reps — DSA Practice Tracker

A single-file, zero-dependency web app for daily DSA practice, organized by
problem pattern (Two Pointers, Prefix Sum, BFS/DFS, ...). Hosted on GitHub
Pages. Personal project — data is stored in the browser's localStorage.

## How it works

- **Today**: up to 2 problems/day. The first one counts toward the streak;
  the second is a bonus. Skipped problems return to the pool.
- **Scheduler per pattern** (from the date the pattern is added):
  - Days 0–3 (`learning`): served every day, easiest problems first.
  - Days 4–13 (`interleave`): served ~every other day, ~35% revision of
    problems solved 4+ days ago.
  - Day 14+ (`maintain`): served ~1 day in 3, easy+medium mix, ~50% revision.
- **Calendar**: ✓ = 1 solved that day, ✓✓ = both. Tap a day for details.
- Deterministic scheduling: assignments are generated from a seeded RNG keyed
  on the date, then persisted, so reloading never reshuffles the day.

## Repo layout

Everything is in `index.html` — markup, CSS, and JS in one file, no build
step. Key sections (search for the banner comments):

| Section | What it holds |
| --- | --- |
| `Seeded problem pool` | `POOL`: 18 patterns × `P(slug, title, diff)` entries. `diff` is `"E"`, `"M"`, or `"H"`. Slug must match the LeetCode URL (`leetcode.com/problems/<slug>/`). |
| `SEED_PROGRESS` | Problems solved before the tracker existed; seeded into localStorage on first run. `[slug, patternKey]` pairs. |
| `Storage` | `Store` abstraction: uses the Claude artifact db when present, otherwise localStorage. On GitHub Pages it is always localStorage. |
| `Scheduler` | `phaseOf`, `isDue`, `generateAssignment`. |
| `Rendering` | Tabs: Today / Patterns / Calendar. |

## Maintenance tasks (for Claude Code)

- **Add problems to a pattern**: append `P("slug","Title","E|M|H")` entries to
  the right `POOL` category. Never duplicate a slug across categories.
  Skip LeetCode premium-only problems.
- **Add a new pattern**: add a `{key, name, problems:[...]}` object to `POOL`.
  Keys are kebab-case and permanent (they're referenced by stored data).
- **Credit solved problems**: add `["slug","pattern-key"]` pairs to
  `SEED_PROGRESS`. This only affects fresh browsers; existing browsers keep
  their own state (the seed runs once, guarded by the
  `patternreps/seeded` localStorage flag).
- **Tune the cadence**: constants live in `phaseOf` (phase boundaries: 3 / 13
  days), `isDue` (0.55 / 0.35 due probabilities), and `generateAssignment`
  (revision probabilities 0.35 / 0.5; revision eligibility: solved ≥ 4 days
  ago).
- After edits, sanity-check: extract the `<script>` body and run
  `node --check` on it.

## Deploy

GitHub Pages, deploy-from-branch: Settings → Pages → Source: `main`, folder
`/ (root)`. The site is just `index.html` at the repo root.

## Durable storage (recommended for daily use)

Instead of opening the static site, run the bundled local server from the
repo folder:

```
python3 server.py
```

It serves the app at http://127.0.0.1:8123/ (opens your browser
automatically) and persists every write to `data/store.json` — plain JSON,
outside the browser, immune to "clear browsing data". Standard library only,
binds to localhost only. On its first run it migrates any existing
browser-localStorage progress into the file automatically.

Committing `data/store.json` to git doubles as an off-machine backup:

```
git add data/store.json && git commit -m "progress" && git push
```

The page picks its storage automatically: Claude artifact db → local server
file → browser localStorage (GitHub Pages).

Additional commands to keep note of with respect to the systemd service:
journalctl --user -u pattern-reps -e        # logs, if something misbehaves
systemctl --user restart pattern-reps       # after Claude Code edits server.py
systemctl --user disable --now pattern-reps # remove from startup entirely

## Data & backup

Progress lives in localStorage under `patternreps/*` keys, one JSON value per
document (`categories/<key>`, `progress/<slug>`, `completions/<date>`,
`customProblems/<slug>`). The Patterns tab has **Export backup** (downloads
JSON) and **Import backup** (restores it) for moving between devices.

## Future Things to consider
For a personal tool, the project-site URL is usually the wiser spend — it's one path segment longer but keeps your root URL free. A middle option since you own nikunjlad.dev: add a custom domain like dsa.nikunjlad.dev to the Pages repo (one CNAME record at your DNS, one line in Pages settings) — short URL, root stays free, and it's a subdomain so it doesn't touch your main site.
