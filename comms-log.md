---
lab4_comms:
  awareness: 2026-10-12T05:06:56Z
  detection: 2026-10-12T05:06:19Z
  classification: 2026-10-12T05:30:00Z
  nis2:
    early_warning_due: 2026-10-13T05:06:56Z
    notification_due: 2026-10-15T05:06:56Z
    notification_sent: 2026-10-13T08:00:00Z
    final_report_due: 2026-11-13T08:00:00Z
  ksc:
    early_warning_due: 2026-10-13T05:06:19Z
    notification_due: 2026-10-15T05:06:19Z
    notification_sent: 2026-10-13T08:00:00Z
    final_report_due: 2026-11-13T08:00:00Z
  dora:
    initial_due: 2026-10-12T09:30:00Z
    initial_sent: 2026-10-12T09:00:00Z
    intermediate_due: 2026-10-15T09:00:00Z
    intermediate_sent: 2026-10-15T08:00:00Z
    final_due: 2026-11-15T08:00:00Z
  log:
    - {at: 2026-10-12T09:00:00Z, to: the financial supervisor, what: DORA initial notification of a major ICT-related incident}
    - {at: 2026-10-12T12:00:00Z, to: the CSIRT, what: NIS2 and KSC early warning}
    - {at: 2026-10-13T08:00:00Z, to: the CSIRT, what: NIS2 and KSC incident notification}
    - {at: 2026-10-15T08:00:00Z, to: the financial supervisor, what: DORA intermediate report}
---
<!-- ai-generated: 85% - Claude Code computed the deadlines from INCIDENT-SPEC.md I-30 and drafted the argument for the three instants; the author reviews it -->

# Communications log: the regulators' clocks

This is the exercise of Stretch 2, not a statement about the real incident. Suppose the shop is an entity to which NIS2, the Polish KSC act and DORA all apply, and that the incident of `lab4-rec-1` (postmortem.md) was significant under the first two and major under the third. In truth it was not either: about one order in 79 was slow, no order was refused and no data was lost, so a real entity would probably have sent nothing. The log shows which clocks would have run, and which of them is the strictest.

## The three instants you defend

All three come from the instants of the postmortem, in UTC on 2026-10-12.

- **Detection (KSC), 05:06:19Z.** The KSC act counts from the moment of detection of the incident, and what detected it was the alert `ShopCheckoutSlow` starting to fire, a machine: no person knew yet. It is the earliest instant of the three, so the KSC clock is the strictest of the two cybersecurity clocks.
- **Awareness (NIS2), 05:06:56Z.** NIS2 counts from the moment the entity becomes aware of a significant incident. The first person who knew was the on-call who acknowledged the P1 ticket, 37 seconds after the detection (MTTA), and by then the page already said that checkout, the shop's revenue path, was slow. Choosing a later instant ("when the investigation had confirmed it was significant") would let the entity move its own clock, which is what the word "aware" is meant to prevent, so I take the acknowledgement. The 37 seconds between detection and awareness is exactly the difference between the KSC and NIS2 deadlines below.
- **Classification as major (DORA), 05:30:00Z.** DORA counts the initial notification from the classification, and the classification needs the impact measured: which clients, how many orders, for how long. By 05:30 the incident was over (the flags were off at 05:10:10Z) and the twelve-minute window to 05:13 had been measured (about 79 orders, one of them slow), so the classification is the first moment at which the criteria could have been applied. It is within 24 hours of the awareness, so the initial notification is due four hours after it, at 09:30:00Z; the other bound, 24 hours after the awareness, is 05:06:56Z the next day and is later.

The deadlines follow from the rules: NIS2 early warning 24 h and notification 72 h after awareness; KSC the same after detection; DORA initial 4 h after classification and intermediate 72 h after the initial notification; each final report one calendar month after the report before it, on the UTC calendar. Warsaw leaves summer time on 2026-10-25, after the incident, so every instant here is in UTC and none of the arithmetic crosses the change.

## The log

| at (UTC) | to | what | which clock it answers |
|---|---|---|---|
| 2026-10-12T09:00:00Z | the financial supervisor | DORA initial notification | `dora.initial_due` 09:30:00Z, 30 minutes of margin |
| 2026-10-12T12:00:00Z | the CSIRT | NIS2 and KSC early warning | `ksc.early_warning_due` 2026-10-13T05:06:19Z, the earlier of the two |
| 2026-10-13T08:00:00Z | the CSIRT | NIS2 and KSC incident notification | `nis2.notification_due` 2026-10-15T05:06:56Z and `ksc.notification_due` 05:06:19Z, two days of margin; the final reports are due one month later, 2026-11-13T08:00:00Z |
| 2026-10-15T08:00:00Z | the financial supervisor | DORA intermediate report | `dora.intermediate_due` 2026-10-15T09:00:00Z, which is 72 hours after the initial notification; the final DORA report is due 2026-11-15T08:00:00Z, a month after this one |

The strictest clock is DORA's: four hours after classification, the only deadline of the day of the incident, and the first one in the table. The two cybersecurity warnings are due the next morning, 05:06:19Z for KSC and 05:06:56Z for NIS2, and a single early warning sent to the CSIRT before 05:06:19Z satisfies both.
