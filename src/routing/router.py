"""TokenRouter Integration — Smart Model Routing.

Routes LLM requests to optimal models based on task type,
leveraging TokenRouter for cost-efficient inference and caching.
"""

import httpx

from src.config import config


# Task type → model mapping
TASK_MODEL_MAP = {
    "data_extraction": "fast",       # Quick extraction tasks
    "risk_analysis": "reasoning",    # Complex reasoning tasks
    "report_writing": "long_context",  # Long-context generation (Kimi K2.6)
}


class TokenRouterClient:
    """Unified interface for routing LLM completions via TokenRouter."""

    def __init__(self):
        self.api_key = config.TOKENROUTER_API_KEY
        self.base_url = config.TOKENROUTER_BASE_URL
        self.client = httpx.AsyncClient(timeout=120.0)

    async def route_completion(
        self,
        task_type: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Route an LLM completion to the optimal model for the task.

        Args:
            task_type: One of 'data_extraction', 'risk_analysis', 'report_writing'.
            messages: OpenAI-compatible message list.
            temperature: Sampling temperature.
            max_tokens: Max tokens in response.

        Returns:
            The model's response text.
        """
        model_tier = TASK_MODEL_MAP.get(task_type, "fast")

        # TODO: Replace with actual TokenRouter API call
        # TokenRouter provides a unified endpoint that routes to the best model
        # Example:
        # response = await self.client.post(
        #     f"{self.base_url}/v1/chat/completions",
        #     headers={"Authorization": f"Bearer {self.api_key}"},
        #     json={
        #         "model": model_tier,
        #         "messages": messages,
        #         "temperature": temperature,
        #         "max_tokens": max_tokens,
        #     }
        # )
        # result = response.json()
        # return result["choices"][0]["message"]["content"]

        raise NotImplementedError(
            f"Wire up TokenRouter API — route to '{model_tier}' tier for task '{task_type}'"
        )

    async def route_to_kimi(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """Directly route to Kimi K2.6 for long-context tasks.

        Falls back to direct Kimi API if TokenRouter is unavailable.
        """
        # Try via TokenRouter first
        if self.base_url and self.api_key:
            try:
                return await self.route_completion(
                    "report_writing", messages, temperature, max_tokens
                )
            except NotImplementedError:
                pass

        # Fallback: direct Kimi K2.6 API call
        response = await self.client.post(
            f"{config.KIMI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.KIMI_API_KEY}"},
            json={
                "model": "kimi-k2.6",
                "messages": messages,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    async def close(self):
        await self.client.aclose()


# Singleton instance
router = TokenRouterClient()
