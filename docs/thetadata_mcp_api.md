# ThetaData MCP API Documentation

**Server URL:** http://localhost:25503/mcp/sse
**Type:** SSE (Server-Sent Events)
**Status:** ✓ Running

## Available Tools

Based on Claude Code environment, the following ThetaData MCP tools are available:

### Real-time/Snapshot Tools

1. **mcp__ThetaData__stock_snapshot_quote**
   - Get real-time quote for a stock
   - Parameters: TBD (need to verify exact schema)
   - Returns: Current bid/ask, last price, volume

2. **mcp__ThetaData__stock_snapshot_ohlc**
   - Get current day's OHLC data
   - Parameters: symbol
   - Returns: Open, High, Low, Close, Volume for current trading session
   - **Use Case:** Can be used for incremental 5-minute updates

3. **mcp__ThetaData__option_list_expirations**
   - List available option expiration dates for a symbol
   - Not needed for stock data caching

4. **mcp__ThetaData__option_list_strikes**
   - List available option strikes for a symbol/expiration
   - Not needed for stock data caching

5. **mcp__ThetaData__option_snapshot_quote**
   - Get real-time option quote
   - Not needed for stock data caching

### Historical Data Tools

**Status:** Need to verify if ThetaData MCP provides historical OHLC endpoints.

**Expected Functionality:**
- Fetch historical OHLC bars for a date range
- Support for different intervals (1min, 5min, 15min, 1h, daily)
- Pagination for large date ranges

**Workaround if not available:**
- Use `stock_snapshot_ohlc` for incremental updates every 5 minutes
- Build historical cache over time (start with recent data, backfill gradually)
- Consider direct ThetaData REST API if MCP doesn't expose historical data

## Implementation Strategy

### For Incremental Updates (Current Session)
Use `mcp__ThetaData__stock_snapshot_ohlc` every 5 minutes during trading hours.

**Pseudocode:**
```python
async def fetch_latest_bar(symbol):
    result = await call_mcp_tool(
        "mcp__ThetaData__stock_snapshot_ohlc",
        {"symbol": symbol}
    )
    return OHLCVBar(
        symbol=symbol,
        timestamp=current_5min_interval(),
        open=result.open,
        high=result.high,
        low=result.low,
        close=result.close,
        volume=result.volume
    )
```

### For Historical Backfill

**Option 1:** If historical MCP tools exist
- Use historical OHLC endpoint with date range
- Fetch in chunks (e.g., 1 month at a time) to respect rate limits

**Option 2:** If no historical MCP tools
- Start with recent data only (last 30 days)
- Gradually build historical cache through daily incremental updates
- Consider direct ThetaData REST API integration for initial backfill

## Rate Limits

**ThetaData API Limits:**
- Standard plan: TBD requests/minute
- Need to implement exponential backoff for 429 responses

## Testing

**Integration Test Checklist:**
- [ ] Verify MCP server connection
- [ ] Test snapshot OHLC tool with real symbol
- [ ] Verify response format and data structure
- [ ] Test error handling (invalid symbol, API failure)
- [ ] Measure response latency

## Next Steps

1. Test `stock_snapshot_ohlc` with real data
2. Document exact request/response format
3. Implement fetcher with current session updates
4. Investigate historical data options for backfill
