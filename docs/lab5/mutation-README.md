<!-- ai-generated: 0% - written by the course team -->
# Lab 5, Stretch 1 - mutation testing of `slaclock.py`

Coverage tells you which lines your tests ran, not whether they would notice a wrong line. Mutation testing asks the
second question: change the code by one small edit (a *mutant*), run the tests, and see whether they fail. A test
suite that still passes on a mutant did not notice the bug; a suite that fails *kills* it. In this Stretch option you
write tests for a small module of the course's, and the grader runs them against 40 mutants you have not seen.

## The module

[`slaclock.py`](slaclock.py) is the SLA arithmetic of a service desk, in pure functions (no I/O, no clock, no
randomness), on the concepts your `svcdesk` already has:

| function | what it returns |
|---|---|
| `priority_of(impact, urgency, vip=False)` | `"P1"` to `"P4"` from the impact and urgency matrix, with the VIP rule |
| `targets(priority)` | the (response, resolution) targets of a priority, in minutes |
| `sla_state(elapsed, target)` | `"ok"`, `"warning"` (from 75 % of the target) or `"breached"` (past 100 %) |
| `is_business_time(moment)` | whether a moment is inside Monday to Friday, 08:00 to 16:00 |
| `add_business_minutes(start, minutes)` | the due date of a clock that pauses outside business hours |
| `business_minutes_between(start, end)` | how many business minutes lie between two moments |
| `escalation_tier(priority, breached, reopens)` | who owns the ticket now, 0 to 3 |
| `parse_duration(text)` | the minutes in `"90m"`, `"1h30m"`, `"2d"` and the like |

**The docstrings are the specification.** Every boundary your tests need is written in them: which values are
accepted and which raise `ValueError`, which side of each threshold is inclusive, what happens at 16:00 exactly.
The module follows the rules of Lab 1 where they overlap - as in `svcdesk`, equality is not a breach, so a clock at
exactly 100 % of its target is still in `"warning"` - but it is not `svcdesk`: test what the docstrings say, not
what you remember.

## Your files

In your repository:

```
mutation/slaclock.py        the course module, copied verbatim - do not edit it
mutation/test_*.py          your tests (one file or several, at most 20)
mutation/conftest.py        optional: fixtures and helpers shared by your tests
```

Import the module the plain way, `import slaclock` or `from slaclock import priority_of`. Your test files carry the
AI-disclosure header like any file you write (the course [README](../../README.md)).

## The rules (P-29)

1. **The grader uses its own copy of the module.** It copies your `mutation/test_*.py` and `mutation/conftest.py`,
   and nothing else, into a directory next to its own `slaclock.py` and a `pytest.ini` that contains only
   `[pytest]`. A helper module or a data file beside your tests is not there when they run: put helpers in
   `conftest.py`. Each file must be a regular file (not a symbolic link) of at most 256 KB.
2. **pytest and the standard library only.** The grader runs `python -m pytest -p no:cacheprovider -q -x` with
   Python 3.13 and pytest 9.1.1, with no other package installed, no network, and the test directory read-only
   (use pytest's `tmp_path` if a test needs to write a file).
3. **Time limits.** Each run is your whole suite against one version of the module. On the module and on each
   rewrite it must finish within 60 s. On a mutant it gets `min(60, max(10, 5 x T))` seconds, where T is how long
   the same suite took on the module: a suite that takes 1 s on the module gets 10 s per mutant, one that takes
   8 s gets 40 s, one that takes 12 s or more gets 60 s. **A timeout is not a kill.** A suite that sleeps, or loops
   until the time runs out, kills nothing - make a test fail, never wait.
4. **Your suite must pass on the module** and on each of its **rewrites**: versions of `slaclock.py` that behave
   exactly like it but read differently - renamed variables, statements in another order, a comprehension written as
   a loop, another layout. A "test" that looks at the module's text instead of its behaviour (a hash of the file,
   `inspect.getsource`, the bytecode) fails on a rewrite, and a suite that fails on a rewrite does not pass, however
   many mutants it kills.
5. **A mutant is killed when your suite fails on it**: pytest exits with code 1. Any other outcome is not a kill -
   passing (the mutant survived), a timeout, and also a **collection error**: if a mutant makes your test file fail
   while it is being imported (say, `EXPECTED = slaclock.targets("P1")` at the top of the file, and the mutant
   raises there), pytest reports an error instead of a failure. Call the module inside test functions or fixtures.
6. **Pass (Tier B, check 1.02):** at least **30 of the 40** withheld mutants killed, with the suite passing on the
   module and on the 3 withheld rewrites. The mutants are single edits of the kind mutation tools make - a
   comparison operator, a constant, an arithmetic or boolean operator, a returned value, a removed condition, a
   string - and none of them is equivalent: each one changes what some documented call returns.

## Practice: `itsmlab mutants 5`

The checker ships 12 practice mutants and 2 practice rewrites, different from the graded ones. From the root of your
repository:

```
./itsmlab.sh mutants 5            # Linux, macOS
.\itsmlab.ps1 mutants 5           # Windows PowerShell
```

It runs your suite on the module, on the 2 rewrites and on each practice mutant, the same way the grader does (one
fresh directory per run, the same time limits), and prints what happened to each. When your suite fails on the module itself,
it stops there and shows pytest's output. Check 1.01 of `itsmlab verify 5` passes when your suite passes on the
module and on both rewrites and kills **at least 9 of the 12** - the same 75 % as 30 of 40.

The practice mutants show the kind of edit, not the graded ones: a suite written to kill exactly those 12 will miss
most of the 40. Aim at the boundaries in every docstring.

## Exploring with mutmut (optional)

[mutmut](https://pypi.org/project/mutmut/) 3.8.0 generates its own mutants of the module (about 230) and tells you
which ones your tests let through. It is a good way to find the boundaries you have not tested yet. It needs `fork`:
Linux or macOS, and on Windows inside WSL. Run it from inside `mutation/`, with a `setup.cfg` there that lists your
test files (every `test_*.py`, and `conftest.py` if you have one, under both keys):

```
cd mutation
cat > setup.cfg <<'EOF'
[mutmut]
source_paths=slaclock.py
also_copy=
    test_slaclock.py
pytest_add_cli_args_test_selection=test_slaclock.py
EOF
pip install mutmut==3.8.0 pytest==9.1.1       # in a virtual environment
mutmut run
mutmut results                                # the survivors
mutmut show <mutant name>                     # the edit of one survivor
```

mutmut writes its copies into `mutation/mutants/`; add that directory to `.gitignore`. Read its numbers with care:

- **Its score is not the graded number.** Its mutants are not the course's 40, and it counts a timeout as a kill;
  the grader does not.
- **Some of its survivors are equivalent**: edits no test can detect because the specification does not say, such as
  the text of an error message (the docstrings promise the exception type, not its wording) or a cap that no input
  can reach. A survivor is a question to answer - is this behaviour specified? - not always a missing test.
