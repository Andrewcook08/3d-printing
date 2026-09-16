# Geometry model

How a part's shape is expressed, and the properties that fall out of it.

## What it does

A part is described as a **two-dimensional cross-section**, and the solid is
that profile swept — along a line for a straight part, around an axis for a
curved one. Where the profile has to *change* along the way, the solid is
stacked from thin slabs of it rather than swept in one operation: an outline
whose features merge into each other as it changes offers nothing to
interpolate between. The whole shape is still decided in flat profiles before
it ever becomes a solid, and holes are cut afterwards where a part needs them.

One consequence is worth stating on its own: two parts swept from the *same*
profile cannot disagree about anything the profile describes. Where a project
needs a straight part and a curved one to match, that is how it is guaranteed
rather than checked.

## Why a profile

Deciding the shape in two dimensions is what makes the rest tractable:

- **The print orientation is chosen with the shape, not after it.** Files are
  exported already lying the way they print. Rotating them in a slicer discards
  that choice.
- **Layer lines can be aimed.** The sweep direction decides whether layers run
  across the direction a load would split the part, or along it.
- **Overhangs are a property of the profile**, so they are known before
  anything is built. Whether a project has none, or has some it has decided to
  live with, is a fact about its profile that it can state — and measure.

## Guarantees

**Measurements are entered once.** A part is parameterised on what it holds and
on the numbers in its [config file](configuration.md); every other dimension
derives from those. Parts built for very different sizes still agree about
whatever they share, because they share anchors rather than each being tuned.

**Forced values are computed, not chosen.** Where geometry fully determines a
value — an angle that must be tangent to a curve while staying parallel to
another, a height that must rest one feature on another — it is solved for.
None is typed in as a number, so it stays correct when a measurement changes.

**Interchangeable structure.** How a part is carried, braced or swept varies
with the situation, and the alternatives are substitutable. Which one a part
uses comes from its configuration, not from a branch in the shape logic.

**Assembly order is deliberate.** Union is not associative in the resulting
mesh, so the order pieces are combined is fixed on purpose: re-ordering them
re-tessellates every part built from that profile, changing bytes without
changing the shape. Where a space has to be kept clear — the room an object
needs, the channel it travels through to come out — it is subtracted after
everything else is assembled, so it is correct however much was added above it.

## Contract

| | |
|---|---|
| Input | The values in the project's config file, and which part to build |
| Output | A solid, ready to export |
| Invariant | Same input, same solid, every time — byte for byte |

## How it fails

A shape that cannot be built usually shows up as an **unsound solid** — not
watertight, or in more than one piece — which the build reports and refuses to
pass. Shapes that build cleanly but are physically wrong are caught separately,
by [pre-print verification](../quality/verification.md).
