# Dependencies

How versions are controlled, and how an upgrade is evaluated before it lands.

## What it does

Two layers, deliberately separate:

| Layer | Holds | Answers |
|---|---|---|
| Constraints | Acceptable version ranges | What is *allowed* |
| Lock | One exact version per package | What is *installed* |

Automated builds install strictly from the lock. That makes them **hermetic**:
a new release of anything has no effect until the lock is deliberately moved.
This is what makes generated parts reproducible — and it means the normal
checks can never notice that a newer version exists.

Both layers are generated. Neither is edited by hand.

## Covering the gap

Because the checks are blind to new releases, two mechanisms watch from outside:

| Mechanism | Produces | Covers |
|---|---|---|
| Update bot | A pull request | Anything needing a decision *and* a commit, including the versions of the automation itself |
| Scheduled upgrade check | A report only | The case the bot misses — a new release that already satisfies an existing range, so no pull request is ever opened |

Neither names any package. Both derive the list from the declared constraints,
so a newly added dependency is covered the moment it is added.

The scheduled check resolves the newest allowed versions, runs every gate, and
**commits nothing**. Bot pull requests go through the ordinary gates, so an
upgrade that changes a part fails the hash lock and cannot merge.

## Guarantees

- An upgrade cannot land without passing every gate.
- An upgrade that changes any generated part is blocked until someone decides.
- A deprecation warning from a dependency fails the run, surfacing a future
  removal while there is still time to act.

## Reading a red upgrade check

**It is a decision, not a build to fix.** The failing gate names the category —
see [testing](../quality/testing.md) for the full table, but in short: parts
changed, code style changed, or a warning arrived.

Then choose, in a pull request:

- **Accept** — move the lock, re-lock anything whose bytes changed, and state
  in the request what changed and why it is acceptable.
- **Hold** — tighten the constraint so the new version is excluded, with a
  comment giving the reason.

Never re-lock a part purely to get to green. See
[locking](../quality/locking.md).

## How it fails

| Symptom | Meaning |
|---|---|
| Upgrade check red on the parts gate | A newer version would change the printed output |
| Upgrade check red on style or types | A newer tool is stricter or restyles code |
| A bot request cannot merge | It is behind the default branch, or a gate is red |
| Nothing happens for a long time | Expected — a hermetic build is quiet by design |
