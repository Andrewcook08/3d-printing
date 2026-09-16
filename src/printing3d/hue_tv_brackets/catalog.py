"""What actually gets printed.

Two shapes, swept from the one profile in geometry.py: straight runs for the
sides of the TV, and 90-degree corners, which may be asked for with straight
runs led into and out of them. The brackets are universal, so how many of each
a TV needs is the TV's business, not this catalog's.

The numbers live in parts.toml, and parts still being tested live in
trials.toml. A part may lean differently from the shipped design; anything it
does not say for itself it takes from there. This module only says how a
configured entry becomes a solid.

See README.md for the design.
"""

import math
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field, replace

from printing3d import config
from printing3d.hue_tv_brackets import CONFIG, NAME
from printing3d.hue_tv_brackets.geometry import (
    QUARTER_TURN,
    Design,
    corner,
    led_corner,
    straight,
)
from printing3d.parts import Part, build_project, trials_dir

TRIALS = CONFIG.parent / "trials.toml"

MM2_PER_CM2 = 100.0


@dataclass(frozen=True, kw_only=True)
class StraightEntry:
    """One straight run, as parts.toml describes it."""

    name: str
    length: float
    tilt: float | None = None
    note: str = ""


@dataclass(frozen=True, kw_only=True)
class CornerEntry:
    """One corner, as parts.toml describes it.

    `lead` and `twist` are optional and go together: a corner naming neither
    is the bare turn, to be joined to straight runs by hand.
    """

    name: str
    radius: float
    tilt: float | None = None
    lead: float | None = None
    twist: float | None = None
    note: str = ""


@dataclass(frozen=True, kw_only=True)
class Catalogue:
    """The parts a config file asks for."""

    straight: list[StraightEntry] = field(default_factory=list)
    corner: list[CornerEntry] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class Shipping(Catalogue):
    """The same, plus the design every part is built from."""

    design: Design


@dataclass(frozen=True)
class Bracket(Part, ABC):
    """A printable bracket, carrying the design it was built from so that
    verify.py can measure the solid against its own intent."""

    design: Design
    note: str

    @abstractmethod
    def footprint_line(self) -> str:
        """One line about what this bracket lands on the TV, for build output.

        Abstract rather than raising: a shape that forgets it should fail when
        it is constructed, not partway through a build with files already on
        disk.
        """

    def annotated(self, measurements: str) -> str:
        """A build-output line: what was measured, then why the part exists."""
        return f"{measurements}{'   -- ' + self.note if self.note else ''}"


@dataclass(frozen=True)
class StraightBracket(Bracket):
    """A straight run, carrying the length it was built from."""

    length: float

    def footprint_line(self) -> str:
        pad = self.length * self.design.base_depth / MM2_PER_CM2
        return self.annotated(
            f"    straight  pad {pad:6.1f} cm2 over {self.length:5.1f} mm of strip"
        )


@dataclass(frozen=True)
class CornerBracket(Bracket):
    """A quarter turn, carrying the radius it was built from."""

    radius: float
    lead: float = 0.0
    twist: float = 0.0

    @property
    def inner_radius(self) -> float:
        """Where the tab edge sweeps -- the innermost material."""
        return self.radius - self.design.to_tab_edge

    @property
    def outer_radius(self) -> float:
        """Where the arm's outer edge sweeps."""
        return self.radius + self.design.to_outermost

    @property
    def strip_spent(self) -> float:
        """Strip consumed by this part, which the straight runs then go without."""
        return math.radians(QUARTER_TURN) * self.radius + 2 * self.lead

    def footprint_line(self) -> str:
        led = (
            f", leads {self.lead:.1f} mm turning over the last {self.twist:.1f}"
            if self.lead
            else ""
        )
        return self.annotated(
            f"    corner    r{self.radius:<5.1f} {self.design.tilt:.0f} deg, "
            f"inner {self.inner_radius:5.2f} mm, outer {self.outer_radius:5.2f} mm, "
            f"spends {self.strip_spent:5.1f} mm{led}"
        )


def shipping() -> Shipping:
    """The design and the parts that ship, validated."""
    return config.read(CONFIG, into=Shipping)


def trials() -> Catalogue:
    """The parts still being tested. Absent means there are none."""
    return config.read_if_present(TRIALS, into=Catalogue)


def parts(ships: Shipping | None = None) -> Iterator[Bracket]:
    """Every bracket this project ships, in the order it is listed and printed.

    What the project declares, and so what is committed, locked and measured
    against. Defaults to the shipped file; a caller may pass its own to see
    what a different set of entries would produce.
    """
    ships = shipping() if ships is None else ships
    yield from _brackets(ships.design, ships)


def trial_parts(
    ships: Shipping | None = None, tried: Catalogue | None = None
) -> Iterator[Bracket]:
    """Every bracket still being tested.

    Built and checked exactly like the rest, and committed like none of it. A
    trial takes its lean from its own entry where it names one, and otherwise
    from the shipped design, so a trial and a shipped part differ only where
    the trial says they do.
    """
    ships = shipping() if ships is None else ships
    tried = trials() if tried is None else tried
    yield from _brackets(ships.design, tried)


def _brackets(design: Design, catalogue) -> Iterator[Bracket]:
    """One catalogue's entries as brackets, straights before corners."""
    for entry in catalogue.straight:
        leaning = _leaning(design, entry)
        yield StraightBracket(
            name=entry.name,
            solid=straight(leaning, entry.length),
            design=leaning,
            note=entry.note,
            length=entry.length,
        )
    for entry in catalogue.corner:
        leaning = _leaning(design, entry)
        yield CornerBracket(
            name=entry.name,
            solid=_turn(design, leaning, entry),
            design=leaning,
            note=entry.note,
            radius=entry.radius,
            lead=entry.lead or 0.0,
            twist=entry.twist or 0.0,
        )


def _turn(design: Design, leaning: Design, entry: CornerEntry):
    """The solid an entry asks for: a bare turn, or one with runs led into it.

    The runs start at the lean the project's straights are drawn at, which is
    the shipped design's rather than the corner's own -- a corner naming a
    lean is saying how the turn stands, not how the strip reaches it.
    """
    if entry.lead is None and entry.twist is None:
        return corner(leaning, entry.radius)
    if entry.lead is None or entry.twist is None:
        raise ValueError(
            f"corner {entry.name!r} gives only one of lead and twist: a run "
            f"leading into a corner needs both its length and how much of "
            f"that length turns"
        )
    return led_corner(leaning, entry.radius, entry.lead, entry.twist, design.tilt)


def _leaning(design: Design, entry) -> Design:
    """The design as this entry wants it: its own lean, or the shipped one."""
    return design if entry.tilt is None else replace(design, tilt=entry.tilt)


def straights(brackets: list[Bracket]) -> list[StraightBracket]:
    """The straight runs among `brackets`."""
    return [part for part in brackets if isinstance(part, StraightBracket)]


def corners(brackets: list[Bracket]) -> list[CornerBracket]:
    """The corners among `brackets`."""
    return [part for part in brackets if isinstance(part, CornerBracket)]


def build_all() -> bool:
    """Write what ships, then what is being tested. True if every solid is sound.

    Two destinations rather than one: the trials land outside the committed
    output, so retiring them is deleting a config file and nothing else.
    """

    # Called through a wrapper rather than passed as Bracket.footprint_line:
    # the latter binds the base class's version and never reaches the subclass.
    def announce(part):
        return part.footprint_line()

    shipped = build_project(NAME, parts(), announce=announce)
    tried = build_project(NAME, trial_parts(), announce=announce, into=trials_dir(NAME))
    return shipped and tried
