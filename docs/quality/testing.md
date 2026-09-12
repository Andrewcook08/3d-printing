# Testing strategy

What the tests guarantee, and how to read a failure.

## What it does

Four layers, ordered by how precisely a failure points at its cause. When
something changes, the narrowest layer that noticed tells you what moved.

| Layer | Asserts | Catches |
|---|---|---|
| **Properties** | Relationships that must hold for *any* input | A design that is geometrically wrong, including for sizes never built before |
| **Characterization** | The exact vertices of each shipped cross-section | A change to a part's outline, naming which part moved |
| **Golden master** | The exact bytes of each shipped file | Any change at all to a printable artifact |
| **Command** | The installed commands behave like the library | Broken entry-point wiring that library tests cannot see |

## Guarantees

**Properties assert intent, not history.** Where a value is forced by geometry,
the test asserts the *relationship* — that a line is genuinely tangent to a
curve, that two parts place what they hold at the same height — rather than
pinning the number that relationship currently produces. Change a measurement
and these still hold.

**The golden master is an integration test.** It builds parts through the real
generation path and writes real files, so a dependency that breaks generation
fails here. It runs on every change, including automated dependency updates.

**Warnings are failures.** A dependency's deprecation warning fails the suite,
so a removal two releases away surfaces while there is still time to act.

**The commands are exercised as commands.** One test runs the installed
executables as subprocesses and compares their output to the library's. That
plus the golden master means the shipped command produces the locked bytes,
without either test needing to know about the other.

## What the tests cannot tell you

The golden master is a **change detector, not a correctness oracle**. It proves
the output did not change. It cannot prove a changed output is wrong, or that
an unchanged one is right — a design wrong from the start stays green forever.
Only the property layer asserts intent, and only for the relationships it
covers. Nothing here knows whether a part survives its load or fits the real
object.

## How to read a failure

| Pattern | Meaning |
|---|---|
| Properties pass, characterization passes, bytes differ | Meshing changed beneath the geometry. Design untouched. |
| Properties pass, characterization fails | A part's outline moved. Usually an intended design change. |
| Properties fail | The design itself is wrong. Investigate before anything else. |
| Command test alone fails | The library is fine; the installed entry point is broken. |
| A deprecation warning fails the run | A dependency is signalling a future removal. |

## Where they run

Before each commit (via hooks), on every pull request, and in the scheduled
upgrade check described in [dependencies](../automation/dependencies.md).
