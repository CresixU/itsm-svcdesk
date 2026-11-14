---
lab5_triage:
  image: ghcr.io/TODO-owner/TODO-repo@sha256:TODO           # the digest the image job printed on main, lower case (P-10)
  sarif_receipt: 0                                         # the issue number of the sarif receipt whose files are in bakeoff/sarif/ (P-10)
---
<!-- ai-generated: ??% - TODO one line on how -->
# Triage

What the gates and the reporting scanners found on my service, and what I did about each (CI-SPEC.md P-11, P-12).
One row per rule of one tool; a row may cover several locations, and the Reason says which. Tool is the tool id of
P-15 (`trivy`, `grype`, `osv-scanner`, `gitleaks`, `semgrep`). Decision is one of `fix`, `ignore`,
`false-positive`, `accept`.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| trivy | CVE-TODO | fix | TODO: which package, which version fixed it, where you changed it (Dockerfile, pin) |
| trivy | CVE-TODO | ignore | TODO: the same reason as above the entry in .trivyignore, and until when |
| semgrep | TODO.rule.id | false-positive | TODO: why the rule is wrong about this code, with the file and line |

## Bake-off

TODO (at least 600 characters, P-13): your matrix in a sentence per tool; which detector you would put in a gate,
and why, with the numbers; which cells surprised you; what the defects none of the five found have in common; and
why every recall here is an upper bound (seeded defects flatter every detector).
