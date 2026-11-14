---
lab5_triage:
  image: ghcr.io/cresixu/itsm-svcdesk@sha256:6f7cb123ee7b10a510818d32f3e59efed571b7114e5ef99585ef2b416a56102a
  sarif_receipt: 422
---
<!-- ai-generated: 80% - Claude Code drafted the rows and the bake-off reading from the receipted SARIF and my matrix; I ran the fixes and checked every number against bakeoff.json -->
# Triage

What the gates and the reporting scanners found on my service, and what I did about each (CI-SPEC.md P-11, P-12).
One row per rule of one tool; a row may cover several locations, and the Reason says which. Findings inside
`lab5-canary/` are the seeded set and belong to the bake-off, not to this table.

Before the first push, my local scan of the image with the pipeline's own Trivy found 10 fixable HIGH vulnerabilities (zlib1g twice, starlette three times,
urllib3 twice, msgpack twice, setuptools once). All were fixed in the Dockerfile and requirements.txt, so `.trivyignore`
and `.gitleaksignore` hold no entries and no CVE is ignored.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| trivy | CVE-2025-71176 | fix | pytest 8.3.4 in requirements.txt line 4 (MEDIUM, so it did not trip the gate); pinned to 9.0.3, the fixed release, in the commit after the canary; the image and deps gates stayed green |
| grype | GHSA-6w46-j5rx-g56g-pytest | fix | the same pytest 8.3.4 finding under Grype's id for requirements.txt line 1; fixed by the pytest 9.0.3 pin |
| osv-scanner | CVE-2025-71176 | fix | the same pytest 8.3.4 finding (reported twice by OSV-Scanner for requirements.txt); fixed by the pytest 9.0.3 pin |
| semgrep | dockerfile.security.missing-user.missing-user | fix | Dockerfile line 31: the container ran as root; added a system user svcdesk (uid 10001) that owns /data and a USER line; tests, /health and writes to the named volume checked afterwards |
| semgrep | python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected | false-positive | docs/lab4/agent/prom_mcp.py line 34, the course's Lab 4 read-only Prometheus client, not part of the service; the URL comes from the operator's environment, never from a request, and the file is kept as published |
| semgrep | python.lang.security.audit.formatted-sql-query.formatted-sql-query | false-positive | semgrep/rules.py line 28: a deliberately bad example in the test file of my own Semgrep rules (the line must be reported); never imported or run; the service code in src/ has no formatted SQL |
| semgrep | python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query | false-positive | semgrep/rules.py lines 28 and 33: the same deliberately bad examples; the code uses sqlite3 with ? placeholders, and storage.list_tickets builds its query from constant fragments only |

## Bake-off

My canary set has 10 defects (5 in code, 3 credentials, 2 vulnerable pins). Semgrep found 4 with 1 false positive
(precision 0.80, recall 0.40, F1 0.53); gitleaks 1 with none (1.00, 0.10, 0.18); Trivy, Grype and OSV-Scanner each found
the same 2, the two pins, with none (1.00, 0.20, 0.33). Together the five found 7 of 10, so 3 defects were missed by
every one of them: the `random` module used for a reset token (CWE-338), and two credentials, a passphrase-like
secret in jwt_secret.py and an SMTP password in mailer.py. I did not test why gitleaks missed those two; my guess is
that they match no known key format and its generic rule needs a longer, more random value, which I have not checked.
The one false positive of Semgrep is the SHA-1 ETag of etag.py, a content fingerprint and not a security control; a
weak hash call looks the same whether it protects a password (the real defect in agent_accounts.py) or labels a
cache entry, so only the key tells them apart. I would
keep the gates as the pipeline has them: Trivy on dependencies, because it has no false positives here, applies the
HIGH/CRITICAL and has-a-fix filters and one of the three dependency scanners is enough, as they are identical on this
set; and gitleaks for secrets, since a single false alarm on a secret gate costs little while a missed credential costs
a lot. I would not gate on Semgrep: it has the best recall and the only false positive, so as a blocker it would train
people to ignore it, but as a report on the pull request it adds 4 defects nobody else sees. Every recall here is an
upper bound: the defects are seeded and flatter every detector, 10 defects make one defect worth 0.10 of recall and
one false positive worth 0.2 of precision, and there is no count of what the tools rightly left alone.
