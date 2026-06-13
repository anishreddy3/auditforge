"""Risk Scorer Agent — Daytona Sandboxed Execution.

Executes financial risk calculations in an isolated Daytona sandbox
to prevent data leakage and ensure computation integrity.
"""

import time

import httpx

from src.config import config
from src.identity.terminal3 import identity, ProofEntry


# Scoring code that will execute inside the Daytona sandbox
SCORING_CODE = '''
import json
import sys

data = json.loads(sys.argv[1])
filings = data.get("filings", [])
news = data.get("news", [])

# Financial Health Score (0-100)
financial_score = 75  # Base score
if any("growth" in f.get("summary", "").lower() for f in filings):
    financial_score += 10
if any("loss" in f.get("summary", "").lower() for f in filings):
    financial_score -= 15

# Regulatory Compliance Score (0-100)
compliance_score = 80  # Base score
if any("approval" in n.get("summary", "").lower() for n in news):
    compliance_score += 10
if any("violation" in n.get("summary", "").lower() for n in news):
    compliance_score -= 20

# Reputation Risk Score (0-100)
reputation_score = 70  # Base score
if any("risk" in n.get("title", "").lower() for n in news):
    reputation_score -= 10
if any("award" in n.get("title", "").lower() for n in news):
    reputation_score += 10

# Clamp scores
financial_score = max(0, min(100, financial_score))
compliance_score = max(0, min(100, compliance_score))
reputation_score = max(0, min(100, reputation_score))

# Composite score (weighted average)
composite = (financial_score * 0.4) + (compliance_score * 0.35) + (reputation_score * 0.25)

result = {
    "financial_health": {"score": financial_score, "explanation": "Based on filing revenue trends"},
    "regulatory_compliance": {"score": compliance_score, "explanation": "Based on regulatory news signals"},
    "reputation_risk": {"score": reputation_score, "explanation": "Based on recent media coverage"},
    "composite_score": round(composite, 1),
    "risk_level": "LOW" if composite >= 70 else "MEDIUM" if composite >= 50 else "HIGH"
}

print(json.dumps(result))
'''


class RiskScorerAgent:
    """Agent that computes risk scores inside a Daytona sandbox."""

    AGENT_ROLE = "risk_scorer"

    def __init__(self):
        self.api_key = config.DAYTONA_API_KEY
        self.base_url = config.DAYTONA_BASE_URL
        self.client = httpx.AsyncClient(timeout=90.0)

    async def score(self, collected_data: dict) -> tuple[dict, ProofEntry]:
        """Compute risk scores for the collected company data.

        Args:
            collected_data: Output from the Data Collector agent.

        Returns:
            Tuple of (risk scores dict, signed proof entry).
        """
        input_data = {
            "company_name": collected_data["company_name"],
            "sources_count": collected_data["sources_count"],
        }

        # Execute scoring in Daytona sandbox
        scores = await self._execute_in_sandbox(collected_data)

        output_data = {
            "company_name": collected_data["company_name"],
            "scores": scores,
            "scored_at": time.time(),
        }

        # Sign the action with Terminal 3
        proof = await identity.sign_action(
            agent_role=self.AGENT_ROLE,
            action="compute_risk_scores",
            input_data=input_data,
            output_data=output_data,
        )

        return output_data, proof

    async def _execute_in_sandbox(self, data: dict) -> dict:
        """Execute scoring logic inside a Daytona sandbox.

        TODO: Replace with actual Daytona SDK integration.
        """
        # TODO: Actual Daytona API call
        # Example using Daytona SDK:
        # from daytona_sdk import Daytona
        # daytona = Daytona()
        # sandbox = daytona.create()
        # response = sandbox.process.code_run(SCORING_CODE)
        # sandbox.delete()
        # return json.loads(response.result)

        # For now, execute the scoring logic locally (same algorithm)
        import json

        filings = data.get("filings", [])
        news = data.get("news", [])

        financial_score = 75
        if any("growth" in f.get("summary", "").lower() for f in filings):
            financial_score += 10
        if any("loss" in f.get("summary", "").lower() for f in filings):
            financial_score -= 15

        compliance_score = 80
        if any("approval" in n.get("summary", "").lower() for n in news):
            compliance_score += 10
        if any("violation" in n.get("summary", "").lower() for n in news):
            compliance_score -= 20

        reputation_score = 70
        if any("risk" in n.get("title", "").lower() for n in news):
            reputation_score -= 10
        if any("award" in n.get("title", "").lower() for n in news):
            reputation_score += 10

        financial_score = max(0, min(100, financial_score))
        compliance_score = max(0, min(100, compliance_score))
        reputation_score = max(0, min(100, reputation_score))

        composite = (financial_score * 0.4) + (compliance_score * 0.35) + (reputation_score * 0.25)

        return {
            "financial_health": {"score": financial_score, "explanation": "Based on filing revenue trends"},
            "regulatory_compliance": {"score": compliance_score, "explanation": "Based on regulatory news signals"},
            "reputation_risk": {"score": reputation_score, "explanation": "Based on recent media coverage"},
            "composite_score": round(composite, 1),
            "risk_level": "LOW" if composite >= 70 else "MEDIUM" if composite >= 50 else "HIGH",
        }

    async def close(self):
        await self.client.aclose()
