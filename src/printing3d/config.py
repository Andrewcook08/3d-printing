"""Reading a project's parameters from the file that holds them.

A project's measured and chosen numbers live in TOML beside its code, so tuning
a part is an edit to data rather than to the code that builds it. Nothing here
knows what any project makes -- only how to turn a file of values into the
frozen dataclass a project asked for.

The dataclass is the schema. Its fields name the tables and values a file may
contain, its annotations say what they must be, and its defaults say what may be
left out. There is no second place to keep a schema in step with.

Unknown keys are refused rather than ignored, which is what keeps a config file
to what was measured or chosen: a value the code can derive has no business
being restated here, and a misspelling is a failure rather than a silently
absent number.
"""

import tomllib
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from types import UnionType
from typing import get_args, get_origin, get_type_hints

SCALARS = (bool, int, float, str)

# What a field may ask for. Said once, so a field asking for something else
# is told what it could have asked for instead.
NOT_A_SHAPE = (
    "which is not a config shape; a field takes a number, text, true/false, "
    "another dataclass, a list of those, or any of them or None"
)


class ConfigError(ValueError):
    """A config file that cannot be trusted to build what it claims."""


def read(path: Path, into: type):
    """The config file at `path`, as an instance of the dataclass `into`."""
    return _built(into, _parsed(path), where=path.name)


def read_if_present(path: Path, into: type):
    """The same, or an empty `into` when the file is absent.

    For the files a project may or may not have -- a set of trial parts being
    tested today and gone tomorrow. Absent and empty mean the same thing, so
    deleting the file is how you retire everything in it.
    """
    return _built(into, _parsed(path) if path.is_file() else {}, where=path.name)


def _parsed(path):
    """The file's raw tables, or a failure that names the file."""
    if not path.is_file():
        raise ConfigError(f"{path} is missing")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as malformed:
        raise ConfigError(f"{path} is not valid TOML: {malformed}") from malformed


def _built(into, table, where):
    """`table` as an instance of `into`, or a failure that names the key."""
    expected = get_type_hints(into)
    _refuse_unknown(table, expected, where)
    _refuse_missing(into, table, where)
    return into(
        **{
            key: _converted(expected[key], value, f"{where}.{key}")
            for key, value in table.items()
        }
    )


def _refuse_unknown(table, expected, where):
    """Keys nobody asked for are the whole point of validating: a typo, or a
    value that should have been derived rather than written down."""
    unknown = sorted(set(table) - set(expected))
    if unknown:
        raise ConfigError(
            f"{where} has no place for {', '.join(unknown)}; "
            f"it takes {', '.join(sorted(expected))}"
        )


def _refuse_missing(into, table, where):
    """A field with no default has to be supplied; one with a default need not."""
    missing = sorted(
        field.name
        for field in fields(into)
        if field.name not in table
        and field.default is MISSING
        and field.default_factory is MISSING
    )
    if missing:
        raise ConfigError(f"{where} is missing {', '.join(missing)}")


def _converted(annotation, value, where):
    """`value` as the annotation asks for it, or a failure that names where."""
    if get_origin(annotation) is UnionType:
        return _converted(_without_none(annotation, where), value, where)
    if is_dataclass(annotation):
        return _built(annotation, _as_table(value, where), where)
    if get_origin(annotation) is list:
        return _entries(get_args(annotation)[0], value, where)
    return _scalar(annotation, value, where)


def _entries(entry_type, value, where):
    """Every entry of a list, numbered so a failure is findable."""
    if not isinstance(value, list):
        raise ConfigError(f"{where} should be a list, not {_named(value)}")
    return [
        _converted(entry_type, entry, f"{where}[{index}]")
        for index, entry in enumerate(value)
    ]


def _as_table(value, where):
    if not isinstance(value, dict):
        raise ConfigError(f"{where} should be a table, not {_named(value)}")
    return value


def _scalar(annotation, value, where):
    """A plain value, with one coercion: a whole number where a decimal is
    wanted. TOML tells 45 from 45.0 and geometry wants the float either way."""
    if annotation not in SCALARS:
        raise ConfigError(f"{where} asks for {_shape(annotation)}, {NOT_A_SHAPE}")
    if annotation is float and isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    if type(value) is annotation:
        return value
    raise ConfigError(f"{where} should be {_shape(annotation)}, not {_named(value)}")


def _without_none(annotation, where):
    """The real type behind `T | None`.

    An optional field says "the value this belongs to has a sensible answer
    already" -- a part that does not name its own lean takes the design's.
    Anything else in a union is a schema nobody should be writing.
    """
    offered = [arg for arg in get_args(annotation) if arg is not type(None)]
    if len(offered) != 1:
        raise ConfigError(f"{where} asks for {annotation}, {NOT_A_SHAPE}")
    return offered[0]


def _named(value):
    """What a value is, for an error message: `12 (int)`."""
    return f"{value!r} ({type(value).__name__})"


def _shape(annotation):
    """What a field asked for, as a name a reader will recognise."""
    return getattr(annotation, "__name__", str(annotation))
