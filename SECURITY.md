# Security Policy

RAGnark is a security auditing tool. It must never itself become a source of
vulnerability — for the systems it scans, for the person running it, or for
anyone whose data passes through it. This document covers three things:

1. How to report a security issue found in RAGnark itself
2. What RAGnark guarantees about its own security posture
3. The rules for using RAGnark responsibly against other systems

---

## 1. Reporting a Vulnerability in RAGnark

**Do not open a public GitHub issue for security vulnerabilities.**
Public issues are for bugs and feature requests only — a public report of a
real vulnerability puts every user of the tool at risk before a fix ships.

### How to report

**GitHub Private Vulnerability Reporting**
Use the **"Report a vulnerability"** button under this repository's
**Security** tab. This opens a private security advisory visible only to
the reporter and the maintainer — no public disclosure, no email required.

### What to include

- A description of the issue, steps to reproduce, affected version/commit,
  and potential impact
- If you have a proof-of-concept, attach it privately — never post it
  inline in a public thread

### What happens next

| Stage | Timeline |
|---|---|
| Acknowledgment of report | Within 5 business days |
| Initial assessment (severity, validity) | Within 10 business days |
| Fix developed and tested | Timeline depends on severity — critical issues prioritized |
| Public disclosure | Coordinated with reporter, after a fix is available |

This is a solo, pre-launch, academic project — there is currently **no bug
bounty program**. Credit will be given in the release notes / changelog for
any valid report, unless the reporter requests anonymity.

### Scope

| In Scope | Out of Scope |
|---|---|
| RAGnark's scanner, detection engine, fingerprinting module, API, frontend | Vulnerabilities in third-party test targets (DVAIA, DVAIB, etc.) |
| Dependency vulnerabilities introduced by RAGnark's own configuration | Vulnerabilities in Claude API, Ollama, or other upstream services themselves |
| Data handling issues (scan results, credentials, logs) | Social engineering, physical access attacks |

---

## 2. Security Guarantees — What RAGnark Commits To

RAGnark audits other people's systems for security flaws. If RAGnark itself
were insecure, it would be actively dangerous — a tool that leaks the very
credentials and data it was given to test with. Every property below is a
requirement, not an aspiration, from the first version onward.

### Input & target handling

- All responses received from a scanned target are treated as **untrusted
  input** and sanitized before reaching any internal component (parser,
  detection engine, report generator, or LLM prompt context)
- A malicious or compromised target cannot use its response to inject
  commands, corrupt RAGnark's own state, or pivot into RAGnark's
  infrastructure

### Network safety (SSRF / DNS protection)

- Private and reserved IP ranges (RFC 1918, loopback, link-local, cloud
  metadata endpoints like `169.254.169.254`) are blocked at scan-input time
  **and** re-validated at actual connection time
- Hostnames are re-resolved immediately before each request (DNS rebinding
  protection) — a hostname cannot resolve to a public IP at validation and
  a private IP at request time
- Redirects during a scan are validated against the same rules before being
  followed — no using a redirect to bypass SSRF checks

### Secrets & credentials

- No API keys, tokens, or credentials are ever hardcoded in source or
  shipped in the frontend bundle
- All secrets are loaded from environment variables / a secrets manager at
  runtime only
- Auth tokens or headers supplied by a user for scanning their own target
  are never logged, and never persisted outside the encrypted scan-results
  store

### Data at rest

- Scan results (which may contain excerpts of a target's private/sensitive
  documents, uncovered during testing) are encrypted at rest
- Scan results and logs never contain plaintext copies of leaked sensitive
  data — only what's needed to demonstrate and describe the finding

### Dependency & supply chain

- All dependencies are pinned to exact versions with hash verification
  (`pip` hash-checking mode / lockfiles) — no floating version ranges
- Dependency updates go through a manual review before being merged, not
  auto-merged

### Error handling & information disclosure

- User-facing error messages are generic ("Scan failed — see logs" style)
- Stack traces, internal file paths, environment details, and library
  versions are never exposed in API responses or the UI

### Web application hardening

- CSRF protection on all state-changing endpoints
- Rate limiting on the scan-trigger endpoint and the AI assistant endpoint,
  per session/user
- Security headers enforced on all responses: `Content-Security-Policy`,
  `X-Frame-Options`, `X-Content-Type-Options`

### AI assistant safety

- The Claude-powered assistant only has access to the current session's
  scan context — no cross-session or cross-user data access
- Assistant inputs/outputs go through the same sanitization rules as any
  other untrusted boundary

---

## 3. Responsible Use Policy

RAGnark is an **offensive security tool**. It actively attempts prompt
injection, data exfiltration, and access-control bypass against a target
RAG system. Used against a system without authorization, this is not
"testing" — it may be unauthorized computer access, and in many
jurisdictions that carries legal consequences for the person running the
scan, not just the tool's author.

### Rules

- **Only scan systems you own, or have explicit written authorization to
  test.** Verbal permission is not sufficient for anything beyond a
  personal lab environment.
- **Never scan production systems handling real user data** unless you are
  specifically authorized to do so as part of a sanctioned security
  engagement (e.g., a signed pentest agreement).
- **Treat all scan findings as sensitive.** A successful scan may surface
  real private data belonging to real people. Handle, store, and share
  results accordingly — do not paste raw findings into public channels,
  tickets, or chat.
- **Report responsibly.** If you use RAGnark against a client's or
  employer's system and find a critical vulnerability, follow standard
  responsible disclosure norms with that organization before any public
  discussion.

### What the author is not responsible for

The author provides RAGnark as-is for legitimate, authorized security
research and auditing. The author is not responsible for misuse of this
tool against systems the user does not have authorization to test. See
`LICENSE.md` for the full no-warranty terms.

---

## Versioning of This Policy

RAGnark is pre-launch and under active development. This policy will be
revisited and expanded as the tool matures — particularly the disclosure
timeline and scope table, once there are real users and a release cadence
to commit to. Check the commit history of this file for changes.
