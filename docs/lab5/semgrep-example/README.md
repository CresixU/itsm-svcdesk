<!-- ai-generated: 0% - written by the course team -->
# Stretch 3 - a Semgrep rule and its tests, on a toy

`semgrep/rules.yml` holds rules; `semgrep/rules.py`, next to it, is their test file: Semgrep pairs a test file with
the config of the same name. A comment `# ruleid: <id>` says "the next line must be reported by rule `<id>`", and
`# ok: <id>` says "the next line must not be". This example has one rule on a toy function; P-31 asks for two rules
of your own, for your own code:

    cp -r semgrep-example/semgrep <your repository>/          # then replace the toy with your rules
    docker run --rm --network none -v "$PWD:$PWD" -w "$PWD" semgrep/semgrep:1.178.0 semgrep --test semgrep/
    docker run --rm --network none -v "$PWD:$PWD" -w "$PWD" semgrep/semgrep:1.178.0 \
        semgrep scan --config semgrep/rules.yml --metrics=off src/

(Windows PowerShell: `${PWD}` in place of `$PWD`, and a backtick instead of `\` to continue a line.) The first command
must end with `All tests passed` (exit 0); the second must report each of your rules at least once in `src/` -
Semgrep names them `semgrep.<id>` there. `./itsmlab.sh verify 5` runs both.

What makes a rule worth writing: it encodes a decision about **your** service that a generic ruleset cannot know - a
function that must never be called from a request handler, a table that must only be written through one helper,
a header every endpoint must set. Its `ok:` cases are the ones a careless rule would also report. A rule that fires on
your code is either a finding (fix it, or triage it in `TRIAGE.md`) or a guard that records a pattern you rely on;
either way, the tests prove where it fires and where it must not.
