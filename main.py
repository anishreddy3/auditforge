"""AuditForge — Multi-Agent Compliance Auditor with Verifiable Agent Identity.

Entry point for running the audit pipeline.

Usage:
    python main.py <company_name>
    python main.py --serve  (start the verification API server)
"""

import asyncio
import json
import sys
import time

from src.pipeline.orchestrator import pipeline, AuditState


async def run_audit(company_name: str) -> None:
    """Run the full AuditForge pipeline for a target company."""
    print("=" * 60)
    print(f"  🏛️  AuditForge — Compliance Audit Pipeline")
    print(f"  Target: {company_name}")
    print("=" * 60)
    print()

    # Initialize pipeline state
    initial_state: AuditState = {
        "company_name": company_name,
        "raw_data": {},
        "risk_analysis": {},
        "audit_report": "",
        "proof_chain": [],
        "status": "started",
        "error": None,
    }

    start_time = time.time()

    # Run the LangGraph pipeline
    print("🚀 Starting audit pipeline...\n")
    result = await pipeline.ainvoke(initial_state)
    elapsed = time.time() - start_time

    print()
    print("=" * 60)

    if result.get("error"):
        print(f"❌ Pipeline failed: {result['error']}")
        return

    print(f"✅ Audit completed in {elapsed:.1f}s")
    print(f"   Status: {result['status']}")
    print(f"   Proof chain: {len(result['proof_chain'])} signed steps")
    print()

    # Display the proof chain
    print("🔐 Cryptographic Proof Chain:")
    print("-" * 40)
    for i, proof in enumerate(result["proof_chain"], 1):
        print(f"  Step {i}: {proof['agent_name']} → {proof['action']}")
        print(f"          Signature: {proof['tee_signature'][:32]}...")
        print(f"          Input hash: {proof['input_hash'][:16]}...")
        print(f"          Output hash: {proof['output_hash'][:16]}...")
        print()

    # Save outputs
    # Save report
    report_path = f"output/{company_name.lower().replace(' ', '_')}_audit_report.md"
    proof_path = f"output/{company_name.lower().replace(' ', '_')}_proof_chain.json"

    import os
    os.makedirs("output", exist_ok=True)

    with open(report_path, "w") as f:
        f.write(result["audit_report"])
    print(f"📄 Report saved: {report_path}")

    with open(proof_path, "w") as f:
        json.dump(result["proof_chain"], f, indent=2)
    print(f"🔗 Proof chain saved: {proof_path}")

    print()
    print("💡 To verify the proof chain, run:")
    print(f"   curl -X POST http://localhost:8000/verify -H 'Content-Type: application/json' -d @{proof_path}")


def serve_api() -> None:
    """Start the AuditForge server (API + UI)."""
    import uvicorn
    from src.api.verify import app

    print("🌐 Starting AuditForge on http://localhost:8000")
    print("   UI:   http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py <company_name>    Run an audit")
        print("  python main.py --serve           Start verification API")
        sys.exit(1)

    if sys.argv[1] == "--serve":
        serve_api()
    else:
        company_name = " ".join(sys.argv[1:])
        asyncio.run(run_audit(company_name))


if __name__ == "__main__":
    main()
