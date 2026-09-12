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

For each part, that the object it holds:

- **Seats without interference** — it fits where it is supposed to sit.
- **Comes straight out** — nothing above the cradle blocks removal along the
  whole length of a long object that cannot dodge sideways.
- **Is trapped in both directions** — it can neither roll back toward the
  mounting surface nor forward out of the cradle.
- **Clears the mounting surface** — there is air between it and the wall.

For each fastener, that its hole is **open through the part** and
**countersunk on the front face only**, leaving the back a flat unbroken pad;
and that it sits clear of the cradle with enough material above it.

For a matched pair, that both parts **place what they hold at the same
height**, within a tolerance tight enough that a long object spans them without
a visible tilt.

Each project defines its own checks. These are the ones that are easy to break
and hard to spot by eye.

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
