# AuditForge — Implementation Tasks

## Phase 1: Project Setup & Foundation

### Task 1.1: Initialize Project Structure
- [ ] Create directory structure as defined in design.md
- [ ] Initialize Python project with `pyproject.toml` or `requirements.txt`
- [ ] Create `.env.example` with all required API keys
- [ ] Set up `src/config.py` for environment variable loading
- **Estimate**: 15 min

### Task 1.2: Install Dependencies
- [ ] `langgraph`, `langchain-core` — pipeline orchestration
- [ ] `fastapi`, `uvicorn` — verification API
- [ ] `httpx` — async HTTP client for Bright Data / APIs
- [ ] `python-dotenv` — env management
- [ ] Terminal 3 SDK (check docs for package name)
- [ ] Daytona SDK
- **Estimate**: 10 min

### Task 1.3: Claim Sponsor Credits
- [ ] Bright Data: http://get.brightdata.com/aibuilders10
- [ ] Daytona: https://app.daytona.io/dashboard/billing/wallet
- [ ] Kimi AI: https://platform.kimi.ai/console/voucher-detail
- [ ] TokenRouter: https://tinyurl.com/tokenroutercredits
- [ ] Terminal 3: https://www.terminal3.io/products/agent-developer-kit
- **Estimate**: 15 min

---

## Phase 2: Terminal 3 Identity Layer (Core Differentiator)

### Task 2.1: Set Up Terminal 3 Agent Dev Kit
- [ ] Register 3 agent identities (Data Collector, Risk Scorer, Report Writer)
- [ ] Implement `src/identity/terminal3.py` with:
  - `register_agent(agent_name, role)` → agent credentials
  - `sign_action(agent_id, payload)` → TEE signature
  - `verify_proof(signature, payload)` → boolean
- [ ] Test signing and verification round-trip
- **Estimate**: 45 min

### Task 2.2: Define Proof Chain Schema
- [ ] Define JSON schema for a single proof entry:
  ```json
  {
    "agent_id": "...",
    "agent_name": "...",
    "action": "...",
    "timestamp": "...",
    "input_hash": "...",
    "output_hash": "...",
    "tee_signature": "..."
  }
  ```
- [ ] Implement helper to append proofs to the chain
- **Estimate**: 15 min

---

## Phase 3: Agent Implementations

### Task 3.1: Data Collector Agent (Bright Data)
- [ ] Set up Bright Data API credentials
- [ ] Implement `src/agents/data_collector.py`:
  - Accept company name as input
  - Scrape company filings / news via Bright Data web scraping API
  - Structure results as JSON (source, url, content, timestamp)
  - Sign output with Terminal 3
- [ ] Handle rate limits and errors gracefully
- **Estimate**: 45 min

### Task 3.2: Risk Scorer Agent (Daytona)
- [ ] Set up Daytona sandbox credentials
- [ ] Implement `src/agents/risk_scorer.py`:
  - Accept raw data from Data Collector
  - Spawn a Daytona sandbox for computation
  - Execute scoring logic (financial health, compliance, reputation)
  - Return structured risk scores with explanations
  - Sign output with Terminal 3
- [ ] Define scoring formulas (can be simple for MVP)
- **Estimate**: 45 min

### Task 3.3: Report Writer Agent (Kimi K2.6 + TokenRouter)
- [ ] Set up Kimi K2.6 API key and TokenRouter credentials
- [ ] Implement `src/routing/router.py`:
  - Configure TokenRouter with available models
  - Implement `route_completion(task_type, messages)` function
- [ ] Implement `src/agents/report_writer.py`:
  - Accept risk analysis + raw data
  - Generate comprehensive audit report via Kimi K2.6 (routed through TokenRouter)
  - Include proof chain references in the report
  - Sign output with Terminal 3
- **Estimate**: 45 min

---

## Phase 4: Pipeline Orchestration (LangGraph)

### Task 4.1: Define LangGraph State & Nodes
- [ ] Implement `src/pipeline/orchestrator.py`:
  - Define `AuditState` TypedDict
  - Create node functions wrapping each agent
  - Define edges: data_collector → risk_scorer → report_writer
- [ ] Add error handling at each node
- **Estimate**: 30 min

### Task 4.2: Wire Up End-to-End Pipeline
- [ ] Implement `main.py` as CLI entry point
- [ ] Accept company name as argument
- [ ] Run full pipeline and output report + proof chain
- [ ] Print summary to console
- **Estimate**: 20 min

---

## Phase 5: Verification API

### Task 5.1: Build Verification Endpoint
- [ ] Implement `src/api/verify.py`:
  - `POST /verify` — accepts proof chain JSON
  - Iterates through each proof entry
  - Verifies each TEE signature via Terminal 3
  - Returns verification result (all valid / which failed)
- [ ] Add `GET /health` endpoint
- **Estimate**: 20 min

### Task 5.2: Add Report Viewing Endpoint
- [ ] `GET /report/{audit_id}` — returns the generated report
- [ ] `GET /proof/{audit_id}` — returns the raw proof chain
- **Estimate**: 15 min

---

## Phase 6: Integration Testing & Demo Prep

### Task 6.1: End-to-End Test
- [ ] Run pipeline for a test company (e.g., "Tesla" or "Apple")
- [ ] Verify all 3 agent steps produce signed outputs
- [ ] Verify proof chain passes verification API
- [ ] Fix any integration issues
- **Estimate**: 30 min

### Task 6.2: Prepare Demo Script
- [ ] Write demo commands / script to run in 2 minutes
- [ ] Prepare fallback (pre-cached results if APIs are slow)
- [ ] Test demo flow end-to-end at least twice
- **Estimate**: 20 min

### Task 6.3: Polish Output
- [ ] Ensure report is well-formatted Markdown
- [ ] Add clear labels showing which sponsor tool produced each section
- [ ] Console output should show real-time progress through pipeline steps
- **Estimate**: 15 min

---

## Time Budget Summary

| Phase | Estimated Time |
|-------|---------------|
| Phase 1: Setup | 40 min |
| Phase 2: Terminal 3 Identity | 60 min |
| Phase 3: Agent Implementations | 2 hr 15 min |
| Phase 4: Pipeline Orchestration | 50 min |
| Phase 5: Verification API | 35 min |
| Phase 6: Testing & Demo | 65 min |
| **Total** | **~6 hr** |

> **Note**: Hackathon is ~5 hours of hacking time. Prioritize Phases 1-4 first. Phase 5 and 6 polish can be trimmed if behind schedule. The key demo moment is showing the signed proof chain — make sure Terminal 3 integration works early.

---

## Priority Order (if time-constrained)

1. ⭐ Terminal 3 identity + signing (this is the differentiator)
2. ⭐ LangGraph pipeline with 3 agents working end-to-end
3. Bright Data scraping in Data Collector
4. Daytona sandbox for Risk Scorer
5. Kimi K2.6 + TokenRouter for Report Writer
6. Verification API
7. Polish and demo prep
