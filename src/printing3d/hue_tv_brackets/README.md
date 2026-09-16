# Hue gradient lightstrip brackets

Clip brackets that carry a Philips Hue gradient lightstrip around the back of a
TV without any adhesive on the strip itself, and hold it at 45° so it throws
light along the wall rather than straight at it.

A straight run and a 90° corner, generated from one profile, so they are the
same bracket swept and cannot drift apart. A corner may also be asked for with
straight runs led into and out of it, which turn from the straights' lean to
the corner's inside the plastic rather than leaving the strip to do it across
a gap.

Shape follows `reference/Hue LED Strip with Angle straight section.stl`,
rebuilt parametrically rather than traced. Every dimension below was measured
off that mesh.

> **Note.** The printing established why the corners stand upright: every rung
> of the leaning radius ladder bound. The passages that argued for a leaning
> corner are replaced rather than kept. The **channel** is untouched throughout
> — nothing the printing disproved reached the clip, its dimensions, or why the
> straights lean.
>
> The corner with runs led into it is still a trial. It is not in `parts.toml`
> and nothing here claims it has been printed.

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

Five parts ship: straight runs at 8, 5, 3 and 2 inches, all leaning 45°, and
one upright corner at a 1.5 inch radius. `uv run build` prints every file it
writes and where, which stays accurate as the set changes.

The brackets are universal — nothing here is sized to a particular TV or strip
length, so how many straights a run takes, and whether you need corners at two
of the TV's corners or all four, follows from the TV and the strip in front of
you.

A corner's radius is a fitting choice rather than a structural one — standing
upright, the turn puts none of itself into the strip's own plane, so there is
nothing to be sharp about. Pick by how the strip has to sit on your TV; see
[What picks the radius, then](#what-picks-the-radius-then).

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
that is what makes it a part this project ships, built into the committed
output and covered by both records.

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

### One profile, three sweeps

A bracket is a 2D profile swept. Extrude it and you have a straight run;
revolve it about an axis standing off to one side and you have a corner; sweep
it while its lean changes and you have a run that turns from one to the other.
All three come from the same profile, so a corner cannot disagree with a
straight about the channel — there is only one channel. `uv run verify` asserts
this directly: it cuts a section through each corner's arc and checks it comes
back as the straight's section.

The turning run is the one that cannot be swept in a single operation. The
profile's outline does not merely rotate as it leans — features merge into each
other and its corner count changes — so there is nothing to interpolate
between, and turning the whole profile instead would lift the mounting plate
off the TV. It is built as a stack of thin slabs, and the channel is cut from
that stack afterwards, in one piece, turning about the middle of its own bed.
That last part is what keeps the promise below: the channel turns around the
strip rather than carrying the strip around with it, so no approximation in the
stack can move where the strip sits.

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

### The strip's place is chosen, so the lean is free

The block used to rest **on** the base plane at its outboard-bottom corner, and
everything else followed from that. It made the strip's height a consequence of
the lean: 7.78 mm at 45°, 9.00 mm at 90°. Build a straight at one lean and a
corner at another and the strip steps out at every corner and back in.

So the strip's place is now the fixed thing and the plastic adapts to it. The
channel sits **9.50 mm** above the TV back and the plate reaches **4.0 mm**
outboard of the strip's centre, at every lean — and through a turning run as
well, not only across leans. The block floats above where it
would have rested — 1.72 mm at 45° — and the arm carries it.

The height is not a free number. It is the lowest that clears two bounds at
once, and both are computed rather than chosen:

- **The block must not dip through the TV back.** What would rest it on the
  plane is `(block/2)·sin + floor·cos`, which peaks near 77.5° rather than at
  either end — so the steepest bracket is not the worst case. Its maximum over
  every lean is `hypot(block/2, floor)` = 9.22 mm.
- **The plate must not intrude into the channel.** Reaching outboard past the
  strip puts the plate under the channel's low end, and too low a floor fills
  the bottom of the slot — the bed measures short while nothing looks wrong.
  Clearing it takes `plate + channel/2` = 9.50 mm.

The second is the binding one here. The tab length (18.0 mm) and the profile's
overall depth (27.19 mm) then follow from the reach.

### Two things the reference had that this does not

**The countersunk screw hole is gone.** These mount with adhesive, so a bore
through the pad was dead weight — and it was eating about 36 mm² of the contact
area the adhesive needs.

**The triangular tunnel under the arm is gone.** It was a material saving baked
permanently into the mesh. Sparse infill does the same job, better, and stays a
slicer setting you can change per print.

### The tab earns its length

The plate runs 18.0 mm past the strip's centre on the inboard side — whatever
is left of the 22 mm footprint once the 4.0 mm outboard reach is taken off it.
That overhang is not decoration. The strip sits in a channel leaning outboard, so its weight and its
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

[[corner]]
name = "corner-r38-lead4in-v1"
radius = 38.1
tilt = 90.0
lead = 101.6       # straight run either side of the turn
twist = 76.2       # of which this much turns, measured back from the corner
```

`lead` and `twist` are optional and go together. A corner naming neither is the
bare turn, to be butted against straight sections by hand. Naming both gives it
a run at each end that meets the strip at the straights' lean, holds it for
`lead - twist`, and turns to the corner's lean over the last `twist`. The turn
is measured back from the corner, so the channel is upright before the turn
starts whatever the two lengths are — lengthening the run moves the straight
part of it, never the turn.

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

**The lean no longer moves the strip, but it is still a trade.** A shallower
lean eases the lip's overhang and throws less light at the wall, which was the
point of leaning in the first place. It also buys less corner relief: relief
scales with the cosine, so 30° would give 1.155× against 45°'s 1.414× — an R30
corner bending the strip like an in-plane R34.6 rather than R42.4.

**Below about 45° the design refuses itself.** The block's resting corner
reaches further outboard as the lean shallows, and once it passes the plate's
4.0 mm reach the block would meet the TV back beyond the edge of the pad. The
error names the lean and the distance. Raising `pad_outboard` buys shallower
leans, at the cost of a shorter tab within the same footprint.

A corner tighter than 18.0 mm is refused rather than built: below that the
pad's inner edge reaches the revolve axis and the part would fold through
itself. A turn cannot be made by a part that reaches past its own centre.

`uv run verify` measures the built solids rather than reading the parameters
back. It checks that the channel still necks down to a clip rather than an open
trough, that it still lies at its lean, that the adhesive pad is flat and full
depth, that nothing encloses a pocket, and that every corner is still the
straight bent. A bare corner is checked to turn a full quarter and stop there;
one with runs led into it is checked to carry the quarter and then reach its
full lead past the turn on both sides, which is what a corner with runs does
instead of stopping.

### The files

| File | What lives there |
|---|---|
| `__init__.py` | Declares this project so the repo discovers it |
| `parts.toml` | Every measured or chosen number, and the parts that ship |
| `trials.toml` | Parts being tested; their STLs are never committed, and deleting this retires all of them |
| `geometry.py` | The channel, the lean, and the three sweeps |
| `catalog.py` | How a configured entry becomes a printable bracket |
| `verify.py` | Geometric checks against the built solids |
| `LOCKED.txt` | Hashes of the STLs this project has shipped |
| `MEASURED.txt` | What the pre-print checks read off those STLs |
| `reference/` | The straight bracket every dimension was measured from |

Building, locking, soundness and verification are covered by the repo-wide
contract, so this project writes no test boilerplate of its own — see
[docs/build/project-contract.md](../../../docs/build/project-contract.md).
