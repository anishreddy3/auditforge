"""LangGraph Pipeline Orchestrator.

Defines the multi-agent pipeline using LangGraph's StateGraph.
Agents execute in sequence: Data Collector → Risk Scorer → Report Writer.
Each step produces a TEE-signed proof entry.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, END

from src.agents.data_collector import DataCollectorAgent
from src.agents.risk_scorer import RiskScorerAgent
from src.agents.report_writer import ReportWriterAgent
from src.identity.terminal3 import ProofChain


class AuditState(TypedDict):
    """Shared pipeline state passed between agents."""

    company_name: str
    raw_data: dict
    risk_analysis: dict
    audit_report: str
    proof_chain: list[dict]
    status: str
    error: str | None


# Agent instances
data_collector = DataCollectorAgent()
risk_scorer = RiskScorerAgent()
report_writer = ReportWriterAgent()


async def initialize_identities_node(state: AuditState) -> AuditState:
    """Node: Initialize Terminal 3 agent identities on T3N testnet."""
    from src.identity.terminal3 import identity

    print("🔐 [Terminal 3] Registering agent identities...")
    await identity.initialize()
    return state


async def collect_data_node(state: AuditState) -> AuditState:
    """Node: Data Collector agent scrapes company information."""
    print(f"📡 [Data Collector] Scraping data for: {state['company_name']}")

    try:
        collected_data, proof = await data_collector.collect(state["company_name"])
        state["raw_data"] = collected_data
        state["proof_chain"].append(proof.to_dict())
        state["status"] = "data_collected"
        print(f"   ✓ Collected {collected_data['sources_count']} sources")
        print(f"   🔏 Action signed: {proof.tee_signature[:24]}...")
    except Exception as e:
        state["error"] = f"Data collection failed: {e}"
        state["status"] = "failed"
        print(f"   ✗ Error: {e}")

    return state


async def score_risk_node(state: AuditState) -> AuditState:
    """Node: Risk Scorer agent computes risk scores in sandbox."""
    print(f"🧮 [Risk Scorer] Computing risk scores for: {state['company_name']}")

    if state.get("error"):
        return state

    try:
        risk_data, proof = await risk_scorer.score(state["raw_data"])
        state["risk_analysis"] = risk_data
        state["proof_chain"].append(proof.to_dict())
        state["status"] = "risk_scored"
        scores = risk_data["scores"]
        print(f"   ✓ Composite score: {scores['composite_score']} ({scores['risk_level']})")
        print(f"   🔏 Action signed: {proof.tee_signature[:24]}...")
    except Exception as e:
        state["error"] = f"Risk scoring failed: {e}"
        state["status"] = "failed"
        print(f"   ✗ Error: {e}")

    return state


async def write_report_node(state: AuditState) -> AuditState:
    """Node: Report Writer agent generates the audit report."""
    print(f"📝 [Report Writer] Generating audit report for: {state['company_name']}")

    if state.get("error"):
        return state

    try:
        report, proof = await report_writer.write_report(
            company_name=state["company_name"],
            collected_data=state["raw_data"],
            risk_data=state["risk_analysis"],
            proof_chain_so_far=state["proof_chain"],
        )
        state["audit_report"] = report
        state["proof_chain"].append(proof.to_dict())
        state["status"] = "completed"
        print(f"   ✓ Report generated ({len(report)} chars)")
        print(f"   🔏 Action signed: {proof.tee_signature[:24]}...")
    except Exception as e:
        state["error"] = f"Report writing failed: {e}"
        state["status"] = "failed"
        print(f"   ✗ Error: {e}")

    return state


def should_continue(state: AuditState) -> str:
    """Determine if pipeline should continue or stop on error."""
    if state.get("error"):
        return END
    return "continue"


def build_pipeline() -> StateGraph:
    """Build and compile the LangGraph audit pipeline."""
    workflow = StateGraph(AuditState)

    # Add nodes
    workflow.add_node("initialize_identities", initialize_identities_node)
    workflow.add_node("collect_data", collect_data_node)
    workflow.add_node("score_risk", score_risk_node)
    workflow.add_node("write_report", write_report_node)

    # Define edges (sequential flow)
    workflow.set_entry_point("initialize_identities")
    workflow.add_edge("initialize_identities", "collect_data")
    workflow.add_edge("collect_data", "score_risk")
    workflow.add_edge("score_risk", "write_report")
    workflow.add_edge("write_report", END)

    return workflow.compile()


# Compiled pipeline (ready to invoke)
pipeline = build_pipeline()
