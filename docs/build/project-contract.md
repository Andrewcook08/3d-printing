# Project contract

What a 3D-printing project must provide, and what it gets in return.

## What it does

A project declares itself inside its own package. Nothing central lists the
projects — they are found by looking, so adding one touches only that project's
own files and never a file shared with every other project.

## What a project must declare

| Declares | Meaning |
|---|---|
| A name | Kebab-case. Names its output directory and its command-line argument. |
| A summary | One line, shown in the command-line help. |
| Its parts | What it ships: each a name and a solid. |
| How to build | Writes those parts to its output directory. |
| How to verify | Its physical checks. **Required** — see below. |
| A lock | The file recording the hash of everything it has shipped. |
| A measurement lock | The file recording what its checks read off those parts. **Required** — it is the only thing that notices shared code measuring differently while the bytes stay identical. |
| A config | The file its measured and chosen numbers come from. **Required** — see [configuration](configuration.md). |

Identity is available without loading any geometry, so listing the projects
stays cheap however many there are. The heavier parts load only when something
asks for them.

## Guarantees

**Declaring a project enrols it in everything.** It is built by the build
command, checked by the verify command, and covered by the shared conformance
tests, without writing any test code.

Those tests assert, for every project: that it declares all of the above; that
its part names are unique; that every locked file is still produced; that
rebuilt bytes match the lock; that the committed output matches the lock; that
its checks still report the numbers they last reported; that every part is a
single watertight body; that building writes exactly the declared parts under
the project's own name; and that its verification passes.

**Verification is not optional.** A project that cannot check its own parts
fails the contract. A part that reaches the output directory has been measured.

**The shared kit never depends on a project.** Shared code stays reusable only
while it carries no project's assumptions, so the direction of that dependency
is checked rather than trusted.

## What a project writes for itself

Only what is genuinely its own: the shape of its parts, the physical checks
that shape must pass, and tests for anything specific to it. Everything else is
inherited.

## How shared code grows

A helper starts inside the project that needs it and reaches the shared kit by
one of two routes: when a second project needs the same thing, or when nothing
about its shape was ever ours to choose. Only utilities with no subject-matter
knowledge are eligible either way. The rule for telling those apart, and the
reasoning behind it, lives in `CLAUDE.md` and is not restated here — a
paraphrase is what let an earlier version of it go stale in this file while the
other copies were corrected.

The move never changes what a helper computes, and two locks prove it rather
than the author's word: one on the bytes each project ships, one on what its
checks measure. A helper may shed dependencies on the way — asking for the two
values it needs rather than the object holding them — since that changes nothing
it produces. What it may not do is grow a way to ask for something different,
because every project sharing it then has more to know.

**Changing a helper already shared is governed separately**, since by then every
project is downstream of it. What a caller may ask for, what may be corrected,
and what must be brought to the repo's owner before it is touched are set out in
`CLAUDE.md` alongside the rest of that rule.

## How it fails

| Symptom | Meaning |
|---|---|
| Contract tests fail for one project, named in the result | That project's declaration or output is wrong; the others are unaffected |
| A project is not built and not listed | It declares nothing discoverable |
| Failures mention the shared kit depending on a project | Shared code has acquired a project's assumptions and is no longer reusable |
