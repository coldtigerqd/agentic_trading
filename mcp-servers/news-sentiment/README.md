# News Sentiment MCP Server

MCP server providing news sentiment analysis, Twitter sentiment tracking, and event calendar tools for the AlphaHive autonomous trading agent.

## Features

### 1. News Sentiment Analysis
- Fetch recent news articles for any stock symbol
- LLM-powered sentiment scoring (-1 to +1 scale)
- Sentiment trend detection (improving/stable/deteriorating)
- Top headlines with individual sentiment scores
- Support for multiple news sources (Serper, NewsAPI)

### 2. Twitter/X Sentiment Tracking
- Real-time Twitter sentiment for stock symbols
- Influencer sentiment (accounts >10K followers)
- Sentiment spike detection (sudden changes)
- High-volume tweet aggregation

### 3. Event Calendar
- Upcoming earnings dates for symbols
- Economic calendar (FOMC, CPI, jobs reports, GDP)
- Days-until-event calculations for trade timing
- Impact level classification (high/medium/low)

## Installation

### 1. Install Dependencies

```bash
cd mcp-servers/news-sentiment
pip install requests anthropic
```

### 2. Set API Keys

Required environment variables:

```bash
# For news sentiment (choose one)
export SERPER_API_KEY="your-serper-key"        # Recommended - Google News API
# OR
export NEWSAPI_KEY="your-newsapi-key"          # Alternative news source

# For sentiment analysis (required)
export ANTHROPIC_API_KEY="your-anthropic-key"  # Claude for sentiment scoring

# For Twitter sentiment (optional)
export TWITTER_BEARER_TOKEN="your-twitter-token"
```

#### Getting API Keys

**Serper API** (Recommended):
- Visit: https://serper.dev
- Free tier: 2,500 searches/month
- Best for news + social search

**NewsAPI**:
- Visit: https://newsapi.org
- Free tier: 100 requests/day
- Good for news articles only

**Anthropic API**:
- Visit: https://console.anthropic.com
- Required for LLM-powered sentiment analysis
- Uses Claude 3.5 Haiku (cost-efficient)

**Twitter API**:
- Visit: https://developer.twitter.com
- Required for direct Twitter sentiment
- Can use Serper as fallback

### 3. Configure MCP Client

Add to your MCP client configuration (e.g., Claude Code settings):

```json
{
  "mcpServers": {
    "news-sentiment": {
      "command": "python",
      "args": ["/path/to/mcp-servers/news-sentiment/server.py"],
      "env": {
        "SERPER_API_KEY": "your-key",
        "ANTHROPIC_API_KEY": "your-key"
      }
    }
  }
}
```

## Usage

### Tool 1: get_news_sentiment

Get news sentiment for a stock symbol.

```python
# Agent call example
result = mcp__news_sentiment__get_news_sentiment(
    symbol="AAPL",
    hours=24,
    source="auto"  # "serper", "newsapi", or "auto"
)
```

**Response**:
```json
{
  "symbol": "AAPL",
  "sentiment_score": 0.65,
  "sentiment_label": "bullish",
  "trend": "improving",
  "num_articles": 15,
  "top_headlines": [
    {
      "title": "Apple announces new product line",
      "source": "Bloomberg",
      "published": "2025-11-19T10:30:00Z",
      "sentiment": 0.8,
      "url": "https://..."
    }
  ],
  "error": null
}
```

**Interpretation**:
- `sentiment_score`: -1 (very bearish) to +1 (very bullish)
- `sentiment_label`: "bearish" / "neutral" / "bullish"
- `trend`: "improving" / "stable" / "deteriorating"

**Use Cases**:
- Avoid trading when news sentiment is very negative
- Increase position size when sentiment is bullish + improving
- Close positions when trend shifts to deteriorating

### Tool 2: get_twitter_sentiment

Get Twitter/X sentiment for a stock symbol.

```python
# Agent call example
result = mcp__news_sentiment__get_twitter_sentiment(
    symbol="AAPL",
    hours=6  # Recent buzz window
)
```

**Response**:
```json
{
  "symbol": "AAPL",
  "sentiment_score": 0.45,
  "sentiment_label": "bullish",
  "num_tweets": 1250,
  "influencer_sentiment": 0.6,
  "spike_detected": false,
  "top_tweets": [
    {
      "text": "Apple stock looking strong...",
      "author": "@trader",
      "followers": 15000,
      "sentiment": 0.7,
      "timestamp": "2025-11-19T14:30:00Z"
    }
  ],
  "error": null
}
```

**Interpretation**:
- `influencer_sentiment`: Sentiment from high-follower accounts (>10K)
- `spike_detected`: True if sudden sentiment change detected

**Use Cases**:
- Detect retail sentiment shifts before price moves
- Avoid trading against strong influencer consensus
- Exit positions when sentiment spike detected (potential reversal)

### Tool 3: get_earnings_calendar

Get upcoming earnings dates for symbols.

```python
# Agent call example
result = mcp__news_sentiment__get_earnings_calendar(
    symbols=["AAPL", "GOOGL", "MSFT"],
    days=7
)
```

**Response**:
```json
{
  "earnings": [
    {
      "symbol": "AAPL",
      "date": "2025-11-25",
      "time": "after_close",
      "days_until": 5,
      "confirmed": true
    }
  ],
  "error": null
}
```

**Use Cases**:
- Avoid opening new positions 1-2 days before earnings
- Close positions before earnings to avoid IV crush
- Increase IV capture trades (iron condors) before earnings

### Tool 4: get_economic_calendar

Get upcoming economic events.

```python
# Agent call example
result = mcp__news_sentiment__get_economic_calendar(days=14)
```

**Response**:
```json
{
  "events": [
    {
      "event": "FOMC Meeting",
      "date": "2025-12-15",
      "days_until": 26,
      "impact": "high",
      "description": "Federal Reserve policy decision"
    },
    {
      "event": "CPI",
      "date": "2025-12-10",
      "days_until": 21,
      "impact": "high",
      "description": "Consumer Price Index"
    }
  ],
  "error": null
}
```

**Use Cases**:
- Reduce position sizes before high-impact events (FOMC, CPI)
- Avoid selling options expiring during major events
- Increase hedging before potentially volatile periods

## Integration with AlphaHive Agent

### Phase 10.5: Sentiment Integration

The agent integrates sentiment into its Reasoning phase:

```python
# During Reasoning phase, agent checks sentiment
news_sentiment = mcp__news_sentiment__get_news_sentiment(
    symbol=opportunity["symbol"],
    hours=24
)

twitter_sentiment = mcp__news_sentiment__get_twitter_sentiment(
    symbol=opportunity["symbol"],
    hours=6
)

earnings_calendar = mcp__news_sentiment__get_earnings_calendar(
    symbols=[opportunity["symbol"]],
    days=7
)

# Decision logic
if news_sentiment["sentiment_label"] == "bearish" and news_sentiment["trend"] == "deteriorating":
    # Reduce position size or skip trade
    print("⚠ Negative news sentiment - reducing position size by 50%")

if twitter_sentiment["spike_detected"]:
    # Potential reversal signal
    print("⚠ Twitter sentiment spike detected - consider waiting")

if earnings_calendar["earnings"] and earnings_calendar["earnings"][0]["days_until"] < 3:
    # Earnings risk
    print("⚠ Earnings in <3 days - skipping trade or using shorter DTE")
```

### Sentiment Scoring Guidelines

**News Sentiment**:
- `> 0.5`: Very bullish - consider larger positions
- `0.2 to 0.5`: Bullish - normal position sizing
- `-0.2 to 0.2`: Neutral - proceed with caution
- `-0.5 to -0.2`: Bearish - reduce size or skip
- `< -0.5`: Very bearish - avoid or consider bearish plays

**Twitter Sentiment**:
- `influencer_sentiment > 0.6`: Strong bullish consensus
- `influencer_sentiment < -0.4`: Strong bearish consensus
- `spike_detected = true`: Potential sentiment reversal

**Earnings Calendar**:
- `days_until <= 1`: High risk - avoid new trades
- `days_until 2-3`: Moderate risk - use caution
- `days_until >= 4`: Normal risk - proceed

**Economic Calendar**:
- `impact = "high" and days_until <= 2`: Reduce positions
- `impact = "high" and days_until 3-5`: Increase hedging
- `impact = "medium"`: Monitor but proceed normally

## Testing

```bash
# Test news sentiment
python -c "
from tools import NewsSentimentTools
tools = NewsSentimentTools()
result = tools.get_news_sentiment('AAPL', hours=24)
print(result)
"

# Test server (requires MCP client)
python server.py
```

## Architecture

```
news-sentiment/
├── server.py           # MCP protocol handler
├── tools.py            # Tool implementations
├── __init__.py         # Package initialization
└── README.md           # Documentation
```

## API Cost Optimization

**Serper API**:
- Cost: Free tier (2,500 searches/month)
- Usage: ~10 calls/day for news + earnings
- Estimate: Well within free tier

**Anthropic API** (Claude 3.5 Haiku):
- Cost: $0.80/MTok input, $4.00/MTok output
- Usage: ~50 tokens/article × 10 articles/day × 30 days = 15K tokens/month
- Estimate: ~$0.01-0.05/month

**Twitter API**:
- Cost: Free tier (10K tweets/month read)
- Usage: ~100 tweets/call × 10 calls/day = 30K tweets/month
- Note: May require Basic tier ($100/month) - use Serper fallback

**Total Monthly Cost**: <$1 (using free tiers + Serper fallback)

## Error Handling

All tools include error handling and return errors in the response:

```json
{
  "symbol": "AAPL",
  "error": "No news API key configured (SERPER_API_KEY or NEWSAPI_KEY required)"
}
```

The agent should check for `error` field and handle gracefully:

```python
if result.get("error"):
    print(f"⚠ Sentiment unavailable: {result['error']}")
    # Proceed without sentiment data
else:
    # Use sentiment data
    sentiment_score = result["sentiment_score"]
```

## Future Enhancements

- [ ] Real-time news streaming (WebSocket)
- [ ] Sector-wide sentiment aggregation
- [ ] Sentiment backtest correlation analysis
- [ ] Custom sentiment models (fine-tuned)
- [ ] Reddit sentiment integration
- [ ] StockTwits sentiment integration
- [ ] Insider trading calendar
- [ ] FDA approval calendar (pharma stocks)

## License

Part of the AlphaHive autonomous trading agent project.
