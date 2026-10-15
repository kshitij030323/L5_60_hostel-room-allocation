# Reflection: Lab 5 Static Code Analysis

### 1. Which issues were the easiest to fix, and which were the hardest? Why?

**Easiest:** Flake8 formatting (E302 blank lines, E501 long lines), unused imports, missing docstrings and the snake_case renames. Each is mechanical, the tool gives the exact line, and the fix cannot change behaviour. Most Bandit findings were also quick one-line swaps once I knew the safe alternative: `yaml.safe_load`, `debug=False`, `secrets.SystemRandom`.

**Hardest:** the issues that needed me to understand what the code was *meant* to do.
- **W0613 unused argument `gender`** looked like a warning about an unused parameter, but it was really a bug: students were being placed in the wrong gender's block. Deleting the argument would have silenced Pylint and hidden the bug.
- **B612 `logging.config.listen`** has no one-line fix. I had to read how the `verify` callback works and decide what payloads to trust (JSON dictConfig only).
- The **logic bugs** that no tool reported (off-by-one capacity, `vacateRoom` not freeing the bed, reversed priority, fee truncation, vacant-bed undercount) only showed up by running the program and checking whether the output made sense.

### 2. Did the static analysis tools report any false positives? If so, describe one example.

Yes, or at least findings whose severity depends on context:
- **B106 hardcoded password**: `sqlite_connect` is a stub that never connects to a real database, so the hardcoded password was not actually exploitable. Moving it to an environment variable is still the right habit, because real credentials should never be committed.
- **B311 `random`**: Bandit flags every use of `random` as a crypto weakness. For a casual shuffle this would be a false positive, but a hostel room lottery is something students have a reason to game, so switching to `secrets.SystemRandom` was justified.
- **B612**: Bandit still reports `logging.config.listen` unless a `verify` callback is passed, even though the function is never called in `main()`. Bandit cannot know whether code is reachable.

The overlapping reports (Pylint C0123 vs Flake8 E721, Pylint W0611 vs Flake8 F401) were duplicates rather than false positives.

### 3. How would you integrate static analysis tools into your actual software development workflow?

- **Locally:** run Flake8 and Pylint in the editor so issues appear while typing, and add a **pre-commit hook** (`pre-commit` with flake8, pylint and bandit) so style and security problems are caught before a commit is made.
- **In CI:** run all three on every pull request (for example in a GitHub Actions job) and fail the build if Bandit finds Medium/High issues, Flake8 reports any violation, or the Pylint score drops below a threshold such as 9.5.
- **Configuration:** keep shared settings in `pyproject.toml`, `.pylintrc` or `setup.cfg` (line length, disabled checks) so everyone gets the same results. Use targeted `# nosec` / `# pylint: disable=` comments, with a justification, for real false positives instead of turning checks off globally.
- **Alongside tests:** static analysis did not catch the logic bugs in this lab, so it should run together with unit tests, not replace them.

### 4. What tangible improvements did you observe in the code quality, readability, or potential robustness after applying the fixes?

- **Security:** Bandit went from 5 issues (1 High, 2 Medium, 2 Low) to 0. The app no longer exposes the Werkzeug debugger, cannot be given malicious YAML, does not commit a password, uses an unpredictable lottery, and escapes user input on `/room` (which also fixed a `TypeError` crash when `id` was missing).
- **Quality and readability:** the Pylint score rose from **5.84 to 10.00**, and Flake8 went from 20 violations to 0. Consistent snake_case names, docstrings on every function and PEP 8 layout make the file easier to read and review.
- **Correctness:** fixing the mutable default argument, the unused `gender` argument and the `type()` check, plus the logic bugs found by running the program, means the output is now correct. Rooms are no longer overfilled, genders go to the right block, students cannot be allocated twice, vacating frees the bed, fees charge every started month, and seniors get priority.
- **Maintainability:** `main()` is behind an `if __name__ == "__main__"` guard, so the module can be imported and unit-tested without side effects.
