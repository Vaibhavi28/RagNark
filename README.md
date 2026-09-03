<div align="center">

# RAGNark

### Security Auditing for RAG Systems

[![Status](https://img.shields.io/badge/Status-In_Development-orange?style=for-the-badge)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Vaibhavi28/RagNark?style=for-the-badge&logo=github&logoColor=white&color=yellow)](https://github.com/Vaibhavi28/RagNark/stargazers)
[![Last Commit](https://img.shields.io/github/last-commit/Vaibhavi28/RagNark?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Vaibhavi28/RagNark/commits/main)

---

### Tech Stack

![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_API-D97757?style=for-the-badge&logo=anthropic&logoColor=white)

---

**Paste a RAG endpoint → Scan for vulnerabilities → Get a plain-English report**

**No cloud. No third-party infrastructure. Runs entirely on your machine.**

> ⚠️ Actively under development. Probe library is being built. Scanner not yet functional. Follow along.

</div>

---

## What Problem Does This Solve

RAG chatbots retrieve private documents — medical records, legal files, financial reports — and feed them to an AI. Nobody is systematically testing whether those documents can leak or be manipulated.

This is not hypothetical. It has already happened:

| Incident | What Happened |
|---|---|
| **Slack AI (2024)** | Hidden instructions planted in a shared message caused the AI to leak content from private channels the attacker never had access to |
| **Microsoft 365 Copilot — EchoLeak (2025)** | A hidden instruction in one email silently exfiltrated private data — zero clicks from the victim |
| **GitHub Copilot (2025)** | A poisoned public GitHub issue caused an AI assistant to leak data from private repositories |
| **PoisonedRAG — USENIX Security 2025** | Researchers planted 5 malicious documents in a knowledge base of millions and manipulated AI responses 90–99% of the time |

Existing tools like Garak and PyRIT test general LLM behavior. Nothing tests the document retrieval layer. RAGnark fills that gap.

---

## What RAGnark Tests For

| Vulnerability | Plain English | MITRE ATLAS |
|---|---|---|
| **Data Exfiltration** | Can the system be tricked into revealing private documents? | AML.T0048 |
| **Access Control Bypass** | Can one user retrieve documents belonging to another? | AML.T0051 |
| **Prompt Injection** | Can hidden text in a query hijack the AI's behavior? | AML.T0051 |
| **Indirect Injection** | Can a poisoned document in the knowledge base hijack the AI silently? | AML.T0020 |
| **Multi-Turn Attacks** | Can the system be broken down slowly across multiple messages? | AML.T0051 |

---

## The Differentiator

Every other tool attacks the system and analyzes what comes out.

**RAGnark inspects the knowledge base itself — before any attack probe fires.**

```
Every other tool:     Attack → Analyze output
RAGnark:              Inspect knowledge base → Attack → Analyze output
```

If 5 poisoned documents can compromise a system of millions, catching those 5 documents proactively is more valuable than detecting the attack after it has already worked.

---

## Probe Library

Attack probes are sourced from peer-reviewed adversarial research — not invented.

| Source | What It Contributes |
|---|---|
| **HackAPrompt** — Schulhoff et al., EMNLP 2023 | 600K+ adversarial prompts from a global competition |
| **JailbreakBench** — Chao et al., NeurIPS 2024 | Standardized jailbreak artifact repository |
| **Garak** — Derczynski et al., 2024 | Open-source LLM vulnerability probe library |
| **MITRE ATLAS** | Adversarial AI technique taxonomy |

Probes go through an automated validation pipeline:

```
Ingest → Filter to RAG-relevant attacks → Deduplicate → Validate against real target
```

Only probes that demonstrably trigger a vulnerability make it into the library.

---

## Detection Engine

| Method | How It Works |
|---|---|
| **Keyword Detection** | Fast pattern matching against known vulnerability indicators |
| **Semantic Detection** | LLM judges whether a response actually leaked something sensitive |
| **Response Fingerprinting** | Baselines normal behavior, flags significant deviations |
| **Retrieval-Layer Analysis** | Monitors which documents were retrieved and whether that is appropriate |
| **Confidence Drift Analysis** | Runs the same probe 10x — high variance signals an unstable system |

**Ensemble rule:** A vulnerability is only flagged when 2 or more methods agree. Cuts false positives significantly.

**Confidence levels:**
```
CRITICAL  ≥95% confidence
HIGH      80–94% confidence
MEDIUM    60–79% confidence
LOW       Manual review recommended
```

---

## Report Output

```
VULNERABILITY FOUND

ID: EX-001 | Severity: Critical | Confidence: 94% | ATLAS: AML.T0048

What happened:
  [Plain English explanation specific to this system]

How an attacker exploits this:
  [Step-by-step, specific to scan results]

How to fix it:
  [Actionable recommendation]
```

---

## Current Build Status

```
Probe Library
  ✅  EX-001 → EX-080    Exfiltration (80 probes)
  ✅  AC-001 → AC-075    Access Control Bypass (75 probes)
  🔄  PI-001 → PI-180    Prompt Injection (in progress)
  ⏳  IP-001 → IP-065    Indirect Injection
  ⏳  MT-001 → MT-040    Multi-Turn Attack Chains

Core Engine
  ⏳  Probe engine
  ⏳  Detection engine
  ⏳  Adversarial document fingerprinting
  ⏳  Report generation

Frontend
  ⏳  React dashboard
  ⏳  Docker deployment
```

---

## Roadmap

| Status | Version | What Gets Built |
|---|---|---|
| 🔄 | **V1** | CLI scanner, probe pipeline, fingerprinting, Claude report, tested on DVAIA |
| ⏳ | **V2** | Full detection engine, React dashboard, Docker, SDK integration |
| ⏳ | **V3** | Claude-powered AI assistant with scan context |
| ⏳ | **V4** | Enterprise auth, scheduled scans, Slack/Jira integration, compliance templates |
| ⏳ | **V5** | Community probe portal, auto-updated library, CVE integration |

---

## Security

RAGnark audits other systems' security. It cannot itself be vulnerable to the attacks it tests for.

Every component ships with these properties from day one:

- All target responses sanitized before reaching any internal component
- SSRF protection — private IP ranges blocked at input time and request time
- DNS rebinding protection — hostname re-resolved at connection time
- No secrets in code or frontend — environment variables only
- Pinned dependencies with hash verification
- Scan results encrypted at rest, never logged in plaintext
- Generic error messages only — no stack traces, paths, or system info exposed

---

## Responsible Use

This tool is for authorized security auditing only.

Do not use RAGnark against systems you do not own or have explicit written permission to test.

See `SECURITY.md` for the responsible disclosure policy.

---

## Research

A vision paper describing the adversarial document fingerprinting technique and the probe validation methodology is in preparation for submission to arXiv and an AI security venue.

---

## Contributing

The probe library is community-extensible. See `CONTRIBUTING.md` for the probe schema and submission format.

Bug reports and feature requests welcome via [GitHub Issues](https://github.com/Vaibhavi28/RagNark/issues).

---

## License

MIT License — see `LICENSE` for details.

---

<div align="center">

**© 2026 Vaibhavi Sanjay Kathepuri**

MS Cybersecurity Analytics and Operations · Pennsylvania State University

[LinkedIn](https://linkedin.com/in/vaibhavi) · [GitHub](https://github.com/Vaibhavi28) · [GitHub Issues](https://github.com/Vaibhavi28/RagNark/issues)

⭐ **If RAGnark is useful to you, please star this repo** ⭐

*Built in public. Follow the commits.*

</div>
