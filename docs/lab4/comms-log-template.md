---
lab4_comms:
  awareness: TODO                 # NIS2: when you became aware of a significant incident (RFC 3339, in UTC)
  detection: TODO                 # KSC: "od momentu jego wykrycia" - the moment of detection
  classification: TODO            # DORA: when you classified it as a major ICT-related incident
  nis2:
    early_warning_due: TODO       # awareness + 24 h
    notification_due: TODO        # awareness + 72 h
    notification_sent: TODO       # when your incident notification would go out
    final_report_due: TODO        # one calendar month after notification_sent
  ksc:
    early_warning_due: TODO       # detection + 24 h
    notification_due: TODO        # detection + 72 h
    notification_sent: TODO       # when your notification would go out
    final_report_due: TODO        # one calendar month after notification_sent
  dora:
    initial_due: TODO             # classification + 4 h, capped at awareness + 24 h when classified within those 24 h
    initial_sent: TODO            # when your initial notification would go out
    intermediate_due: TODO        # initial_sent + 72 h
    intermediate_sent: TODO       # when your intermediate report would go out
    final_due: TODO               # one calendar month after intermediate_sent
  log:                            # at least three communications: when, to whom, what
    - {at: TODO, to: TODO, what: TODO}
    - {at: TODO, to: TODO, what: TODO}
    - {at: TODO, to: TODO, what: TODO}
---
<!-- ai-generated: ??% - TODO replace ?? with a number and say in one line how this file was written -->

# Communications log: the regulators' clocks

Stretch 2 (`L4-STRETCH-2.01`, INCIDENT-SPEC.md I-30). Copy this file to `comms-log.md` at your repository root and
replace every `TODO`. Suppose the shop is an entity that NIS2, the Polish KSC act and DORA all apply to (Lecture 4
slide 21), and that your incident was significant under the first two and major under the third.

- Write every instant in UTC with `Z`. The checker compares instants, so another offset is not wrong, but Warsaw
  leaves summer time in the night after the lab (25 October 2026, 03:00 CEST becomes 02:00 CET), and 24 hours after
  a Saturday noon in Warsaw is not Sunday noon on a Warsaw clock.
- The three instants you defend (`awareness`, `detection`, `classification`) and the four `*_sent` instants are
  your choice; the eight deadlines follow from them by the rule, and the checker recomputes each one (within one
  minute).
- Hours are elapsed hours. "One calendar month after" is the same day and time of the next month on the UTC calendar,
  or that month's last day when it is shorter: a month after 2026-10-31T09:00:00Z is 2026-11-30T09:00:00Z.
- INCIDENT-SPEC.md section 4.7 has a worked example. The weekend relief of the DORA technical standard (Art. 5(4))
  is ignored.

Delete these instructions when you write the file.

## The three instants you defend

TODO: which instant of your incident you call the awareness of a significant incident (NIS2), which the detection
(KSC), and which the classification as major (DORA), and why each is that instant - with the timestamps of your
postmortem, and what you knew at each.

## The log

TODO: the communications of the front matter in prose or as a table - who was told what, when, and which clock each
one answers.
