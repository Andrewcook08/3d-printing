# Configuration

Where a project's numbers live, and what reading them guarantees.

## What it does

Every project keeps its measured and chosen values in `parts.toml` beside its
code. The build reads that file and produces exactly what it describes. Tuning
a part — a diameter, a radius, an angle, how many of a thing to make — is an
edit to that file, and nothing else changes.

A project may also keep `trials.toml`: parts being tested rather than shipped.
It is optional, and absent means there are none.

## The boundary

**A number you measured or chose belongs in the file. A number you computed
belongs in the code.**

Anything derivable from what the file already says is derived, every time,
rather than written down a second place where the two can disagree. This is the
repo's existing rule that dimensions are derived and never restated, made
enforceable: a key nobody asked for is refused, so a derived value written down
by hand fails the moment the file is read.

## Guarantees

**What the file says is what gets built.** There is no path by which a part
appears in the output without an entry behind it, and none by which an entry is
silently skipped.

**Anything unrecognised is refused.** A misspelled key fails with the file, the
key, and the keys it could have been. It never becomes a value quietly left at
its default.

**A value is what it says it is.** A number is read as a number, text as text,
and a whole number is accepted where a decimal is wanted. Nothing is guessed
from how a value looks.

**Limits are enforced when the file is read**, not when the shape is built. A
value a project cannot make sense of — a corner tighter than the part reaching
into it — fails immediately, naming the limit it broke.

**Retiring a part is deleting its entry.** The next build moves the orphaned
file aside; see [output and locking](output.md).

## The contract

| | |
|---|---|
| Reads | `parts.toml` beside the project's code; `trials.toml` if it exists |
| Produces | One part per entry, built from the values in the file |
| Fails on | An unknown key, a missing required value, a value of the wrong type, a value outside what the project allows, or a file that is not valid TOML |
| Never | Writes to either file, or to the hash lock |

The file is TOML rather than JSON or YAML for two reasons: the reasoning behind
a number belongs beside it, which needs comments; and a build whose output is
hash-locked cannot afford a format that infers a value's type from how it is
written.

## How it fails

| Message | Meaning |
|---|---|
| `has no place for <key>` | A misspelling, or a value that should have been derived |
| `is missing <key>` | A required value with no sensible default was left out |
| `should be <type>` | The value is there but is not the kind of thing it must be |
| `is not valid TOML` | The file is malformed; the parser says where |
| A project's own limit, naming a bound | The value parsed but the project cannot build it |

A change to the file that changes a part's shape will also fail the hash lock,
which is the intended second line: config says what to build, the lock says what
was last agreed to. See [output and locking](output.md).
