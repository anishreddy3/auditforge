# AuditForge — System Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AuditForge Pipeline                       │
│                         (LangGraph Orchestrator)                 │
├─────────────┬──────────────────┬──────────────────┬─────────────┤
│  Data       │   Risk           │   Report         │  Verification│
│  Collector  │   Scorer         │   Writer         │  API         │
│  Agent      │   Agent          │   Agent          │              │
├─────────────┼──────────────────┼──────────────────┼─────────────┤
│ Bright Data │ Daytona Sandbox  │ Kimi K2.6        │ Terminal 3   │
│ (scraping)  │ (computation)    │ (long-context)   │ (identity)   │
├─────────────┴──────────────────┴──────────────────┴─────────────┤
│                        TokenRouter (model routing)               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. LangGraph Orchestrator (`src/pipeline/orchestrator.py`)

- Defines a StateGraph with nodes for each agent
- Manages shared state (company name, collected data, scores, report)
- Handles error recovery and retries
- Emits structured logs at each transition

**State Schema:**
```python
class AuditState(TypedDict):
    company_name: str
    raw_data: dict          # Output of Data Collector
    risk_analysis: dict     # Output of Risk Scorer
    audit_report: str       # Output of Report Writer
    proof_chain: list       # List of TEE-signed proofs per step
    metadata: dict          # Timestamps, agent IDs, etc.
```

### 2. Data Collector Agent (`src/agents/data_collector.py`)

- **Identity**: Registered Terminal 3 agent with verifiable credentials
- **Function**: Scrapes target company data via Bright Data APIs
- **Data sources**:
  - Company filings (SEC EDGAR or equivalent)
  - Recent news articles
  - Public financial records
- **Output**: Structured JSON with source URLs, timestamps, content
- **Signing**: Every data retrieval action is TEE-signed before passing downstream

### 3. Risk Scorer Agent (`src/agents/risk_scorer.py`)

- **Identity**: Registered Terminal 3 agent
- **Function**: Analyzes collected data and computes risk scores
- **Execution**: Runs scoring logic inside a Daytona sandbox
- **Scoring dimensions**:
  - Financial health score (0-100)
  - Regulatory compliance score (0-100)
  - Reputation risk score (0-100)
  - Overall composite score
- **Output**: Structured risk assessment with explanations
- **Signing**: Score computation results are TEE-signed

### 4. Report Writer Agent (`src/agents/report_writer.py`)

- **Identity**: Registered Terminal 3 agent
- **Function**: Synthesizes data + scores into a final audit report
- **Model**: Uses Kimi K2.6 via TokenRouter for long-context document generation
- **Output format**: Markdown report with embedded proof references
- **Signing**: Final report hash is TEE-signed

### 5. Terminal 3 Identity Layer (`src/identity/terminal3.py`)

- Manages agent identity registration and credential issuance
- Provides `sign_action(agent_id, action_payload)` → TEE signature
- Provides `verify_proof(signature, payload)` → boolean
- Wraps Terminal 3 Agent Dev Kit APIs

### 6. TokenRouter Integration (`src/routing/router.py`)

- Routes LLM calls based on task type:
  - Data extraction → fast, cheap model
  - Risk analysis → reasoning-focused model
  - Report writing → long-context model (Kimi K2.6)
- Provides unified interface: `route_completion(task_type, messages)`

### 7. Verification API (`src/api/verify.py`)

- FastAPI endpoint for external verification
- `POST /verify` — accepts a report + proof chain, returns verification result
- Allows regulators/CFOs to independently validate the audit trail

## Data Flow

```
1. User submits company name
       │
       ▼
2. Data Collector (Bright Data scraping)
   → Signs collected data with Terminal 3
       │
       ▼
3. Risk Scorer (Daytona sandbox execution)
   → Signs risk scores with Terminal 3
       │
       ▼
4. Report Writer (Kimi K2.6 via TokenRouter)
   → Signs final report with Terminal 3
       │
       ▼
5. Output: Audit Report + Proof Chain
       │
       ▼
6. Verification API (anyone can verify)
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | LangGraph (Python) |
| Web Framework | FastAPI |
| Data Scraping | Bright Data API |
| LLM (long-context) | Kimi K2.6 |
| LLM Routing | TokenRouter |
| Sandboxing | Daytona SDK |
| Agent Identity | Terminal 3 Agent Dev Kit |
| Runtime | Python 3.11+ |

## Project Structure

```
auditforge/
├── src/
│   ├── pipeline/
│   │   └── orchestrator.py      # LangGraph pipeline definition
│   ├── agents/
│   │   ├── data_collector.py    # Bright Data scraping agent
│   │   ├── risk_scorer.py       # Daytona-sandboxed scoring agent
│   │   └── report_writer.py    # Kimi K2.6 report generation agent
│   ├── identity/
│   │   └── terminal3.py         # Terminal 3 identity & signing
│   ├── routing/
│   │   └── router.py            # TokenRouter integration
│   ├── api/
│   │   └── verify.py            # Verification endpoint
│   └── config.py                # Environment & API key config
├── requirements.txt
├── .env.example
├── main.py                      # Entry point
├── requirements.md
├── design.md
└── tasks.md
```

## Security Considerations

- All API keys stored in environment variables (never committed)
- Daytona sandbox isolates financial computation from main process
- TEE signatures are non-repudiable — agents cannot deny actions
- Proof chain is append-only; tampering is detectable
- No PII stored in logs; only hashes and references

## Demo Flow (2 minutes)

1. **[0:00-0:20]** Show the pipeline config — 3 agents, each with Terminal 3 identity
2. **[0:20-0:50]** Trigger audit for "Acme Corp" → show live Bright Data scraping
3. **[0:50-1:20]** Show Risk Scorer running in Daytona sandbox, producing scores
4. **[1:20-1:40]** Show Report Writer generating audit report via Kimi K2.6
5. **[1:40-2:00]** Show the proof chain — call verification API to prove integrity
