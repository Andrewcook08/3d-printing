"""Turning a config file into the dataclass a project asked for."""

from dataclasses import dataclass, field

import pytest

from printing3d.config import ConfigError, read, read_if_present


@dataclass(frozen=True, kw_only=True)
class Channel:
    width: float
    depth: float = 4.0


@dataclass(frozen=True, kw_only=True)
class Entry:
    name: str
    radius: float


@dataclass(frozen=True, kw_only=True)
class Catalogue:
    corner: list[Entry] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class Design(Catalogue):
    channel: Channel


def written(tmp_path, text, name="parts.toml"):
    path = tmp_path / name
    path.write_text(text)
    return path


# ---------------------------------------------------------------------------
# What a good file becomes
# ---------------------------------------------------------------------------


def test_a_table_becomes_the_dataclass_that_was_asked_for(tmp_path):
    design = read(written(tmp_path, "[channel]\nwidth = 15.0\n"), into=Design)
    assert design.channel == Channel(width=15.0, depth=4.0)


def test_a_whole_number_is_accepted_where_a_decimal_is_wanted(tmp_path):
    """TOML tells 15 from 15.0; geometry wants the float either way."""
    design = read(written(tmp_path, "[channel]\nwidth = 15\n"), into=Design)
    assert design.channel.width == 15.0
    assert isinstance(design.channel.width, float)


def test_an_array_of_tables_becomes_a_list_of_entries(tmp_path):
    text = '[channel]\nwidth = 15.0\n[[corner]]\nname = "a"\nradius = 51.0\n'
    design = read(written(tmp_path, text), into=Design)
    assert design.corner == [Entry(name="a", radius=51.0)]


def test_a_list_left_out_entirely_is_empty(tmp_path):
    assert (
        read(written(tmp_path, "[channel]\nwidth = 15.0\n"), into=Design).corner == []
    )


# ---------------------------------------------------------------------------
# What a bad file does instead
# ---------------------------------------------------------------------------


def test_a_key_nobody_asked_for_is_refused_and_named(tmp_path):
    """The check that keeps config to what was measured: a derived value
    written down by hand is refused the same way a typo is."""
    text = "[channel]\nwidth = 15.0\nmouth = 12.0\n"
    with pytest.raises(ConfigError, match="mouth") as refused:
        read(written(tmp_path, text), into=Design)
    assert "width" in str(refused.value), "it should say what it does take"


def test_a_required_value_left_out_is_refused_and_named(tmp_path):
    with pytest.raises(ConfigError, match="width"):
        read(written(tmp_path, "[channel]\ndepth = 4.0\n"), into=Design)


def test_a_value_of_the_wrong_type_is_refused(tmp_path):
    with pytest.raises(ConfigError, match="width"):
        read(written(tmp_path, '[channel]\nwidth = "wide"\n'), into=Design)


def test_true_is_not_a_number(tmp_path):
    """isinstance(True, int) is true in Python, so this needs its own guard."""
    with pytest.raises(ConfigError, match="width"):
        read(written(tmp_path, "[channel]\nwidth = true\n"), into=Design)


def test_a_failure_inside_an_array_names_which_entry(tmp_path):
    text = (
        "[channel]\nwidth = 15.0\n"
        '[[corner]]\nname = "a"\nradius = 51.0\n'
        '[[corner]]\nname = "b"\n'
    )
    with pytest.raises(ConfigError, match=r"corner\[1\]"):
        read(written(tmp_path, text), into=Design)


def test_a_missing_section_is_refused(tmp_path):
    with pytest.raises(ConfigError, match="channel"):
        read(written(tmp_path, "# nothing here\n"), into=Design)


def test_a_malformed_file_is_refused_by_name(tmp_path):
    with pytest.raises(ConfigError, match="not valid TOML"):
        read(written(tmp_path, "[channel\nwidth = 15.0\n"), into=Design)


def test_a_missing_file_is_refused_by_name(tmp_path):
    with pytest.raises(ConfigError, match="missing"):
        read(tmp_path / "absent.toml", into=Design)


# ---------------------------------------------------------------------------
# The file a project may or may not have
# ---------------------------------------------------------------------------


def test_an_absent_optional_file_reads_as_empty(tmp_path):
    """Deleting the file is how everything in it is retired."""
    assert read_if_present(tmp_path / "trials.toml", into=Catalogue) == Catalogue()


def test_an_optional_file_that_is_present_is_read_normally(tmp_path):
    path = written(tmp_path, '[[corner]]\nname = "t"\nradius = 99.0\n', "trials.toml")
    assert read_if_present(path, into=Catalogue).corner == [
        Entry(name="t", radius=99.0)
    ]


def test_an_optional_file_is_still_validated(tmp_path):
    path = written(tmp_path, '[[corner]]\nname = "t"\nbogus = 1\n', "trials.toml")
    with pytest.raises(ConfigError, match="bogus"):
        read_if_present(path, into=Catalogue)
