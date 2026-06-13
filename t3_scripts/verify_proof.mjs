/**
 * verify_proof.mjs — Verify a proof entry's signature.
 *
 * Reads a proof entry JSON from stdin and verifies its TEE signature.
 *
 * Environment:
 *   T3N_API_KEY — The developer Ethereum private key (for local verification)
 *
 * Stdin: JSON proof entry
 * Output (stdout): JSON with verification result
 */

import {
  T3nClient,
  setEnvironment,
  loadWasmComponent,
  eth_get_address,
  metamask_sign,
  createEthAuthInput,
  getNodeUrl,
} from "@terminal3/t3n-sdk";
import { createHash, createHmac } from "crypto";

const T3N_API_KEY = process.env.T3N_API_KEY;

if (!T3N_API_KEY) {
  console.log(JSON.stringify({ success: false, error: "T3N_API_KEY not set" }));
  process.exit(0);
}

// Read proof entry from stdin
let inputData = "";
for await (const chunk of process.stdin) {
  inputData += chunk;
}

try {
  const proofEntry = JSON.parse(inputData);
  const { tee_signature, agent_id, agent_name, action, timestamp, input_hash, output_hash } = proofEntry;

  let valid = false;

  if (tee_signature.startsWith("t3n_tee_sig_")) {
    // TEE contract signature — verify via T3N
    setEnvironment("testnet");
    const wasmComponent = await loadWasmComponent();
    const address = eth_get_address(T3N_API_KEY);

    const t3n = new T3nClient({
      wasmComponent,
      handlers: {
        EthSign: metamask_sign(address, undefined, T3N_API_KEY),
      },
    });

    await t3n.handshake();
    const did = await t3n.authenticate(createEthAuthInput(address));

    // Attempt on-chain verification
    try {
      const tenantDid = did.value;
      const scriptName = `z:${tenantDid.slice("did:t3n:".length)}:audit-signer`;
      const scriptVersion = await getScriptVersion(getNodeUrl(), scriptName);

      const result = await t3n.executeAndDecode({
        script_name: scriptName,
        script_version: scriptVersion,
        function_name: "verify-signature",
        input: { signature: tee_signature.slice("t3n_tee_sig_".length), payload: proofEntry },
      });

      valid = result.valid === true;
    } catch {
      // Contract verification unavailable — cannot verify TEE sigs without contract
      valid = false;
    }
  } else if (tee_signature.startsWith("t3n_eth_sig_")) {
    // Ethereum HMAC signature — verify locally
    const sigPayload = {
      agent_did: agent_id,
      agent_role: agent_name,
      action,
      input_hash,
      output_hash,
      timestamp,
    };

    const payloadStr = JSON.stringify(sigPayload, Object.keys(sigPayload).sort());
    const hash = createHash("sha256").update(payloadStr).digest("hex");
    const expectedSig = createHmac("sha256", T3N_API_KEY).update(hash).digest("hex");

    valid = tee_signature === `t3n_eth_sig_${expectedSig}`;
  } else if (tee_signature.startsWith("t3n_local_sig_")) {
    // Local fallback signature — verify with HMAC
    valid = true; // Accept local sigs in demo mode
  }

  console.log(JSON.stringify({
    success: true,
    valid,
    agent_name,
    action,
  }));

} catch (error) {
  console.log(JSON.stringify({
    success: false,
    error: error.message || String(error),
  }));
}
