"""The helpers the other suites share."""

from tests.support import guarding_main


def test_a_working_copy_is_not_guarding_main(monkeypatch):
    """Nothing local sets the marker, so nothing local carries the rule."""
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    assert not guarding_main()


def test_a_pull_request_onto_main_is_guarding_it(monkeypatch):
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert guarding_main()


def test_a_pull_request_onto_another_branch_is_not(monkeypatch):
    """Only what reaches the default branch has to satisfy the whole contract."""
    monkeypatch.setenv("GITHUB_BASE_REF", "some-long-lived-branch")
    assert not guarding_main()


def test_the_scheduled_upgrade_check_is_not_guarding_main(monkeypatch):
    """The case that makes the generic automation marker the wrong one to read.

    The upgrade check runs this same suite on a schedule, so it sets every
    marker that says "this is automation" while guarding nothing. Reading one
    of those would fail it for a project that is merely mid-design, and report
    that as though a dependency had broken -- which is the one thing a run
    about dependencies must not do.
    """
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    assert not guarding_main()
