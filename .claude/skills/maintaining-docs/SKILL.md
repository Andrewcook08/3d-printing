---
name: maintaining-docs
description: Use when any documentation work is in scope - writing or updating a doc, documenting a new component, restructuring the docs tree, reviewing docs in a pull request, or when docs are stale, bloated, duplicated, or have drifted out of step with the code.
---

# Maintaining Docs

## Overview

**Docs describe behavior. Code describes implementation.** A document that
names a function is welded to that function: rename it and the doc is wrong.
A document that describes what the system guarantees survives any refactor
that keeps the guarantee.

This is the whole framework. Everything below follows from it.

## The Rename Test

Before committing any doc, ask:

> If someone renamed a function, moved a module, or restructured a class
> hierarchy — without changing what the system does — would this document
> need editing?

**Yes → the doc is coupled. Rewrite it.**

Docs change when *behavior* changes. Never as part of a refactor.

## What You May Name

| Name freely | Never name |
|---|---|
| Commands a user runs | Functions, methods, classes |
| File and directory locations that are part of the contract | Module or package names |
| Environment variables, config keys | Internal types, constructor arguments |
| Observable artifacts and their names | Private helpers, call sequences |
| Failure signatures and exit codes | Line numbers, code excerpts |

Anything observable from outside is fair game — it is behavior. Anything you
would only know by opening a source file is implementation.

## The Map

One index, components grouped by concern:

```
docs/README.md          the whole system in brief, plus links to every doc
docs/<concern>/<component>.md
```

Rules:

- **The index carries the high-level picture and jump links only.** No
  component detail — that lives in the component doc, once.
- **Every component doc is reachable from the index.** An unreachable doc is
  an invisible doc.
- **One component, one doc.** If two docs explain the same thing, one is wrong.
  Link instead of repeating.
- Group by concern, not by source-tree shape. Source layout is implementation;
  concerns are behavior.

## What Goes In a Component Doc

Four things, in roughly this order:

1. **What it does** — one or two sentences.
2. **The guarantees** — what a caller may rely on.
3. **The contract** — inputs, outputs, and observable side effects.
4. **How it fails** — what failure looks like and what it means.

Never: code walkthroughs, changelogs (version control owns those), rationale
essays, or anything another doc already says.

## Length

**About one screen.** A table beats a paragraph. A doc that runs long is either
covering two components or explaining implementation. Cut rather than pad — a
short accurate doc gets read; a long one gets skimmed, then distrusted.

## Quick Reference

| Situation | Do |
|---|---|
| New component | Add its doc under the right concern, link it from the index |
| Behavior changed | Update that doc only |
| Refactor, same behavior | Change nothing |
| Doc explains *how* | Rewrite as what and why |
| Two docs overlap | Delete one, link to the other |
| Doc is growing | Split by concern or cut implementation detail |

## Common Mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| Naming functions for precision | Precision that rots is worse than none | Describe the guarantee |
| Organising docs by source tree | Mirrors implementation, breaks on refactor | Group by concern |
| Duplicating detail into the index | Two copies drift; readers trust neither | Index links, docs explain |
| Adding a doc without linking it | Nobody finds it | Link it in the same change |

## Red Flags

- You opened a source file to write a sentence
- The doc contains a function, class, or module name
- You are describing a sequence of calls
- A refactor PR touches documentation

**Each means: stop, and describe the behavior instead.**
