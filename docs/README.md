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

The properties that hold the whole thing together:

- **Generation is deterministic.** The same source always produces the same
  bytes, which is what makes the parts hash-lockable.
- **Parameters are data, not code.** What a project measures or chooses lives
  in its config file; the code derives everything else from it and changes only
  when the shape does.
- **Dimensions are derived, never restated.** A measurement is entered once;
  everything geometric follows from it.
- **Nothing reaches the default branch unchecked.**
- **Projects are found, not listed.** Adding one touches only its own files,
  and enrols it in every check automatically.

## The components

### Making parts

| Doc | Covers |
|---|---|
| [Project contract](build/project-contract.md) | What a project must declare, and what it inherits for free |
| [Configuration](build/configuration.md) | Where a project's numbers live, and what reading them guarantees |
| [Build pipeline](build/pipeline.md) | A declared part becoming an STL file, and what building reports |
| [Geometry model](build/geometry.md) | How a part's shape is expressed, and why it prints without supports |
| [Output](build/output.md) | Where files land, what is committed, and what is not |

### Checking them

| Doc | Covers |
|---|---|
| [Testing strategy](quality/testing.md) | The test layers, and what a given failure pattern means |
| [Pre-print verification](quality/verification.md) | What the physical checks guarantee about a part |
| [Locking](quality/locking.md) | The two records of what a project last shipped, and what each catches |

### Automation

| Doc | Covers |
|---|---|
| [CI pipeline](automation/ci.md) | The gates on a change, and why they are shaped this way |
| [Dependencies](automation/dependencies.md) | Constraints versus pins, and the upgrade lifecycle |

## Where to start

Reading in order — [build pipeline](build/pipeline.md),
[output](build/output.md), [locking](quality/locking.md) — explains
how a part is produced and why you can trust the file in `output/`. The rest can
wait until you need it.

For **using** the tool, see the [root README](../README.md). For **printing and
hanging** a specific part, see that project's own README next to its source.

## About these docs

They describe behavior, not implementation, so they stay correct across
refactors. They change only when the system's behavior changes. Before editing
any of them, use the `maintaining-docs` skill.
