---
name: git-conventions
description: Use when running git commands that touch a subset of changes — git stash push with a pathspec while the index has staged-added (new) files, or generating/applying patches that include binary files. Also covers stacked pull requests with `gh stack`. Prevents stashes that silently capture every staged-add and binary patches that fail to apply.
user-invocable: false
---

## `git stash push -- <pathspec>` Captures All Staged-Adds
`git stash push -m "msg" -- <paths>` filters tracked-*modified* files (` M`) by the pathspec correctly, but **unconditionally captures every staged-added file** (`A `, `AM`) in the index regardless of the pathspec. A stash you intended to hold 12 files becomes those 12 plus every staged-add in the working tree, and popping it re-applies those staged-adds — a clean no-op if their content is unchanged, but an add/add conflict if it has since diverged.

When the index contains staged-adds and you need to stash only a subset, don't trust `git stash push -- <paths>`. Use one of:

- **Sidestep (simplest):** commit everything to a temp commit, then `git reset --mixed HEAD~1` so the staged-adds become *untracked* files — which `git stash push -- <paths>` leaves alone unless you pass `-u` — then stash the tracked-modified subset cleanly.
- **Plumbing rebuild** when you can't disturb the index:
  1. `cp .git/index .git/index.bak`
  2. `git read-tree HEAD` (reset index to HEAD)
  3. `git add -- <paths>` (stage just the subset)
  4. `TREE=$(git write-tree); PARENT=$(git rev-parse HEAD)`
  5. `INDEX=$(echo "index on $branch: msg" | git commit-tree $TREE -p $PARENT)`
  6. `WIP=$(echo "On $branch: msg" | git commit-tree $TREE -p $PARENT -p $INDEX)`
  7. `git update-ref -m "On $branch: msg" --create-reflog refs/stash $WIP` — the `-m` is required; a positional message is parsed as `old_value` and errors with "not a valid old SHA1".
  8. `mv .git/index.bak .git/index`
  9. `git checkout HEAD -- <paths>` to revert the subset in the working tree.

## Binary Patches Need `--binary`
When generating a patch that includes binary files (images, fonts, compiled assets), use `git diff --binary`. A plain `git diff` patch fails to apply with `cannot apply binary patch to '<file>' without full index line`.

## Stacked Pull Requests with `gh stack`
`gh stack` (the `github/gh-stack` extension) manages a chain of branches with one PR each: `gh stack init`, `add`, `submit`, `sync`, and `merge --squash`.

- **A draft PR blocks the merge.** `gh stack merge` checks only that each PR is open and not a draft. Run `gh pr ready <n>` for every PR in the stack first.
- **The merge is atomic.** If any PR cannot be merged, none is merged.
- `gh stack submit --auto` creates new PRs as drafts unless you pass `--open`.
- Without the extension, rebase each child branch onto its new parent with `git rebase --onto <new-parent> <old-parent-sha>`. Stop at the first failed rebase. Do not let a script continue to the next branch.
