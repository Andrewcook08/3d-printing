# Geometry model

How a part's shape is expressed, and the properties that fall out of it.

## What it does

A part is described as a **two-dimensional cross-section, extruded sideways**,
with fastener holes cut afterwards. The whole shape is therefore decided in a
flat profile before it ever becomes a solid.

## Why that shape

The extrusion direction is the print orientation, and it buys three things at
once:

- **No overhangs.** Every face is either vertical or horizontal in the print,
  so no supports are needed and nothing has to be cleaned out of an interior.
- **Layer lines across the load.** The layers run across the direction a load
  would try to split the part, not along it.
- **Exported ready to print.** Files come out already lying in that
  orientation. Rotating them in a slicer undoes both benefits.

## Guarantees

**Measurements are entered once.** A part is parameterised on what it holds —
its measured size — and every other dimension derives from that. Two parts
built for very different sizes still position what they hold identically,
because they share the same anchor points rather than each being tuned.

**Forced angles are computed, not chosen.** Where geometry fully determines an
angle — a face that must be tangent to a curve while staying parallel to
another — it is solved for. No such value is typed in as a number, so it stays
correct when a measurement changes.

**Interchangeable support structures.** How a part is carried out from its
mounting surface varies with the situation, and the alternatives are
substitutable. Which one a part uses is part of its declaration, not a branch
in the shape logic.

**The held object's space is subtracted last.** The clearance it needs, and the
channel it travels through to come out, are removed after everything else is
assembled. So they are correct no matter what was added above them, rather than
depending on every added piece having been careful.

## Contract

| | |
|---|---|
| Input | The measured size of what the part holds, plus its style |
| Output | A solid, ready to export |
| Invariant | Same input, same solid, every time |

## How it fails

A shape that cannot be built usually shows up as an **unsound solid** — not
watertight, or in more than one piece — which the build reports and refuses to
pass. Shapes that build cleanly but are physically wrong are caught separately,
by [pre-print verification](../quality/verification.md).
