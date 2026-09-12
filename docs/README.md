# How this project works

This repo turns Python into printable parts. Each 3D-printing project describes
its parts parametrically; one command generates them as STL files into a shared
output location, and a layer of checks makes sure a change to the code cannot
silently change the parts.

The shape of it:

```
a project declares named parts
        │
        ├─ build ──▶ output/<project>/*.stl        the printable artifacts
        │
        ├─ verify ─▶ measurements of the solids    is it physically sound?
        │
        └─ tests ──▶ pass / fail                   did anything change?
```

Three properties hold the whole thing together:

- **Generation is deterministic.** The same source always produces the same
  bytes, which is what makes the parts hash-lockable.
- **Dimensions are derived, never restated.** A measurement is entered once;
  everything geometric follows from it.
- **Nothing reaches the default branch unchecked.**

## The components

### Making parts

| Doc | Covers |
|---|---|
| [Build pipeline](build/pipeline.md) | A declared part becoming an STL file, and what building reports |
| [Geometry model](build/geometry.md) | How a part's shape is expressed, and why it prints without supports |
| [Output and locking](build/output.md) | Where files land, determinism, and the hash lock |

### Checking them

| Doc | Covers |
|---|---|
| [Testing strategy](quality/testing.md) | The test layers, and what a given failure pattern means |
| [Pre-print verification](quality/verification.md) | What the physical checks guarantee about a part |

### Automation

| Doc | Covers |
|---|---|
| [CI pipeline](automation/ci.md) | The gates on a change, and why they are shaped this way |
| [Dependencies](automation/dependencies.md) | Constraints versus pins, and the upgrade lifecycle |

## Where to start

Reading in order — [build pipeline](build/pipeline.md),
[output and locking](build/output.md), [testing](quality/testing.md) — explains
how a part is produced and why you can trust the file in `output/`. The rest can
wait until you need it.

For **using** the tool, see the [root README](../README.md). For **printing and
hanging** a specific part, see that project's own README next to its source.

## About these docs

They describe behavior, not implementation, so they stay correct across
refactors. They change only when the system's behavior changes. Before editing
any of them, use the `maintaining-docs` skill.
