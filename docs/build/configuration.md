# Configuration

Where a project's numbers live, and what reading them guarantees.

## What it does

Every project keeps its measured and chosen values in `parts.toml` beside its
code. The build reads that file and produces exactly what it describes. Tuning
a part — a diameter, a radius, an angle, how many of a thing to make — is an
edit to that file, and nothing else changes.

A project may read more than one file. The one convention worth copying is a
`trials.toml` holding parts being tested rather than shipped: deleting it
retires all of them at once, and what they produce is kept out of the committed
[output](output.md) and out of both locks. That is a project's choice, not
something the contract provides. What the contract requires is `parts.toml`.

The distinction the two files draw is what a project is **committing to**. An
entry in `parts.toml` is a part the project ships and stands behind; an entry in
`trials.toml` is a question it has not answered yet.

## The shape of a file

One table holds the numbers the shape itself is built from; repeated entries
name the parts being asked for.

```toml
[design]          # what the shape is made of — measured or chosen
[[straight]]      # one entry per part, named and dimensioned
```

What the entries are called is the project's own business — one asks for
straights and corners, another for rods and the styles each is held in. What
they share is the shape: design numbers in one table, repeated entries for what
is being asked for. A part entry may override a value from `[design]` for itself
alone, which is how one bracket leans differently from the rest.

## The boundary

**A number you measured or chose belongs in the file. A number you computed
belongs in the code.**

Anything derivable from what the file already says is derived, every time,
rather than written down a second place where the two can disagree. This is the
repo's existing rule that dimensions are derived and never restated, made
enforceable: a key nobody asked for is refused, so a derived value written down
by hand fails the moment the file is read.

## Guarantees

**What the file says is what gets built.** Every part in the output is
described by the file, and nothing in the file is silently skipped. A project
may turn its entries into parts however it likes — one each, or a rod against
every style it is held in — but nothing appears that the file did not ask for.

**Anything unrecognised is refused.** A misspelled key fails with the file, the
key, and the keys it could have been. It never becomes a value quietly left at
its default.

**A value is what it says it is.** A number is read as a number, text as text,
and a whole number is accepted where a decimal is wanted. Nothing is guessed
from how a value looks.

**A value the project cannot build stops the build before it writes anything.**
Everything is constructed first, so a corner tighter than the part reaching into
it fails naming the limit it broke, with the output directory untouched rather
than half rewritten. The reader checks a value's shape; only the project knows
its limits.

**Retiring a part is deleting its entry.** The next build moves the orphaned
file aside; see [output and locking](output.md).

## The contract

| | |
|---|---|
| Reads | `parts.toml` beside the project's code, and any further files the project chooses |
| Declares | One config file, the one the contract checks. A project reading more keeps the others its own business — no project has yet needed two the contract must know about. |
| Produces | Parts described by the file, built from the values in it |
| Fails on | An unknown key, a missing required value, a value of the wrong type, a field asking for something config cannot express, or a file that is not valid TOML |
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
| `asks for <type>, which is not a config shape` | The schema wants something config cannot express, not a bad value |
| A project's own limit, naming a bound | The value parsed, but the project cannot build it — raised before anything is written |

A change to the file that changes a part's shape will also fail the hash lock,
which is the intended second line: config says what to build, the lock says what
was last agreed to. See [output and locking](output.md).
