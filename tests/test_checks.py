"""The shared pass/fail runner."""

from printing3d.checks import CheckRunner


def test_a_new_runner_has_passed_nothing_and_failed_nothing():
    assert CheckRunner().all_passed


def test_a_passing_check_is_reported_with_its_measurement(capsys):
    runner = CheckRunner()
    runner.check("the gap is wide enough", True, "0.90 mm")
    out = capsys.readouterr().out
    assert "[PASS]" in out
    assert "the gap is wide enough" in out
    assert "0.90 mm" in out


def test_a_failing_check_is_remembered_by_name(capsys):
    runner = CheckRunner()
    runner.check("the gap is wide enough", False)
    assert "[FAIL]" in capsys.readouterr().out
    assert runner.failures == ["the gap is wide enough"]
    assert not runner.all_passed


def test_one_failure_among_many_still_fails():
    runner = CheckRunner()
    runner.check("first", True)
    runner.check("second", False)
    runner.check("third", True)
    assert not runner.all_passed


def test_the_report_announces_success(capsys):
    """Also guards the empty-run test below from passing by breaking this."""
    runner = CheckRunner()
    runner.check("fine", True)
    assert runner.report()
    assert "ALL CHECKS PASSED" in capsys.readouterr().out


def test_the_report_names_what_failed(capsys):
    runner = CheckRunner()
    runner.check("broken", False)
    assert not runner.report()
    assert "broken" in capsys.readouterr().out


def test_a_section_heading_is_printed(capsys):
    CheckRunner().section("cross-part alignment")
    assert "cross-part alignment" in capsys.readouterr().out


def test_a_run_that_examined_nothing_does_not_claim_success(capsys):
    """It is vacuously true that every check passed when none of them ran, and
    printing that is how an empty record comes to read as a guarantee.

    This is not hypothetical: re-locking a project that declares no parts wrote
    a record whose entire content was the words announcing success.
    """
    runner = CheckRunner()
    runner.report()
    printed = capsys.readouterr().out
    assert "NOTHING CHECKED" in printed
    assert "ALL CHECKS PASSED" not in printed
