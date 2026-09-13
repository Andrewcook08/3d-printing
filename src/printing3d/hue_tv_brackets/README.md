# Hue gradient lightstrip brackets

Clip brackets that carry a Philips Hue gradient lightstrip around the back of a
TV without any adhesive on the strip itself, and hold it at 45° so it throws
light along the wall rather than straight at it.

Two shapes — a straight run and a 90° corner — generated from one profile, so
they are the same bracket swept two ways and cannot drift apart.

Shape follows `reference/Hue LED Strip with Angle straight section.stl`,
rebuilt parametrically rather than traced. Every dimension below was measured
off that mesh.

> **Note.** Everything below about **corners** is out of date, including the
> print list: the 45° ladder it recommends was printed and every rung bound.
> Those three parts have moved to `trials.toml`, and the leaned trials that
> replaced them are not described here at all. The straight runs and the channel
> are unaffected and still current. This README is rewritten once the corner's
> design is settled.

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
| **`output/hue-tv-brackets/corner-r30-v1.stl`** | 39.2 × 39.2 × 17.0 mm | 6.3 cm³ |
| **`output/hue-tv-brackets/corner-r40-v1.stl`** | 49.2 × 49.2 × 17.0 mm | 8.7 cm³ |
| **`output/hue-tv-brackets/corner-r55-v1.stl`** | 64.2 × 64.2 × 17.0 mm | 12.2 cm³ |

The brackets are universal — nothing here is sized to a particular TV or strip
length, so how many straights a run takes, and whether you need corners at two
of the TV's corners or all four, follows from the TV and the strip in front of
you.

The three corners are a **radius ladder**, not three products. Print one of
each, try the strip in all three, and keep the sharpest that does not fight it.
See [Choosing the radius](#choosing-the-radius).

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
is real relief, but not immunity — and how much in-plane bend a given strip
tolerates is not something that can be derived. Hence the ladder.

| Radius | Inner edge | Outer edge | Strip spent per corner |
|---|---|---|---|
| 30 mm | 12.95 mm | 39.19 mm | 47 mm |
| 40 mm | 22.95 mm | 49.19 mm | 63 mm |
| 55 mm | 37.95 mm | 64.19 mm | 86 mm |

Sharper is not only tidier. The arc eats strip that the straight runs then go
without — across four corners, R30 spends 189 mm against R55's 345 mm. If your
strip is close-fitted to the TV, that difference decides whether the ends meet.

Once you have picked one, delete the other two from the catalog and re-lock.

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

Parts still being tested live in `trials.toml` instead. Deleting that file
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
| `trials.toml` | Parts being tested; delete it to retire all of them |
| `geometry.py` | The channel, the lean, and the two sweeps |
| `catalog.py` | How a configured entry becomes a printable bracket |
| `verify.py` | Geometric checks against the built solids |
| `LOCKED.txt` | Hashes of the STLs this project has shipped |
| `reference/` | The straight bracket every dimension was measured from |

Building, locking, soundness and verification are covered by the repo-wide
contract, so this project writes no test boilerplate of its own — see
[docs/build/project-contract.md](../../../docs/build/project-contract.md).
