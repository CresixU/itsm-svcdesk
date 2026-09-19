# svcdesk - guidance for Claude Code in this repository

This repository holds `svcdesk`, the Lab 1 service-desk API. Read, in order, before changing anything:
`docs/REQUIREMENTS.md`, `docs/API.md`, `docs/CHECKS.md`, `specs/spec.md`, `DECISIONS.md`. `specs/spec.md` and
`DECISIONS.md` record which side of each of the three contradictions (C1, C2, C3) this service takes; keep the
running code and those two documents consistent - `L1-CORE-4` fails the build otherwise.

## Layout

- `src/svcdesk/` - the FastAPI implementation (`config.py` holds the C1/C2/C3 constants, `priority.py` the matrix,
  `sla.py` the business-hours clock, `storage.py` SQLite persistence, `main.py` the HTTP layer).
- `specs/` - `spec.md` (the specification, written before `src/` existed) and `converge.md` (the comparison of
  spec against implementation).
- `.claude/agents/reviewer.md` - a read-only review sub-agent; see `AGENT-POLICY.md` for what it is barred from
  doing and why.

## Commands

- `docker compose build` / `docker compose up -d` - run the service locally on port 8080.
- `.\itsmlab.ps1 verify 1` (or `./itsmlab.sh verify 1` on Linux/macOS) - run the published Tier A checker. Must
  exit 0, with every Core spec `pass` (L1-CORE-5 is `skip` locally by design).

## Rules for any agent working here

- Never change `C1`, `C2` or `C3` in `src/svcdesk/config.py` without updating the matching front matter and prose
  in `DECISIONS.md` in the same change; the two must always agree.
- Do not add a bind mount to `docker-compose.yml` and do not add a runtime network call to the image (API.md
  section 9) - both fail Core specs outright.
- Every file under `src/` and `specs/`, plus `DECISIONS.md`, needs the `ai-generated: <0-100>% - <how>` header in
  its first ten lines.
