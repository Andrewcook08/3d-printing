# Hue TV brackets — design

Adhesive-free mounting for a Philips Hue gradient lightstrip that wraps all
four sides of a TV, in matching straight and corner sections.

## The problem

The strip was mounted to the TV back with its own adhesive. The adhesive crept
away from the panel, the strip sagged unevenly, and the wall wash went patchy.
A printed bracket with a clip channel removes the adhesive from the strip
entirely: the bracket is stuck down, the strip snaps into it.

A second problem is aim. The wall behind this TV is dark, so a strip firing
straight back produces less wash than wanted. Holding the strip at 45° throws
light out and back rather than only back.

Both are solved by an existing third-party straight bracket, kept in
`reference/`. What does not exist is a matching corner: the strip wraps all
four sides, and off-the-shelf corner parts are built for the Play gradient
strip, which covers sides and top only. Those corner parts also share none of
the straight section's design — no clip, no 45°.

## What ships

| Part | Description |
|---|---|
| `straight-125mm-v1` | The long run. Print as many as the TV needs. |
| `corner-r30-v1` | Radius ladder — sharpest |
| `corner-r40-v1` | Radius ladder |
| `corner-r55-v1` | Radius ladder — most relaxed |

The brackets are universal: nothing is sized to a particular TV. How many
straights to print follows from the TV; corners are two or four depending on
whether the strip wraps fully or covers sides and top only.

## Approach

**One profile, swept two ways.** A single cross-section is built once and
consumed twice — extruded for a straight section, revolved 90° about an offset
axis for a corner. Straights and corners cannot disagree about the channel,
because there is only one channel. This is the central decision; everything
else follows.

The alternative considered and rejected was adapting the reference corner
parts. Measured, their curve turns only 37–48° and is not a true arc, and they
share no feature with the straight section. Reusing them would mean matching
two unrelated designs by hand, forever.

## The profile

All dimensions measured from `reference/Hue LED Strip with Angle straight
section.stl`, which stays in the repo as the source of these numbers.

Authored in `(X = distance from the revolve axis, outboard positive;
Y = height above the TV back)`.

**The channel**, in its own 45°-rotated frame — symmetric, and round enough to
confirm the original was drawn parametrically:

| Feature | Value |
|---|---|
| Block, overall | 18.0 wide × 6.0 deep |
| Slot | 15.0 wide × 4.0 deep |
| Wall, each side | 1.5 |
| Floor under the slot | 2.0 |
| Lip | closes 1.5 inward while rising 2.0 |
| Mouth | 12.0 |

The 15.0 → 12.0 neck is the clip: the strip flexes past the lips and is held
without adhesive.

**The rest**: a 2.0 mm base plate, 22.0 mm deep at its contact face; the
channel block set at 45°; the block's side faces run straight down to meet the
plate, which is what forms the arm. Overall height 17.0 mm.

**Two derived distances set every corner**, measured from the channel
centerline:

| To | Distance |
|---|---|
| Tab edge (innermost material) | 17.05 |
| Arm outer edge (outermost material) | 9.20 |

### Two changes from the reference

- **The countersunk screw hole is removed.** These mount with adhesive, so the
  bore is dead weight, and deleting it returns about 36 mm² of contact area per
  bracket.
- **The triangular tunnel under the arm is removed.** It was a material saving
  baked into the mesh; sparse infill is the slicer's job and is changeable per
  print. The part becomes solid and nothing observable changes.

The tab is **not** shortened. It sits on the far side of the pivot the strip's
weight levers about, so its length is what resists the base peeling off the TV
— the exact failure being designed away from.

## The corner

`profile.translate((R, 0)).revolve(segments, 90)`. The revolve is about the
profile's own Y axis, which is why the profile is translated out by R rather
than given an axis to spin about.

R is measured to the channel centerline, where the strip actually is.
Resolution: 128 segments per full turn, so 32 across the 90°; chord error at
R30 is 0.02 mm.

| R | Inner radius | Outer radius | Strip consumed |
|---|---|---|---|
| 30 | 12.95 | 39.20 | 47 mm |
| 40 | 22.95 | 49.20 | 63 mm |
| 55 | 37.95 | 64.20 | 86 mm |

**Why a ladder rather than a number.** Revolving about an axis perpendicular to
the TV back bends the strip about that same axis, which sits 45° between the
strip's easy bend (about its width) and its in-plane bend (about its face
normal), so the curvature splits cos 45° each way. The 45° tilt buys a factor
of √2 of relief over laying the strip flat — real, but not immunity. The
in-plane tolerance of this particular strip is not known and cannot be derived,
so it gets measured: print three, keep the sharpest that does not bind.

Geometry sets a hard floor at R = 17.05, where the tab edge lands on the axis
and the wedge self-intersects. That floor is far below anything the strip will
tolerate, so it never governs.

### Resolving the ladder

Once a radius wins, the losing rungs are deleted and `LOCKED.txt` regenerated —
an explicit, stated re-lock, not a test edited to pass.

## Printing

Base-down, which is the only orientation a revolved corner has. The arm's
underside lands at exactly 45°, self-supporting.

**One lip overhangs at 8° from the bed and is accepted as-is.** The channel is
tilted 45° and a lip is by definition an undercut, so on the upper side tilt
and undercut add and on the lower side they cancel. No chamfer angle fixes it
without removing the undercut, and that lip is the one gravity settles the
strip against. Unsupported reach is 1.5 mm. This has been printed: the lip
comes out slightly rough, the hold is unaffected. Support inside a 12 mm slot
would risk the clip while removing it, so it is not used.

## Verification

`uv run verify` measures the built solids, never the constants they came from:

- the mouth is narrower than the channel floor — it genuinely clips
- the channel floor clears the strip in width and depth
- the channel sits at 45° to the base plane
- the base is flat and coplanar with the mounting plane
- the profile contains no enclosed voids, proving the tunnel is gone
- each corner's inner radius is positive, and its arc turns 90°
- **a radial section through a corner matches a straight's cross-section** —
  same area, same mouth, same floor

The last one is the point of the whole design, asserted rather than assumed.

## Tests

In `tests/hue_tv_brackets/`: characterization of the shipped profile (vertex
count, area, vertex digest), and property tests for the two relationships that
must hold at any radius or length — that the mouth is narrower than the floor,
and that a corner's radial section equals the straight's section. Building,
locking, soundness and verification come free from the contract suite.

## Shared kit

**This project adds nothing to the shared kit.** Profile construction, the 45°
angle check and the enclosed-void check are all already covered by it.

Two helpers written here are domain-free and will look promotable. Both stay
local, marked in their own docstrings, until a second project needs them:

- **`radial_section`** — the cross-section of a solid at an angle about an
  axis. The stronger candidate: it is a measurement primitive of the same
  shape as the ones the kit already has, and any curved part would want it.
- **`revolve_about`** — offset a profile and revolve it. Recommended *not* to
  promote even later: it is one line, and what is actually reusable is the
  knowledge that the revolve takes no axis parameter, which belongs in a
  comment at the call site rather than hidden in a wrapper.

## Files

Added under `src/printing3d/hue_tv_brackets/`: the project declaration, the
geometry, the catalog, the checks, `LOCKED.txt`, and a README covering print
settings and how many of each part to print. Tests under
`tests/hue_tv_brackets/`.

Removed: `reference/Philips Hue Mounts v2 Left.stl` and
`reference/Philips Hue Mounts v2 right.stl`. Nothing in the design derives from
them.

## Deferred

- A shorter straight length, if 125 mm alone leaves awkward remainders.
- Shrinking the lower lip to about 0.8 mm, if the droop ever proves to matter.
- Whether a 125 mm channel is too stiff to snap a strip into along its length;
  threading from the end is the fallback, and is required at corners anyway.
