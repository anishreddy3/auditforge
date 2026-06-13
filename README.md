# 🏛️ AuditForge — Multi-Agent Compliance Auditor with Verifiable Agent Identity

> **Cryptographic, not contractual, trust.**

AuditForge is a multi-agent compliance auditing system where every AI agent action is cryptographically signed and verifiable. Built for the [Agent Forge Hackathon](https://www.theaibuilders.dev/) in Singapore.

## The Problem

Enterprises deploying AI agents for finance, legal, and procurement workflows **cannot prove which agent took which action**. Regulators are starting to demand cryptographic proof of AI decision chains. Current solutions rely on contractual trust — AuditForge provides **cryptographic trust** via TEE-signed audit trails.

## How It Works

```
┌────────────────────────────────────────────────┐
│           LangGraph Orchestrator               │
├──────────────┬──────────────┬──────────────────┤
│ Data         │ Risk         │ Report           │
│ Collector    │ Scorer       │ Writer           │
│ Agent        │ Agent        │ Agent            │
├──────────────┼──────────────┼──────────────────┤
│ Bright Data  │ Daytona      │ Kimi K2.6        │
│ (scraping)   │ (sandbox)    │ (long-context)   │
├──────────────┴──────────────┴──────────────────┤
│     Terminal 3 — TEE Identity & Signing        │
├────────────────────────────────────────────────┤
│         TokenRouter — Model Routing            │
└────────────────────────────────────────────────┘
```

1. **Data Collector** scrapes live company filings and news via Bright Data
2. **Risk Scorer** computes risk scores inside an isolated Daytona sandbox
3. **Report Writer** generates a comprehensive audit report via Kimi K2.6
4. **Every step** is signed with a Terminal 3 TEE-backed verifiable identity
5. A **Verification API** lets anyone cryptographically validate the entire chain

Hosted on a Daytona sandbox.

## Sponsor Integration

| Sponsor | Integration | Description |
|---------|-------------|-------------|
| 🔐 **Terminal 3** | Agent identity + action signing | Each agent has a verifiable DID; every action is TEE-signed for tamper-proof audit trails |
| 🌐 **Bright Data** | Web scraping infrastructure | Data Collector agent scrapes company filings and news in real-time |
| 🧠 **Kimi K2.6** | Long-context document analysis | Report Writer uses Kimi's 128K context to generate comprehensive audit reports |
| 📦 **Daytona** | Sandboxed execution + hosting | Risk Scorer runs in an isolated sandbox; app deployed on Daytona |
| ⚡ **TokenRouter** | Smart model routing | Routes LLM calls to optimal models based on task type with caching |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for Terminal 3 SDK)
- API keys from sponsors (see `.env.example`)

### Installation

```bash
# Clone the repository
git clone https://github.com/anishreddy3/auditforge.git
cd auditforge

# Set up Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Terminal 3 Node.js dependencies
cd t3_scripts && npm install && cd ..

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Run Locally

```bash
# Run a single audit via CLI
python main.py "Tesla"

# Start the web UI + API server
python main.py --serve
# Open http://localhost:8000
```

### Deploy to Daytona

```bash
# Make sure DAYTONA_API_KEY is in your .env
python daytona_host.py
```

## Project Structure

```
auditforge/
├── main.py                         # CLI entry point
├── daytona_host.py                 # Daytona deployment script
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container build
├── .env.example                    # Required API keys template
├── src/
│   ├── pipeline/
│   │   └── orchestrator.py         # LangGraph StateGraph pipeline
│   ├── agents/
│   │   ├── data_collector.py       # Bright Data scraping agent
│   │   ├── risk_scorer.py          # Daytona-sandboxed scoring
│   │   └── report_writer.py       # Kimi K2.6 report generation
│   ├── identity/
│   │   └── terminal3.py            # Terminal 3 TEE signing layer
│   ├── routing/
│   │   └── router.py              # TokenRouter model selection
│   ├── api/
│   │   └── verify.py              # FastAPI verification endpoints + UI
│   └── config.py                   # Environment configuration
├── t3_scripts/                     # Node.js bridge for Terminal 3 SDK
│   ├── register_agents.mjs         # Agent DID registration
│   ├── sign_action.mjs            # TEE action signing
│   └── verify_proof.mjs           # Proof verification
├── ui/
│   └── index.html                  # Single-page web UI
├── requirements.md                 # Product requirements
├── design.md                       # System architecture
└── tasks.md                        # Implementation checklist
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/health` | Health check |
| `POST` | `/audit` | Run full audit pipeline |
| `POST` | `/verify` | Verify a proof chain |
| `GET` | `/docs` | OpenAPI documentation |

### Run an Audit

```bash
curl -X POST http://localhost:8000/audit \
  -H 'Content-Type: application/json' \
  -d '{"company_name": "Tesla"}'
```

### Verify a Proof Chain

```bash
curl -X POST http://localhost:8000/verify \
  -H 'Content-Type: application/json' \
  -d '{"proof_chain": [...]}'
```

## Proof Chain Format

Every agent action produces a signed proof entry:

```json
{
  "agent_id": "did:t3n:a1b2c3...",
  "agent_name": "data_collector",
  "action": "collect_company_data",
  "timestamp": 1718300000.123,
  "input_hash": "sha256:bda271b1...",
  "output_hash": "sha256:199c77db...",
  "tee_signature": "t3n_eth_sig_4f8c751f..."
}
```

A CFO or regulator can verify the entire decision chain cryptographically — no trust in the operator required.



## Contributors

Built by [Anish Posim Reddy](https://github.com/anishreddy3) at Agent Forge Hackathon, Singapore — June 2026.

## License

MIT
