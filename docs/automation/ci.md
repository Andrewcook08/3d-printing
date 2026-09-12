# CI pipeline

The gates a change passes, and why they are shaped this way.

## What it does

The default branch accepts no direct pushes — from anyone, including the repo
owner. Every change travels the same route:

```
branch  →  pull request  →  checks pass  →  merge  →  branch deleted
```

No reviewer approval is required. You merge your own work once it is green.

## The gates

One definition of "is this repo healthy?" is shared by every automated run, so
a scheduled check can never drift into testing something different from a pull
request. It installs the project and runs four things, each named for the
concern it covers:

| Gate | Fails when |
|---|---|
| Lint | Code violates the agreed rules |
| Format | Code is not in the agreed style |
| Types | A type error is detectable statically |
| Tests | Behavior changed — see [testing](../quality/testing.md) |

They run independently: a failure in one does not stop the rest, so a single
run reports every category that is broken rather than only the first.

They arrive as one check, not four. **The failing gate's name is the
diagnosis**, and you read it in the run's log, where each gate is its own
labelled group.

## Guarantees

**Checks run against the merge result.** A pull request is tested as its branch
merged into the default branch, not as the branch alone. If the default branch
moves while the request is open, the branch must be brought up to date and
re-checked.

Together with the no-direct-push rule, that means **every commit on the default
branch was verified as the merge that created it**. This is also why nothing
runs on push: it would re-verify an identical tree.

**A subset runs before each commit**, locally, via hooks — the fast checks plus
the test suite, so a broken change usually never becomes a commit. Static type
checking runs only in CI.

## Contract

| | |
|---|---|
| Trigger | Opening or updating a pull request against the default branch |
| Required to merge | Every gate green, and the branch up to date |
| Not required | Reviewer approval |
| On merge | The branch is deleted automatically |

## How it fails

| Symptom | Meaning |
|---|---|
| Merge blocked, no check reported | The branch is behind, or the checks have not run yet |
| Merge blocked, a gate red | Read the gate's name; it names the category |
| A push to the default branch is rejected | Working as intended — open a pull request |
| A hook rewrote files and the commit aborted | Formatting was applied; stage the changes and commit again |
