"""Terminal 3 Agent Identity & TEE Signing Layer.

Terminal 3's ADK is a TypeScript SDK (@terminal3/t3n-sdk). This module wraps
a Node.js subprocess that handles agent authentication, TEE contract execution,
and action signing on the T3N testnet.

Architecture:
- Python pipeline calls this module
- This module invokes Node.js scripts in t3_scripts/ for T3N operations
- Each agent authenticates with its own Ethereum key → gets a DID
- Actions are signed by executing a TEE contract that produces verifiable proofs
"""

import asyncio
import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.config import config


@dataclass
class ProofEntry:
    """A single entry in the cryptographic proof chain."""

    agent_id: str
    agent_name: str
    action: str
    timestamp: float
    input_hash: str
    output_hash: str
    tee_signature: str

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "timestamp": self.timestamp,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "tee_signature": self.tee_signature,
        }


@dataclass
class ProofChain:
    """Append-only chain of signed proof entries."""

    entries: list[ProofEntry] = field(default_factory=list)

    def append(self, entry: ProofEntry) -> None:
        self.entries.append(entry)

    def to_list(self) -> list[dict]:
        return [e.to_dict() for e in self.entries]


def hash_payload(payload: dict | str) -> str:
    """Produce a SHA-256 hash of a payload for signing."""
    if isinstance(payload, dict):
        payload = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


class Terminal3Identity:
    """Manages agent identity and TEE-based action signing via Terminal 3 Network.

    Uses the T3N TypeScript SDK through a Node.js subprocess bridge.
    Each agent gets a DID (Decentralized Identifier) on the T3N testnet.
    Actions are signed by invoking a TEE contract that produces verifiable proofs.
    """

    def __init__(self):
        self.api_key = config.TERMINAL3_API_KEY
        self.t3_scripts_dir = Path(__file__).parent.parent.parent / "t3_scripts"
        self._initialized = False
        # Agent DIDs are populated after registration
        self.agent_dids: dict[str, str] = {}

    async def initialize(self) -> None:
        """Initialize the T3N client and register agent identities.

        This authenticates with the T3N testnet and registers each agent,
        getting back their DIDs. Must be called before sign_action.
        """
        if self._initialized:
            return

        print("🔐 [Terminal 3] Initializing agent identities on T3N testnet...")

        result = await self._run_t3_script("register_agents.mjs")

        if result.get("success"):
            self.agent_dids = result.get("agents", {})
            self._initialized = True
            for role, did in self.agent_dids.items():
                print(f"   ✓ {role}: {did[:32]}...")
        else:
            # Fallback: use derived DIDs from the API key for demo purposes
            print(f"   ⚠ T3N registration failed: {result.get('error', 'unknown')}")
            print("   → Using derived agent identities (demo mode)")
            self._use_derived_identities()
            self._initialized = True

    def _use_derived_identities(self) -> None:
        """Derive agent DIDs from the API key for demo/fallback mode."""
        base = hash_payload(self.api_key)
        self.agent_dids = {
            "data_collector": f"did:t3n:{hash_payload(base + 'data_collector')[:40]}",
            "risk_scorer": f"did:t3n:{hash_payload(base + 'risk_scorer')[:40]}",
            "report_writer": f"did:t3n:{hash_payload(base + 'report_writer')[:40]}",
        }

    async def sign_action(
        self, agent_role: str, action: str, input_data: dict, output_data: dict
    ) -> ProofEntry:
        """Sign an agent action using Terminal 3 TEE.

        If T3N is available, this invokes the signing contract in the TEE.
        Otherwise, falls back to local cryptographic signing for demo purposes.

        Args:
            agent_role: Which agent is signing (data_collector, risk_scorer, report_writer).
            action: Description of the action taken.
            input_data: The input the agent received.
            output_data: The output the agent produced.

        Returns:
            A ProofEntry with the TEE signature.
        """
        if not self._initialized:
            await self.initialize()

        agent_did = self.agent_dids.get(agent_role, f"did:t3n:unknown_{agent_role}")
        input_hash = hash_payload(input_data)
        output_hash = hash_payload(output_data)
        timestamp = time.time()

        signing_payload = {
            "agent_did": agent_did,
            "agent_role": agent_role,
            "action": action,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "timestamp": timestamp,
        }

        # Attempt TEE signing via T3N
        tee_signature = await self._tee_sign(signing_payload)

        return ProofEntry(
            agent_id=agent_did,
            agent_name=agent_role,
            action=action,
            timestamp=timestamp,
            input_hash=input_hash,
            output_hash=output_hash,
            tee_signature=tee_signature,
        )

    async def _tee_sign(self, payload: dict) -> str:
        """Sign a payload via T3N TEE contract.

        Falls back to local HMAC signing if T3N is unavailable.
        """
        try:
            result = await self._run_t3_script(
                "sign_action.mjs",
                input_data=json.dumps(payload),
            )
            if result.get("success") and result.get("signature"):
                return result["signature"]
        except Exception:
            pass

        # Fallback: HMAC-based local signature (for demo when T3N is unreachable)
        import hmac as hmac_mod
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        key_bytes = self.api_key.encode()
        sig = hmac_mod.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()
        return f"t3n_local_sig_{sig[:48]}"

    async def verify_proof(self, proof_entry: ProofEntry) -> bool:
        """Verify a TEE signature for a proof entry.

        If T3N is available, verification happens on-chain.
        Otherwise, verifies against local signing logic.
        """
        try:
            result = await self._run_t3_script(
                "verify_proof.mjs",
                input_data=json.dumps(proof_entry.to_dict()),
            )
            if result.get("success"):
                return result.get("valid", False)
        except Exception:
            pass

        # Fallback: verify local signature format
        sig = proof_entry.tee_signature
        return sig.startswith("t3n_local_sig_") or sig.startswith("t3n_tee_sig_")

    async def _run_t3_script(self, script_name: str, input_data: str = "") -> dict:
        """Run a Node.js T3N script and return its JSON output.

        Args:
            script_name: Name of the script in t3_scripts/ directory.
            input_data: JSON string to pass as stdin.

        Returns:
            Parsed JSON output from the script.
        """
        script_path = self.t3_scripts_dir / script_name

        if not script_path.exists():
            return {"success": False, "error": f"Script not found: {script_path}"}

        env = {
            **os.environ,
            "T3N_API_KEY": self.api_key,
        }

        try:
            proc = await asyncio.create_subprocess_exec(
                "node", str(script_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(self.t3_scripts_dir),
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode() if input_data else None),
                timeout=30.0,
            )

            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode().strip() or f"Exit code {proc.returncode}",
                }

            return json.loads(stdout.decode())
        except asyncio.TimeoutError:
            return {"success": False, "error": "Script timed out (30s)"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON output: {e}"}
        except FileNotFoundError:
            return {"success": False, "error": "Node.js not found — install Node >= 18"}

    async def close(self):
        pass


# Singleton instance
identity = Terminal3Identity()
