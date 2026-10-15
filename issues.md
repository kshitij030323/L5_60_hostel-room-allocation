# Issues Found and Fixed: `hostel_allocation.py`

Tools: Pylint, Bandit, Flake8. Baseline reports are in `*_report_before.txt` and final reports are in `*_report_after.txt`. Line numbers refer to the **original** file.

## Results summary

| Tool   | Before                                  | After                     |
|--------|-----------------------------------------|---------------------------|
| Pylint | 5.84/10 (32 messages)                   | **10.00/10** (0 messages) |
| Bandit | 5 issues (1 High, 2 Medium, 2 Low)      | **0 issues**              |
| Flake8 | 20 violations                           | **0 violations** (empty report) |

## Issues reported by the tools (high and medium severity first)

| # | Issue | Type | Tool / Code | Line(s) | Description | Fix Approach |
|---|-------|------|-------------|---------|-------------|--------------|
| 1 | Flask debug mode enabled | Security (High) | Bandit B201 | 80 | `app.run(debug=True)` exposes the Werkzeug debugger, which allows arbitrary code execution from the browser. | Run with `debug=False`. |
| 2 | Unsafe YAML load | Security (Medium) | Bandit B506 | 21 | `yaml.load(..., Loader=yaml.Loader)` can instantiate arbitrary Python objects from untrusted YAML. | Use `yaml.safe_load(text)`. |
| 3 | Insecure logging config listener | Security (Medium) | Bandit B612 | 72 | `logging.config.listen(9999)` accepts any config sent to the port, and a config can contain code that gets executed. | Pass a `verify=` callback (`_verify_log_config`) that only accepts JSON dictConfig payloads. |
| 4 | Hardcoded password | Security (Low) | Bandit B106 | 66 | The warden DB password `"Hostel@123"` is in the source code and in version control. | Read it from the `WARDEN_DB_PASSWORD` environment variable. |
| 5 | Insecure random generator | Security (Low) | Bandit B311 | 56 | `random.sample` is predictable, so the room lottery could be gamed. | Use `secrets.SystemRandom().sample(...)`. |
| 6 | Mutable default argument | Bug | Pylint W0102 | 29 | `preferred=[]` is created once and shared between all calls. | Default to `None` and create a new list inside the function. |
| 7 | Unused argument `gender` | Bug | Pylint W0613 | 29 | Gender was ignored, so a female student (S4) was put in male block A. | Skip rooms whose `gender` does not match the student. |
| 8 | `type()` used for type check | Bug / Style | Pylint C0123, Flake8 E721 | 30 | `type(year) != int` rejected the string `"2"`, so S5 got neither a room nor a waitlist entry. | Convert with `int(year)` inside `try/except (TypeError, ValueError)`. |
| 9 | Unused imports | Quality | Pylint W0611, Flake8 F401 | 1–2 | `os` and `sys` were imported but never used. | Removed `sys`. `os` is now used for the environment variable. |
| 10 | Non-snake_case function names | Convention | Pylint C0103 | 20–79 | `loadConfig`, `allocateRoom`, etc. break PEP 8 naming. | Renamed to `load_config`, `allocate_room`, and so on. |
| 11 | Missing docstrings | Convention | Pylint C0114, C0116 | 1, 20–82 | No module or function docstrings. | Added docstrings throughout. |
| 12 | Iterating dict keys then indexing | Convention | Pylint C0206 | 60 | `for r in rooms: rooms[r]...` | Iterate with `.items()` / `.values()`. |
| 13 | Missing blank lines | Style | Flake8 E302, E305 | 20–101 | Top-level definitions need 2 blank lines around them. | Added 2 blank lines between definitions. |
| 14 | Lines too long | Style | Flake8 E501, Pylint C0301 | 25, 66, 95 | Lines longer than 79 (Flake8) or 100 (Pylint) characters. | Wrapped the lines and split long expressions into named variables. |

## Logic bugs found by running the program (not flagged by any tool)

| # | Issue | Type | Line(s) | Description | Fix Approach |
|---|-------|------|---------|-------------|--------------|
| 15 | Off-by-one capacity check | Bug | 34 | `len(occupants) > capacity` let A1 (capacity 2) take 3 students. | Changed to `>=`. |
| 16 | Duplicate allocation | Bug | 29–38 | Allocating S1 again gave them a second bed in A2. | Return the existing room if the student is already allocated. |
| 17 | Vacate does not free the bed | Bug | 41–45 | `vacateRoom` removed the allocation record but left the student in the room's `occupants`. | Pop the allocation and remove the student from that room's occupants. |
| 18 | Fee truncates partial months | Bug | 49 | `45 // 30 = 1`, so 45 days was charged as 1 month. | `math.ceil(days / 30)` charges each started month (45 days = 2 months). |
| 19 | Priority order is reversed | Bug | 53 | Sorted juniors first even though seniors should get priority. | `sorted(..., reverse=True)`. |
| 20 | Vacant beds undercounted | Bug | 58–63 | Only fully empty rooms were counted, so free beds in partly filled rooms were missed. | Sum `capacity - len(occupants)` over all rooms. |
| 21 | Inconsistent return / waitlist | Bug | 29–39 | Implicitly returned `None` when waitlisting, and could add the same student twice. | Explicit `return None`, and only append if not already waitlisted. |
| 22 | Reflected XSS and crash in `/room` | Security | 76–77 | `id` was put straight into HTML, and a missing `id` raised `TypeError` (`None + str`). | Default to `""` and HTML-escape the output with `markupsafe.escape`. |
| 23 | Unknown preferred room crashes | Bug | 33 | A preferred room not in `rooms` raised `KeyError`. | Use `rooms.get()` and skip unknown rooms. |
| 24 | Code runs on import | Quality | 101 | `main()` ran whenever the module was imported. | Wrapped it in `if __name__ == "__main__":`. |

## Program output: before vs after

| Check | Before | After |
|-------|--------|-------|
| S3 (A1 already has 2) | `A1` (overfull) | `A2` |
| S4 (female) | `A2` (male block) | `B1` |
| S1 again | `A2` (second bed) | `A1` (existing room) |
| S5 year `'2'` | `None`, not waitlisted | `A2` |
| A1 after S2 left | `['S1', 'S2', 'S3']` | `['S1']` |
| Fee for S1, 45 days | `4000` | `8000` |
| Priority (seniors first) | `[1, 2, 4]` | `[4, 2, 1]` |
