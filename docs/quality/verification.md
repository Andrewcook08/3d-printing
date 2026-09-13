# Pre-print verification

Physical checks on the generated solids. Run before printing.

```sh
verify
```

## What it does

Where the tests ask *"did anything change?"*, verification asks *"is this part
physically sound?"* — by measuring the finished solids and printing what it
measured, so the numbers are visible rather than merely asserted.

Crucially it measures the **solids**, not the parameters they came from. A
mistake anywhere between a dimension and the exported shape still shows up.

## Guarantees

**Every check measures the built solid**, not the numbers it was built from. A
mistake anywhere between a dimension and the exported shape still shows up,
because nothing is read back from the parameters that produced it.

**Every check is measured against what the project asked for.** The numbers a
check compares against come from the project's [config file](../build/configuration.md),
so what is confirmed is that the machine produced the part that was specified.
Whether the specification is *right* for the object it has to hold is a
different question, and one a project can only answer by checking the built
shape against a measurement of that object.

**Every check reports its measurement, not just its verdict.** A near miss is
visible before it becomes a failure.

**Every check can fail.** Each is exercised against something deliberately
wrong, so a check that has quietly stopped measuring anything is itself caught.

**What is checked is a project's own business.** One project asks whether a rod
seats, lifts out and is trapped sideways; another asks whether a channel necks
down to a clip, aims where it should, and turns a full corner. What they share
is the shape of the guarantee above, not a list of questions.

## Contract

| | |
|---|---|
| Input | The built solids, generated fresh |
| Output | One `PASS`/`FAIL` line per check, with the measured value |
| Exit code | `0` if every check passes, `1` otherwise |
| Side effects | None. It reads; it never writes a file. |

The same checks also run inside the test suite, so a part that fails them
cannot reach the default branch unnoticed.

## How it fails

A `FAIL` line names the check and shows the measurement that broke it — the
interference volume, the clearance, the height mismatch. Compare it against the
threshold in the same line to see how far out it is.

**A failure here means do not print.** The file may well be watertight and
perfectly exportable; it is the *part* that is wrong.
