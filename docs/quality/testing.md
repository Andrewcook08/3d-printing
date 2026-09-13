# Testing strategy

What the tests guarantee, and how to read a failure.

## What it does

Six layers, ordered by how precisely a failure points at its cause. When
something changes, the narrowest layer that noticed tells you what moved.

| Layer | Asserts | Catches |
|---|---|---|
| **Contract** | What every project must guarantee, for every project | A project that ships unverified, unlocked, or unsound parts |
| **Architecture** | The boundary between the shared kit and the projects | Shared code that has taken on a project's assumptions, or a helper copied into a second project |
| **Properties** | Relationships that must hold for *any* input | A design that is geometrically wrong, including for sizes never built before |
| **Characterization** | The exact vertices of each shipped cross-section | A change to a part's outline, naming which part moved |
| **Golden master** | The exact bytes of each shipped file | Any change at all to a printable artifact |
| **Command** | The installed commands behave like the library | Broken entry-point wiring that library tests cannot see |

## Guarantees

**The contract layer applies itself.** It runs over whatever projects exist, so
a new project is covered by existing rather than by copying tests, and a
failure names the project it belongs to. See
[project contract](../build/project-contract.md).

**Shared code stays shared.** The kit may not depend on any project — it is
reusable only while it carries no project's assumptions. And no helper may be
defined by two projects at once: that is the signal that a helper has outgrown
the project it started in, so the suite fails and names both, and it gets moved
rather than copied. Names every project is expected to define are exempt, being
roles rather than duplication.

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
| Architecture test fails, naming two projects | Both define the same helper. Promote it to the shared kit, or rename one if they were never the same thing. |
| Architecture test fails, naming shared code | Shared code has taken a dependency on one project, and is no longer shared. |
| Contract test fails, named for one project | That project's declaration or output is wrong; others are unaffected. |
| A deprecation warning fails the run | A dependency is signalling a future removal. |

## Where they run

Before each commit (via hooks), on every pull request, and in the scheduled
upgrade check described in [dependencies](../automation/dependencies.md).
