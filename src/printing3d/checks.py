"""Reporting for pre-print verification.

Checks print what they measured, not just whether they passed, so a near-miss
is visible before it becomes a failure. Nothing here knows what is being
checked.
"""


class CheckRunner:
    """Runs named checks, prints each result, and remembers the failures."""

    def __init__(self):
        self.failures = []

    def section(self, title):
        print(f"\n{title}")

    def check(self, name, passed, detail=""):
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {name}{'  -- ' + detail if detail else ''}")
        if not passed:
            self.failures.append(name)

    @property
    def all_passed(self):
        return not self.failures

    def report(self):
        """Print the verdict and return whether everything passed."""
        print(
            "\nALL CHECKS PASSED" if self.all_passed else f"\nFAILURES: {self.failures}"
        )
        return self.all_passed
