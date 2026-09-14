# Hue gradient lightstrip brackets

Clip brackets that carry a Philips Hue gradient lightstrip around the back of a
TV without any adhesive on the strip itself, and hold it at 45° so it throws
light along the wall rather than straight at it.

Two shapes — a straight run and a 90° corner — generated from one profile, so
they are the same bracket swept two ways and cannot drift apart.

Shape follows `reference/Hue LED Strip with Angle straight section.stl`,
rebuilt parametrically rather than traced. Every dimension below was measured
off that mesh.

> **Note. Nothing here is final yet.** Everything in `parts.toml` is there so
> that it is built, committed and readable — not because the set is decided.
> Which parts there are, their sizes and radii, and their names are all still
> open, and this file is rewritten when that closes. `uv run build` is the
> accurate list of what exists at any moment.
>
> What the printing did establish is narrower and does hold: every rung of the
> leaning radius ladder bound, which is why the corners stand upright. The
> passages that argued for a leaning corner are replaced rather than kept. The
> **channel** is untouched throughout — nothing the printing disproved reached
> the clip, its dimensions, or why the straights lean.

## The problem these solve

The strip was mounted with its own adhesive backing. Over weeks the adhesive
crept away from the panel, the strip sagged in the middle of each run, and the
wall wash went patchy. Adhesive holding a continuous flexible strip fails this
way: the strip's own springiness works on the bond everywhere at once.

A bracket breaks that. The adhesive holds a small rigid pad; the strip is held
by a clip. Nothing pulls on a glue line along its whole length any more.

The second problem is aim. The wall behind this TV is dark, and a strip firing
straight back at a dark wall produces very little wash. The channel leans 45°,
so light goes out *and* back.

## Print these

| File | Size | Volume |
|---|---|---|
| **`output/hue-tv-brackets/straight-125mm-v1.stl`** | 26.2 × 125.0 × 17.0 mm | 18.8 cm³ |
| **`output/hue-tv-brackets/corner-tight-v1.stl`** | 42.1 × 42.1 × 18.0 mm | 4.8 cm³ |
| **`output/hue-tv-brackets/corner-wide-v1.stl`** | 80.2 × 80.2 × 18.0 mm | 10.5 cm³ |

**Provisional — see the note at the top.** There are two corners rather than
one because the radius is a fitting choice rather than a structural one (see
below); they are otherwise identical, so print whichever suits the run you are
covering. The lengths, radii and names of all three are still open.

Anything still under test builds outside the committed output and is not listed
here. `uv run build` prints every file it writes and where.

The brackets are universal — nothing here is sized to a particular TV or strip
length, so how many straights a run takes, and whether you need corners at two
of the TV's corners or all four, follows from the TV and the strip in front of
you.

The two corners differ only in radius, and neither is sharper on the strip than
the other — at 90° there is nothing to be sharp about. Pick by how the strip
has to sit on your TV; see [What picks the radius, then](#what-picks-the-radius-then).

### Slicer settings

They are exported already lying on their base, which is the orientation they
print in. **Do not rotate them.**

- **PETG** preferred. The back of a TV runs warm, and PLA softens at
  temperatures a panel can reach in a sunlit room.
- 0.2 mm layer height
- 3 wall loops
- 15 % infill — nothing here is structural once it is stuck down
- **No supports.** See below.

**One lip prints with a small droop, and that is expected.** The channel leans
45° and a lip is an undercut leaning back over it, so on the upper side the
lean and the undercut add and the face gets steeper, while on the lower side
they cancel and the face comes out near horizontal — 1.5 mm of unsupported
reach. It sags on the first layer and pulls flat over the next few. The rough
surface is inside the channel where nothing sees it, and the droop biases the
mouth slightly narrower, which grips the strip a little harder.

Supporting it is worse than living with it: you would be prying support
material out of a 12 mm slot, and the thing you would be prying against is the
clip.

## Choosing the radius

Going round a corner bends the strip about an axis perpendicular to the TV
back. That axis sits 45° between the strip's easy bend — the way a tape measure
coils — and its in-plane bend, which a flat strip essentially refuses. So the
curvature splits evenly between the two, and the in-plane bend the strip
actually feels corresponds to **R × √2**: a 40 mm bracket asks of it what a
57 mm in-plane bend would.

The 45° lean is therefore worth a factor of √2 over laying the strip flat. It
is real relief and not immunity, and how much in-plane bend a given strip
tolerates cannot be derived — only found. It was found by printing: rungs at
9.3%, 3.0% and below all bound, which is what sent the corners upright, where
the cosine is zero and the question does not arise.

### Why the corners stand upright

Leaning the channel relieves the in-plane bend but never removes it, and the
45° ladder that argued otherwise was printed and bound at every rung. Standing
the channel fully upright removes it outright: at 90° the cosine is zero, so
none of the turn lands in the strip's own plane and the whole of it becomes the
easy roll a flat strip is built for. The corners are 90° for that reason, while
the straights keep the 45° lean that aims the light.

The strip therefore has to twist between a straight and a corner. Leave it room
to — butt the two brackets tight together and the twist has nowhere to go.

### What picks the radius, then

Not strain, which is zero at any radius here. Geometry.

**Rounding a corner shortens the loop.** The arc replaces two legs of `r` with
an arc of `πr/2`, so each corner gives back `(2 − π/2)r ≈ 0.43r`, and four give
back `(8 − 2π)r ≈ 1.72r`. A *bigger* radius gives back *more*. Reading the arc
length on its own suggests the opposite and is the easiest mistake to make
here: the arc grows with `r`, but the sharp path it replaces grows faster.

For a strip of length `L` running inset `x` from each edge of a mounting
surface `W` by `H`, with four corners of radius `r`:

```
path = 2(W − 2x) + 2(H − 2x) − (8 − 2π)r
```

Setting `path = L` and writing `P = 2(W + H)` for the perimeter:

```
x = (P − L − (8 − 2π)r) / 8
```

So a larger radius buys a **shallower** inset, not a deeper one — the length it
saves goes into a larger rectangle. And `x = 0` is the ceiling: a radius above
`(P − L) / (8 − 2π)` would need a path outside the mounting surface, however
much the corner itself would fit.

Moving an entry from `trials.toml` into `parts.toml` is what commits to it:
that is what gets it built into the committed output and covered by both
records. Doing so is not the same as settling the design — an entry can sit
there provisionally, as these corners do.

## Mount them

1. Work out the strip's path on the TV back first, with the strip held in place
   dry. The corners are what set the geometry; the straights fill between them.
2. Clean each bracket's footprint on the panel with isopropyl alcohol. This is
   the step that decides whether the adhesive lasts.
3. Stick the brackets down with VHB or similar double-sided tape on the flat
   pad. The pad is 22 mm deep and unbroken — there is no screw hole to work
   around.
4. **Thread the strip in from the end rather than snapping it in along its
   length.** A 125 mm channel takes real force to flex a strip past both lips
   at once, and at a corner threading is the only option anyway.

**Which way round.** The channel leans *away* from the centre of the TV, so
light clears the panel edge instead of being caught by it. At a corner, the
arc's centre is toward the middle of the TV — the narrow end of the fan points
inward.

## How it works

### One profile, two sweeps

A bracket is a 2D profile swept. Extrude it and you have a straight run;
revolve it about an axis standing off to one side and you have a corner. Both
come from the same `CrossSection` object, so a corner cannot disagree with a
straight about the channel — there is only one channel. `uv run verify` asserts
this directly: it cuts a section through each corner's arc and checks it comes
back as the straight's section.

That is also why the reference corner brackets are not used here. Measured,
their curve turns only 37–48°, is not a true arc, and shares no feature with
the straight section — no clip, no lean. Matching them would have meant keeping
two unrelated designs in step by hand forever.

### The channel is the clip

| | |
|---|---|
| Bed, where the strip lies | 15.0 mm wide, 4.0 mm deep |
| Mouth, at the face | 12.0 mm |
| Wall, each side | 1.5 mm |
| Floor under the bed | 2.0 mm |

The strip flexes past the 15 → 12 mm neck and is then held mechanically. Every
other number in the part follows from this block and the 45° lean.

### Everything derives from one constraint

The channel block rests **on** the base plane at its outboard-bottom corner.
That single constraint fixes the channel's height above the TV back (7.78 mm),
where the arm's wall drops (7.78 mm inboard of the channel's own datum), the tab
length (9.27 mm) and the profile's overall depth (26.24 mm) — all four matching
the reference mesh to under 0.01 mm, with no coordinate transcribed from it.

### Two things the reference had that this does not

**The countersunk screw hole is gone.** These mount with adhesive, so a bore
through the pad was dead weight — and it was eating about 36 mm² of the contact
area the adhesive needs.

**The triangular tunnel under the arm is gone.** It was a material saving baked
permanently into the mesh. Sparse infill does the same job, better, and stays a
slicer setting you can change per print.

### The tab earns its length

The plate runs 9.27 mm past the arm on the inboard side. That overhang is not
decoration. The strip sits in a channel leaning outboard, so its weight and its
springiness apply a moment that tries to lift the *outboard* edge of the pad off
the panel, pivoting about the arm's outer edge. The tab sits on the far side of
that pivot, and its length is the lever arm resisting the lift.

It is the same peeling action that pulled the strip's original adhesive off.
Shortening the tab would have traded away resistance to the one failure these
brackets exist to prevent.

## Changing the numbers

Every dimension is an independent knob, and all of them live in `parts.toml`:
the slot's width and depth set what strip fits, the lip's reach sets how hard it
clips, the base depth sets the adhesive pad, and the lean sets how far out the
light is thrown. The parts themselves are entries in the same file:

```toml
[[straight]]
name = "straight-125mm-v1"
length = 125.0

[[corner]]
name = "corner-r101-v1"
radius = 101.0
tilt = 65.0        # this corner only; everything else takes the design's lean
```

Parts still being tested live in `trials.toml` instead. What they produce is
written to `output/trials/hue-tv-brackets/`, which is not committed and is
covered by neither lock -- a trial is printed to answer a question, not kept.
Deleting that file
retires every one of them: the next build moves their STLs to the archive and
leaves `output/` holding only what ships.

No code changes for any of this. The code changes when the *shape* does.

Then, from the repo root:

```sh
uv run build hue-tv-brackets   # regenerate STLs into output/
uv run verify                  # check geometry before printing
uv run pytest                  # check the code
```

**Changing the lean is a trade, not a free choice.** A shallower lean makes the
bracket sit lower and reach less far past its pad — 3.0 mm at 30° against
4.2 mm at 45° — and it eases the lip's overhang, from 8° off the bed to 23°.
But the lean is also what buys corner relief, and that falls with it: at 30° the
relief is 1.155× instead of 1.414×, so an R30 corner would bend the strip like
an in-plane R34.6 rather than R42.4. Tilting down 15° costs about what tightening
R30 to R24 would. Less light reaches the wall, too, which was the point of the
lean to begin with.

A corner tighter than 17.05 mm is refused rather than built: below that the
pad's inner edge reaches the revolve axis and the part would fold through
itself. A turn cannot be made by a part that reaches past its own centre.

`uv run verify` measures the built solids rather than reading the parameters
back. It checks that the channel still necks down to a clip rather than an open
trough, that it still lies at its lean, that the adhesive pad is flat and full
depth, that nothing encloses a pocket, that each corner turns a full quarter and
stops, and that every corner is still the straight bent.

### The files

| File | What lives there |
|---|---|
| `__init__.py` | Declares this project so the repo discovers it |
| `parts.toml` | Every measured or chosen number, and the parts that ship |
| `trials.toml` | Parts being tested; their STLs are never committed, and deleting this retires all of them |
| `geometry.py` | The channel, the lean, and the two sweeps |
| `catalog.py` | How a configured entry becomes a printable bracket |
| `verify.py` | Geometric checks against the built solids |
| `LOCKED.txt` | Hashes of the STLs this project has shipped |
| `MEASURED.txt` | What the pre-print checks read off those STLs |
| `reference/` | The straight bracket every dimension was measured from |

Building, locking, soundness and verification are covered by the repo-wide
contract, so this project writes no test boilerplate of its own — see
[docs/build/project-contract.md](../../../docs/build/project-contract.md).
