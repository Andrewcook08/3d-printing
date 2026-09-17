"""Reporting for pre-print verification.

Checks print what they measured, not just whether they passed, so a near-miss
is visible before it becomes a failure. Nothing here knows what is being
checked.
"""


class CheckRunner:
    """Runs named checks, prints each result, and remembers the failures."""

    def __init__(self):
        self.failures = []
        self.checked = 0

    def section(self, title):
        print(f"\n{title}")

    def check(self, name, passed, detail=""):
        self.checked += 1
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {name}{'  -- ' + detail if detail else ''}")
        if not passed:
            self.failures.append(name)

    @property
    def all_passed(self):
        return not self.failures

    def report(self):
        """Print the verdict and return whether everything passed.

        A run that examined nothing says so rather than claiming success. It is
        vacuously true that every check passed when none of them ran, and
        printing that is how an empty record comes to read as a guarantee.
        """
        if not self.checked:
            print("\nNOTHING CHECKED")
        elif self.all_passed:
            print("\nALL CHECKS PASSED")
        else:
            print(f"\nFAILURES: {self.failures}")
        return self.all_passed
