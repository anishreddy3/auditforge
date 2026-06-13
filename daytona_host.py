"""Deploy AuditForge to a Daytona sandbox."""

import os
from dotenv import load_dotenv
from daytona import Daytona, CreateSandboxFromImageParams, Image, Resources

load_dotenv()

daytona = Daytona()  # Uses DAYTONA_API_KEY and DAYTONA_BASE_URL from env

# Create sandbox with Python pre-installed (Node installed after creation)
image = (
    Image.debian_slim("3.12")
    .pip_install([
        "langgraph", "langchain-core", "fastapi", "uvicorn",
        "httpx", "python-dotenv", "pydantic",
    ])
    .workdir("/home/daytona")
)

# Pass env vars directly to the sandbox
env_vars = {
    "TERMINAL3_API_KEY": os.getenv("TERMINAL3_API_KEY", ""),
    "BRIGHTDATA_API_KEY": os.getenv("BRIGHTDATA_API_KEY", ""),
    "BRIGHTDATA_ZONE": os.getenv("BRIGHTDATA_ZONE", ""),
    "KIMI_API_KEY": os.getenv("KIMI_API_KEY", ""),
    "KIMI_BASE_URL": "https://api.moonshot.ai/v1",
    "DAYTONA_API_KEY": os.getenv("DAYTONA_API_KEY", ""),
    "DAYTONA_BASE_URL": os.getenv("DAYTONA_BASE_URL", "https://app.daytona.io/api"),
    "TOKENROUTER_API_KEY": os.getenv("TOKENROUTER_API_KEY", ""),
    "TOKENROUTER_BASE_URL": os.getenv("TOKENROUTER_BASE_URL", ""),
}

print("🚀 Creating Daytona sandbox...")
sandbox = daytona.create(
    CreateSandboxFromImageParams(
        image=image,
        resources=Resources(cpu=2, memory=4, disk=8),
        name="auditforge-v2",
        public=True,
        env_vars=env_vars,
    ),
    on_snapshot_create_logs=print,
)

print(f"✅ Sandbox created: {sandbox.id}")

# Install Node.js inside the running sandbox
print("📦 Installing Node.js...")
response = sandbox.process.exec("apt-get update && apt-get install -y curl git && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs")
print(f"   Node installed: {sandbox.process.exec('node --version').result.strip()}")

# Clone repo
print("📦 Cloning repository...")
response = sandbox.process.exec("git clone https://github.com/anishreddy3/auditforge.git /home/daytona/app")
print(f"   {response.result.strip()}")

# Install T3N deps
print("📦 Installing Node.js dependencies...")
response = sandbox.process.exec("cd /home/daytona/app/t3_scripts && npm install --production")
print(f"   Done")

# Create .env file from env vars
print("🔑 Writing .env file...")
env_lines = "\\n".join(f"{k}={v}" for k, v in env_vars.items())
sandbox.process.exec(f'printf "{env_lines}" > /home/daytona/app/.env')

# Create a startup script and launch in background
print("🌐 Starting AuditForge server on port 8000...")
sandbox.process.exec(
    "echo '#!/bin/bash\ncd /home/daytona/app && exec python main.py --serve' > /home/daytona/start.sh && chmod +x /home/daytona/start.sh"
)
# Use timeout=5 so exec returns quickly after daemonizing
try:
    sandbox.process.exec(
        "bash -c 'setsid /home/daytona/start.sh > /tmp/auditforge.log 2>&1 < /dev/null &'",
        timeout=5,
    )
except Exception:
    pass  # Timeout is expected — server is starting in background

# Wait for server to boot
import time
time.sleep(5)
response = sandbox.process.exec("curl -s http://localhost:8000/health")
print(f"   Health check: {response.result.strip()}")

print()
print("=" * 60)
print("  ✅ AuditForge deployed successfully!")
print(f"  Sandbox ID: {sandbox.id}")
print(f"  Dashboard:  https://app.daytona.io")
print("=" * 60)
print()
print("To stop and clean up:")
print(f'  python -c "from daytona import Daytona; Daytona().delete(\'{sandbox.id}\')"')


from daytona import Daytona
d = Daytona()
sb = d.get("57ba420d-c557-4768-86d6-defa74170664")
link = sb.get_preview_link(8000)
print(link.url)