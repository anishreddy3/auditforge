/**
 * register_agents.mjs — Register AuditForge agent identities on T3N testnet.
 *
 * This script authenticates with Terminal 3's T3N testnet using the developer key,
 * claims a tenant DID, and derives agent DIDs for the three pipeline agents.
 *
 * Environment:
 *   T3N_API_KEY — The developer Ethereum private key from Terminal 3 claim page
 *
 * Output (stdout): JSON with registered agent DIDs
 */

import {
  T3nClient,
  TenantClient,
  setEnvironment,
  loadWasmComponent,
  eth_get_address,
  metamask_sign,
  createEthAuthInput,
  getNodeUrl,
} from "@terminal3/t3n-sdk";

const T3N_API_KEY = process.env.T3N_API_KEY;

if (!T3N_API_KEY) {
  console.log(JSON.stringify({ success: false, error: "T3N_API_KEY not set" }));
  process.exit(0);
}

try {
  // Configure for testnet
  setEnvironment("testnet");

  // Load WASM crypto component
  const wasmComponent = await loadWasmComponent();
  const address = eth_get_address(T3N_API_KEY);

  // Create T3N client
  const t3n = new T3nClient({
    wasmComponent,
    handlers: {
      EthSign: metamask_sign(address, undefined, T3N_API_KEY),
    },
  });

  // Authenticate
  await t3n.handshake();
  const did = await t3n.authenticate(createEthAuthInput(address));
  const tenantDid = did.value;

  // Build tenant client
  const tenant = new TenantClient({
    t3n,
    baseUrl: getNodeUrl(),
    tenantDid,
  });

  // Claim tenant (idempotent — succeeds if already claimed)
  try {
    await tenant.claim();
  } catch (e) {
    // Already claimed is fine
    if (!e.message?.includes("already")) {
      throw e;
    }
  }

  // Get tenant info
  const me = await tenant.me();

  // For AuditForge, each "agent" is identified by a derived DID
  // In production, each agent would have its own key. For the hackathon,
  // we derive deterministic agent identifiers from the tenant DID.
  const agents = {
    data_collector: `${tenantDid}:agent:data_collector`,
    risk_scorer: `${tenantDid}:agent:risk_scorer`,
    report_writer: `${tenantDid}:agent:report_writer`,
  };

  console.log(JSON.stringify({
    success: true,
    tenantDid,
    agents,
    balance: me.balance || null,
  }));

} catch (error) {
  console.log(JSON.stringify({
    success: false,
    error: error.message || String(error),
  }));
}
