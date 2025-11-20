# MCP Servers Troubleshooting Guide

## Issue Summary

From the test results:
- **IBKR MCP**: Connection error - "This event loop is already running"
- **ThetaData MCP**: Timeout error

Let's troubleshoot both:

## 1. IBKR MCP Issues

### Error: "This event loop is already running"

This is a common issue with `ib-insync` in async environments.

**Solutions:**

#### Option A: Restart IBKR Gateway/TWS
```bash
# 1. Stop IBKR Gateway if running
# 2. Restart it with these settings:
#    - Port: 4002 (paper trading) or 4001 (live)
#    - Enable API connections
#    - Read-Only API: OFF (allow modifications)
#    - Client ID: Any (MCP will use 1, watchdog should use 999)
```

#### Option B: Check MCP Server Configuration

The IBKR MCP server configuration should look like:
```json
{
  "mcpServers": {
    "ibkr": {
      "command": "path/to/ibkr-mcp",
      "args": ["--host", "127.0.0.1", "--port", "4002", "--client-id", "1"],
      "env": {
        "IBKR_HOST": "127.0.0.1",
        "IBKR_PORT": "4002"
      }
    }
  }
}
```

#### Option C: Test IBKR Connection Directly

```bash
# Test if IBKR Gateway is accepting connections
python3 << 'EOF'
from ib_insync import IB
import asyncio

async def test_connection():
    ib = IB()
    await ib.connectAsync('127.0.0.1', 4002, clientId=1)
    print("✅ Connected to IBKR successfully!")
    print(f"Account: {ib.managedAccounts()}")
    ib.disconnect()

asyncio.run(test_connection())
EOF
```

## 2. ThetaData MCP Issues

### Error: Timeout

This suggests:
1. API key not set or invalid
2. Network connectivity issue
3. MCP server not configured correctly

**Solutions:**

#### Option A: Verify API Key

```bash
# Check if API key is set
echo $THETADATA_API_KEY

# Test API directly
curl "https://api.thetadata.com/v2/quote?symbol=AAPL&api_key=$THETADATA_API_KEY"
```

#### Option B: Check MCP Configuration

The ThetaData MCP configuration should look like:
```json
{
  "mcpServers": {
    "ThetaData": {
      "command": "path/to/thetadata-mcp",
      "env": {
        "THETADATA_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### Option C: Test ThetaData Directly

```bash
# Install thetadata library if needed
pip install thetadata

# Test connection
python3 << 'EOF'
from thetadata import ThetaClient

client = ThetaClient()
# client.connect()  # Use default demo credentials or set API key

print("✅ ThetaData client created")
# Test quote fetch
# quote = client.get_quote("AAPL")
# print(f"AAPL Quote: {quote}")
EOF
```

## 3. Quick Diagnostic Script

Save this as `diagnose_mcp.py`:

```python
#!/usr/bin/env python3
"""Diagnostic script for MCP server connections."""

import os
import sys

print("=" * 60)
print("MCP Servers Diagnostic")
print("=" * 60)

# Check environment variables
print("\n[1/4] Checking Environment Variables...")
ibkr_host = os.getenv("IBKR_HOST", "127.0.0.1")
ibkr_port = os.getenv("IBKR_PORT", "4002")
theta_key = os.getenv("THETADATA_API_KEY")

print(f"   IBKR_HOST: {ibkr_host}")
print(f"   IBKR_PORT: {ibkr_port}")
print(f"   THETADATA_API_KEY: {'✓ Set' if theta_key else '✗ Not set'}")

# Test IBKR connection
print("\n[2/4] Testing IBKR Connection...")
try:
    from ib_insync import IB
    import asyncio

    async def test_ibkr():
        ib = IB()
        await ib.connectAsync(ibkr_host, int(ibkr_port), clientId=1, timeout=5)
        accounts = ib.managedAccounts()
        ib.disconnect()
        return accounts

    accounts = asyncio.run(test_ibkr())
    print(f"   ✓ IBKR Connected: {accounts}")
except Exception as e:
    print(f"   ✗ IBKR Connection Failed: {e}")

# Test ThetaData
print("\n[3/4] Testing ThetaData API...")
if theta_key:
    try:
        import requests
        url = f"https://api.thetadata.com/v2/quote?symbol=AAPL&api_key={theta_key}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"   ✓ ThetaData API Working")
        else:
            print(f"   ✗ ThetaData API Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ ThetaData Connection Failed: {e}")
else:
    print("   ⚠ ThetaData API key not set, skipping test")

# Check MCP server processes
print("\n[4/4] Checking MCP Server Processes...")
import subprocess
try:
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )
    mcp_procs = [line for line in result.stdout.split("\n") if "mcp" in line.lower()]
    if mcp_procs:
        print(f"   ✓ Found {len(mcp_procs)} MCP-related processes")
        for proc in mcp_procs[:3]:  # Show first 3
            print(f"     {proc[:80]}")
    else:
        print("   ⚠ No MCP processes found")
except Exception as e:
    print(f"   ✗ Process check failed: {e}")

print("\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)
```

Run it:
```bash
python diagnose_mcp.py
```

## 4. Common Fixes

### Fix 1: IBKR Gateway Not Running

```bash
# Start IBKR Gateway
# On Linux/Mac with IBC:
~/ibc/scripts/ibcstart.sh

# Or manually start TWS/Gateway desktop application
```

### Fix 2: Port Conflicts

```bash
# Check if port 4002 is in use
netstat -an | grep 4002

# Or use lsof
lsof -i :4002
```

### Fix 3: MCP Server Not Started

```bash
# Check Claude Desktop MCP configuration
cat ~/.config/Claude/claude_desktop_config.json

# Restart Claude Desktop to reload MCP servers
```

### Fix 4: API Key Not Set

```bash
# Set in .env file
echo "THETADATA_API_KEY=your_key_here" >> .env

# Or export in shell
export THETADATA_API_KEY="your_key_here"
```

## 5. Next Steps After Fix

Once MCP servers are working:

1. **Test Basic Calls**
   ```python
   # In Claude Code session
   account = mcp__ibkr__get_account()
   print(account)

   quotes = mcp__ThetaData__stock_snapshot_quote(symbol=["AAPL"])
   print(quotes)
   ```

2. **Run Commander Workflow**
   ```bash
   # See INTEGRATION_GUIDE.md for full workflow
   # Test each phase: SENSE → THINK → DECIDE → ACT
   ```

3. **Start Paper Trading**
   ```bash
   # Once everything works:
   python runtime/main_loop.py
   ```

## 6. Getting Help

If issues persist:

1. Check IBKR MCP logs
2. Check ThetaData MCP logs
3. Verify network connectivity
4. Ensure API keys are valid
5. Test with minimal examples above

---

**Status**: MCP integration code is ready, testing connection issues
