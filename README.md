# envdiff 🔍

**Diff, sort, and validate `.env` files.** Zero dependencies, pure Python stdlib.

> Part of the **Trust & Reliability Layer for Agentic AI** — provenance, economics, truth, and interop tools for people building on agentic models.

## Why it exists
Environment files drift across environments, branches, and team members. envdiff gives you a fast, audit-friendly way to compare, sort, and validate them — no Docker, no node_modules, just Python.

## One tool, many domains
| Domain | What envdiff does |
|---|---|
| **DevOps** | Compare staging vs production `.env` files before deploy |
| **Security Audits** | Validate `.env` files for duplicate keys, syntax issues |
| **CI/CD** | Gate deploys when env files differ from expected baselines |
| **Agentic AI** | Diff agent config environments; validate prompt templates |

## Install
```bash
git clone git@github.com:realMNohgee/envdiff.git
cd envdiff
python3 envdiff.py --help
```

## Quick start
```bash
python3 envdiff.py compare .env .env.example
python3 envdiff.py sort .env
python3 envdiff.py validate .env
python3 envdiff.py compare .env .env.example --format json
```

## License
MIT — see [LICENSE](LICENSE).

---
🧰 **[Tool on Hermtica Marketplace](https://hermtica.com/marketplace)**
