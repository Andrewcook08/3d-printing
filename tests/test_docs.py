"""Rules a document has to satisfy, for the ones a machine can settle.

Documentation goes stale quietly. A renamed file leaves a dead link, a doc
added without being indexed is a doc nobody finds, and a command that was
renamed leaves an instruction that cannot be followed. None of that shows up in
a test run unless something looks, so these look.

What is checked here is references, not claims. Whether a number in a doc is
still true is a question no test can answer; that is what review is for. These
catch the failures that have an objectively right answer.
"""

import re
import tomllib

import pytest

from printing3d.parts import repo_root

ROOT = repo_root()
DOCS = ROOT / "docs"
INDEX = DOCS / "README.md"

# A repo path written in prose: backticked, containing a directory separator,
# and ending in an extension. Bare filenames are deliberately not matched --
# `catalog.py` means a different file in each project, so resolving it would
# invent a location the author never stated.
QUOTED_PATH = re.compile(r"`([\w./-]+/[\w.-]+\.(?:py|toml|txt|md|stl))`")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
RUN_COMMAND = re.compile(r"^\s*uv run ([\w-]+)", re.MULTILINE)

# Run through uv but not installed by this project. Listed rather than
# guessed at, so anything else a document promises has to be real.
DEV_TOOLS = frozenset({"pytest", "ruff", "ty", "python"})
FENCED_SHELL = re.compile(r"```sh\n(.*?)```", re.DOTALL)


def documents():
    """Every document in the repo, wherever it lives."""
    return sorted(
        [*DOCS.rglob("*.md"), ROOT / "README.md", ROOT / "CLAUDE.md"]
        + list((ROOT / "src" / "printing3d").glob("*/README.md"))
    )


def console_scripts():
    """The commands the project actually installs."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return set(tomllib.load(handle)["project"]["scripts"])


def linked_targets(text):
    """Every local link target in a document, ignoring URLs and anchors."""
    return [
        target
        for target in MARKDOWN_LINK.findall(text)
        if not target.startswith(("http://", "https://", "#"))
    ]


def test_there_are_documents_to_check():
    """Guards every rule below from passing because it found nothing."""
    assert len(documents()) > 5
    assert console_scripts()


@pytest.mark.parametrize("doc", documents(), ids=lambda doc: str(doc.relative_to(ROOT)))
def test_every_link_in_a_document_goes_somewhere(doc):
    dead = [
        target
        for target in linked_targets(doc.read_text())
        if not (doc.parent / target.split("#")[0]).exists()
    ]
    assert not dead, f"{doc.relative_to(ROOT)} links to {dead}, which do not exist"


@pytest.mark.parametrize("doc", documents(), ids=lambda doc: str(doc.relative_to(ROOT)))
def test_every_path_named_in_a_document_exists(doc):
    missing = [
        quoted
        for quoted in QUOTED_PATH.findall(doc.read_text())
        if not (ROOT / quoted).exists()
    ]
    assert not missing, f"{doc.relative_to(ROOT)} names {missing}, which do not exist"


@pytest.mark.parametrize("doc", documents(), ids=lambda doc: str(doc.relative_to(ROOT)))
def test_every_command_a_document_tells_you_to_run_exists(doc):
    promised = {
        command
        for block in FENCED_SHELL.findall(doc.read_text())
        for command in RUN_COMMAND.findall(block)
    }
    broken = sorted(promised - console_scripts() - DEV_TOOLS)
    assert not broken, (
        f"{doc.relative_to(ROOT)} promises {broken}, which is neither a command "
        f"this project installs nor a development tool it depends on"
    )


def test_every_doc_is_reachable_from_the_index():
    """An unreachable doc is an invisible doc."""
    index = INDEX.read_text()
    linked = {(INDEX.parent / target).resolve() for target in linked_targets(index)}
    unreachable = sorted(
        doc.relative_to(ROOT)
        for doc in DOCS.rglob("*.md")
        if doc != INDEX and doc.resolve() not in linked
    )
    assert not unreachable, f"not linked from docs/README.md: {unreachable}"


def test_the_corpus_gives_these_checks_something_to_check():
    """Each rule above is parameterised per document, so it passes trivially for
    a document that names no paths and runs no commands. That is fine for one
    document and meaningless for all of them."""
    named = sum(len(QUOTED_PATH.findall(doc.read_text())) for doc in documents())
    promised = sum(
        len(RUN_COMMAND.findall(block))
        for doc in documents()
        for block in FENCED_SHELL.findall(doc.read_text())
    )
    assert named, "no document names a repo path; the path rule proves nothing"
    assert promised, "no document runs a command; the command rule proves nothing"
