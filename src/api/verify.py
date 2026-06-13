"""Verification API — FastAPI endpoints for proof chain validation and UI.

Allows regulators, CFOs, or any party to independently verify
the cryptographic audit trail produced by AuditForge.
"""

import asyncio
import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.identity.terminal3 import identity, ProofEntry

app = FastAPI(
    title="AuditForge",
    description="Multi-Agent Compliance Auditor with Verifiable Agent Identity",
    version="0.1.0",
)


class ProofEntryRequest(BaseModel):
    agent_id: str
    agent_name: str
    action: str
    timestamp: float
    input_hash: str
    output_hash: str
    tee_signature: str


class VerifyRequest(BaseModel):
    proof_chain: list[ProofEntryRequest]


class VerifyResponse(BaseModel):
    valid: bool
    total_steps: int
    verified_steps: int
    failed_steps: list[int]
    message: str


class AuditRequest(BaseModel):
    company_name: str


class AuditResponse(BaseModel):
    success: bool
    company_name: str
    report: str
    proof_chain: list[dict]
    scores: dict
    elapsed_seconds: float
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="auditforge",
        version="0.1.0",
    )


@app.post("/audit", response_model=AuditResponse)
async def run_audit(request: AuditRequest):
    """Run a full audit pipeline for a company.

    Triggers the LangGraph pipeline and returns the report + proof chain.
    """
    from src.pipeline.orchestrator import pipeline, AuditState

    start_time = time.time()

    initial_state: AuditState = {
        "company_name": request.company_name,
        "raw_data": {},
        "risk_analysis": {},
        "audit_report": "",
        "proof_chain": [],
        "status": "started",
        "error": None,
    }

    try:
        result = await pipeline.ainvoke(initial_state)
        elapsed = time.time() - start_time

        if result.get("error"):
            return AuditResponse(
                success=False,
                company_name=request.company_name,
                report="",
                proof_chain=[],
                scores={},
                elapsed_seconds=elapsed,
                error=result["error"],
            )

        return AuditResponse(
            success=True,
            company_name=request.company_name,
            report=result["audit_report"],
            proof_chain=result["proof_chain"],
            scores=result.get("risk_analysis", {}).get("scores", {}),
            elapsed_seconds=elapsed,
        )
    except Exception as e:
        elapsed = time.time() - start_time
        return AuditResponse(
            success=False,
            company_name=request.company_name,
            report="",
            proof_chain=[],
            scores={},
            elapsed_seconds=elapsed,
            error=str(e),
        )


@app.post("/verify", response_model=VerifyResponse)
async def verify_proof_chain(request: VerifyRequest):
    """Verify an entire proof chain from an audit."""
    if not request.proof_chain:
        raise HTTPException(status_code=400, detail="Proof chain cannot be empty")

    verified = 0
    failed_steps = []

    for i, entry_req in enumerate(request.proof_chain):
        proof_entry = ProofEntry(
            agent_id=entry_req.agent_id,
            agent_name=entry_req.agent_name,
            action=entry_req.action,
            timestamp=entry_req.timestamp,
            input_hash=entry_req.input_hash,
            output_hash=entry_req.output_hash,
            tee_signature=entry_req.tee_signature,
        )

        is_valid = await identity.verify_proof(proof_entry)

        if is_valid:
            verified += 1
        else:
            failed_steps.append(i)

    all_valid = verified == len(request.proof_chain)

    return VerifyResponse(
        valid=all_valid,
        total_steps=len(request.proof_chain),
        verified_steps=verified,
        failed_steps=failed_steps,
        message=(
            "All proof chain entries verified successfully."
            if all_valid
            else f"Verification failed for {len(failed_steps)} step(s)."
        ),
    )


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the AuditForge UI."""
    ui_path = Path(__file__).parent.parent.parent / "ui" / "index.html"
    if not ui_path.exists():
        return HTMLResponse("<h1>UI not found</h1>", status_code=404)
    return HTMLResponse(ui_path.read_text())
