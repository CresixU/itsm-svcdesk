# Agent policy - the reviewer sub-agent's denylist

`.claude/agents/reviewer.md` declares `disallowedTools`, a narrow denylist rather than an allowlist: the reviewer
keeps every tool it needs to read and reason about the repository, and is barred only from the specific actions
whose blast radius exceeds a reviewer's job. Each entry below is a decision about that blast radius, not a general
safety rule.

- Bash(rm *): the reviewer reads and comments on code; deleting a file is an authorial decision that belongs to
  whoever is making the change, never to something running alongside it as a check.
- Bash(git push *): a review must never be able to publish anything on its own. Only a human, or the primary
  session that requested the review, decides when a change is ready to leave the local repository.
- Bash(docker *): the reviewer inspects source, tests and configuration; starting, stopping or rebuilding
  containers changes state that other work in the same repository may depend on mid-review.
- WebFetch: a reviewer's job is bounded to this repository's own requirement documents and diffs. Letting it fetch
  arbitrary external pages both widens its blast radius past that scope and exposes it to content that was never
  vetted for this project, including prompt injection aimed at the agent itself.
