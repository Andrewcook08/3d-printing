# Build pipeline

How a part that exists only as parameters becomes a file you can print.

## What it does

Each project declares a set of parts. A part is a name and a solid. Building
writes every declared part to that project's output directory as binary STL.

```sh
build                     # every project
build <project>           # one project
```

## Guarantees

- **Deterministic.** The same source produces byte-identical files on every
  run. Nothing about the output depends on when or where it ran.
- **Complete or loud.** Every declared part is written, or the command reports
  a problem and exits non-zero.
- **Self-describing files.** A part's name is both its filename and a label
  recorded inside the file, so a file separated from this repo still says what
  it is.

## Contract

| | |
|---|---|
| Input | The declared parts of one or more projects |
| Output | One STL per part, under the project's output directory |
| Also written | A report line per part, on standard output |
| Exit code | `0` if every part is sound, `1` if one is not, `2` if the arguments were wrong |

Naming a project that does not exist is rejected, with the valid names listed.

Because the part's name is written into the file's contents, **renaming a part
changes its bytes** — and therefore its hash. That is not a quirk to work
around; it is why a file can be trusted to identify itself.

## What building reports

For each part: its overall dimensions, its volume, how many triangles it took,
and whether the solid is sound. A project may add a line of its own above each
part — a derived dimension worth seeing at build time, such as how far the part
will stand off the wall.

"Sound" means the solid is watertight, free of errors, and a single connected
body. An unsound solid is reported and the command fails, because a slicer
cannot be trusted to do something sensible with one.

## How it fails

| Symptom | Meaning |
|---|---|
| Exit `1`, a part marked as needing checking | The solid is not watertight or is in more than one piece. Do not print it. |
| Exit `2`, valid names listed | An unknown project was requested. |
| Files appear somewhere unexpected | The output location was redirected; see [output and locking](output.md). |
