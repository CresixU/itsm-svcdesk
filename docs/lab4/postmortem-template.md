---
lab4_postmortem:
  ticket: "TODO"                  # the `id` in incident/ticket.json, in quotes
  detecting_alert: TODO           # the alertname `itsmlab incident 4` prints
  onset: TODO                     # the four instants in UTC, as `itsmlab incident 4` prints them: 2026-10-24T10:41:05Z
  detection: TODO
  acknowledgement: TODO
  recovery: TODO
  mttd_seconds: TODO              # detection - onset, in whole seconds
  mtta_seconds: TODO              # acknowledgement - detection
  mttr_seconds: TODO              # recovery - onset
  identified_flags: [TODO]        # the flag keys you identified, from the pool of INCIDENT-SPEC.md section 2.2
---
<!-- ai-generated: ??% - TODO replace ?? with a number and say in one line how this file was written -->

# Postmortem: TODO a title that names what the shop's users saw

Copy this file to `postmortem.md` at your repository root and replace every `TODO`. The rules are I-14 and I-18 to
I-22 in INCIDENT-SPEC.md (section 4.5); the checks are L4-CORE-3.09 and L4-CORE-4.01 to 4.06:

- the front matter: every field; `ticket` equal to the `id` in `incident/ticket.json`; the four instants and the three
  durations within 30 s of what `itsmlab incident 4` prints, and `detecting_alert` the name it prints, so copy them
  from its output; `identified_flags` names only flags of the injector's pool;
- the thirteen `##` headings below, in this order and spelt exactly so, each followed by at least 20 characters of
  its own text. That includes `Date`, `Authors` and `Status`: write a sentence, not `2026-10-24`;
- `## Lessons Learned` with its three `###` headings;
- the Action Items table with these four columns, at least two rows, and every Type one of `mitigate`, `prevent`,
  `process`, `other`. Give every row a Bug id, a ticket id such as `ITSM-42` (not `none`): Labs 6 and 8 refer to an
  action item by its Bug id, and without one they need the row's Action Item text, quoted exactly;
- the Timeline with the four instants of the front matter in UTC, as `HH:MM:SS` or in full;
- `## Problem record` at the end: each label at the start of its own line, its text on the same line.

What goes under each heading - the SRE book's Appendix D, the example Lecture 4 slide 17 showed (delete this list
when you write the file):

| heading | what to write |
|---|---|
| Date | the date of the incident, and when this postmortem was written |
| Authors | who wrote it, and in which role (you were the on-call) |
| Status | where it stands: the SRE book's example says "Complete, action items in progress" |
| Summary | one or two sentences: what broke for the shop's users, and for how long |
| Impact | the effect on users: which requests failed or slowed, how many, for how long - each number with the query that measured it |
| Root Causes | what was already wrong: each fault you identified, and what it did to which service |
| Trigger | what set it off, and when (the onset) |
| Resolution | what restored service: which flags you switched off, when, in which order, and why in that order |
| Detection | how the incident was noticed: which alert, on which symptom, after how long (MTTD), and who would have noticed without it |
| Action Items | the table: what should change so that this incident is detected sooner, lasts less, or cannot recur; Bug is the row's ticket id (`ITSM-42`) |
| Lessons Learned | three `###` headings; "Where we got lucky" is for near misses |
| Timeline | UTC, from the last quiet minute before the onset to the recovery: the four instants, what you saw, what you did, and every AI hypothesis you acted on, with its ledger id and its query - no query, no timeline (Lecture 4 slide 26) |
| Supporting information | what supports the other twelve: the queries, the dashboards, the page, the ledger, `itsmlab incident 4`'s output |
| Problem record | the problem, kept apart from the incident (Lecture 4 slide 16): the four labels below |

Blameless (Lecture 4 slide 18): name what happened and what each person knew at the time, never who is to blame.

## Date

TODO

## Authors

TODO

## Status

TODO

## Summary

TODO

## Impact

TODO

## Root Causes

TODO

## Trigger

TODO

## Resolution

TODO

## Detection

TODO

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |

## Lessons Learned

### What went well

TODO

### What went wrong

TODO

### Where we got lucky

TODO

## Timeline

TODO

## Supporting information

TODO

## Problem record

- Incident record: TODO
- Root cause: TODO
- Known error: TODO
- Workaround: TODO
