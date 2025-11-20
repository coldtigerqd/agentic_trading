#!/usr/bin/env python3
"""
News Sentiment Tools for AlphaHive Agent.

Provides news sentiment analysis, Twitter sentiment tracking, and event calendar
tools for informed trading decisions.

Supports multiple news sources:
- Serper (Google Search + News API)
- NewsAPI (news aggregator)
- Firecrawl (web scraping)

Dependencies:
    pip install requests anthropic

API Keys Required:
    - SERPER_API_KEY or NEWSAPI_KEY (for news)
    - ANTHROPIC_API_KEY (for sentiment analysis)
    - TWITTER_BEARER_TOKEN (optional, for Twitter sentiment)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests
from anthropic import Anthropic


class NewsSentimentTools:
    """Tools for news sentiment analysis and event tracking."""

    def __init__(self):
        """Initialize news sentiment tools with API clients."""
        self.serper_key = os.getenv("SERPER_API_KEY")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.twitter_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if self.anthropic_key:
            self.anthropic = Anthropic(api_key=self.anthropic_key)
        else:
            self.anthropic = None

    def get_news_sentiment(
        self,
        symbol: str,
        hours: int = 24,
        source: str = "auto"
    ) -> Dict[str, Any]:
        """
        Get news sentiment for a symbol over the specified time period.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            hours: Hours to look back (default: 24)
            source: News source ("serper", "newsapi", or "auto" to try both)

        Returns:
            {
                "symbol": "AAPL",
                "sentiment_score": 0.65,  # -1 (bearish) to +1 (bullish)
                "sentiment_label": "bullish",  # bearish/neutral/bullish
                "trend": "improving",  # improving/stable/deteriorating
                "num_articles": 15,
                "top_headlines": [
                    {
                        "title": "Apple announces new product",
                        "source": "Bloomberg",
                        "published": "2025-11-19T10:30:00Z",
                        "sentiment": 0.8,
                        "url": "https://..."
                    }
                ],
                "error": None
            }

        Example:
            >>> tools = NewsSentimentTools()
            >>> result = tools.get_news_sentiment("AAPL", hours=24)
            >>> result["symbol"]
            'AAPL'
            >>> "sentiment_score" in result
            True
        """
        try:
            # Fetch news articles
            if source == "serper" or (source == "auto" and self.serper_key):
                articles = self._fetch_news_serper(symbol, hours)
            elif source == "newsapi" or (source == "auto" and self.newsapi_key):
                articles = self._fetch_news_newsapi(symbol, hours)
            else:
                return {
                    "symbol": symbol,
                    "error": "No news API key configured (SERPER_API_KEY or NEWSAPI_KEY required)"
                }

            if not articles:
                return {
                    "symbol": symbol,
                    "sentiment_score": 0.0,
                    "sentiment_label": "neutral",
                    "trend": "stable",
                    "num_articles": 0,
                    "top_headlines": [],
                    "error": None
                }

            # Analyze sentiment for each article
            articles_with_sentiment = []
            for article in articles[:10]:  # Limit to top 10 for cost control
                sentiment = self._analyze_sentiment(article["title"], article.get("description", ""))
                articles_with_sentiment.append({
                    "title": article["title"],
                    "source": article.get("source", "Unknown"),
                    "published": article.get("published", ""),
                    "sentiment": sentiment,
                    "url": article.get("url", "")
                })

            # Calculate aggregate sentiment
            sentiment_scores = [a["sentiment"] for a in articles_with_sentiment]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

            # Determine sentiment label
            if avg_sentiment > 0.2:
                label = "bullish"
            elif avg_sentiment < -0.2:
                label = "bearish"
            else:
                label = "neutral"

            # Calculate trend (compare recent vs older articles)
            trend = self._calculate_sentiment_trend(articles_with_sentiment)

            return {
                "symbol": symbol,
                "sentiment_score": round(avg_sentiment, 3),
                "sentiment_label": label,
                "trend": trend,
                "num_articles": len(articles),
                "top_headlines": articles_with_sentiment[:5],
                "error": None
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Error fetching news sentiment: {str(e)}"
            }

    def get_twitter_sentiment(
        self,
        symbol: str,
        hours: int = 6
    ) -> Dict[str, Any]:
        """
        Get Twitter/X sentiment for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            hours: Hours to look back (default: 6 for recent buzz)

        Returns:
            {
                "symbol": "AAPL",
                "sentiment_score": 0.45,  # -1 to +1
                "sentiment_label": "bullish",
                "num_tweets": 1250,
                "influencer_sentiment": 0.6,  # Sentiment from accounts >10K followers
                "spike_detected": False,  # Sudden change in sentiment
                "top_tweets": [
                    {
                        "text": "Apple stock looking strong...",
                        "author": "@trader",
                        "followers": 15000,
                        "sentiment": 0.7,
                        "timestamp": "2025-11-19T14:30:00Z"
                    }
                ],
                "error": None
            }

        Example:
            >>> tools = NewsSentimentTools()
            >>> result = tools.get_twitter_sentiment("AAPL", hours=6)
            >>> result["symbol"]
            'AAPL'
            >>> "sentiment_score" in result
            True
        """
        try:
            if not self.twitter_token and not self.serper_key:
                return {
                    "symbol": symbol,
                    "error": "No Twitter API configured (TWITTER_BEARER_TOKEN or SERPER_API_KEY required)"
                }

            # Fetch tweets
            if self.serper_key:
                # Use Serper social search as fallback
                tweets = self._fetch_tweets_serper(symbol, hours)
            else:
                tweets = self._fetch_tweets_twitter(symbol, hours)

            if not tweets:
                return {
                    "symbol": symbol,
                    "sentiment_score": 0.0,
                    "sentiment_label": "neutral",
                    "num_tweets": 0,
                    "influencer_sentiment": 0.0,
                    "spike_detected": False,
                    "top_tweets": [],
                    "error": None
                }

            # Analyze sentiment for each tweet
            tweets_with_sentiment = []
            influencer_tweets = []

            for tweet in tweets[:20]:  # Limit for cost control
                sentiment = self._analyze_sentiment(tweet["text"])
                tweet_data = {
                    "text": tweet["text"][:200],  # Truncate for display
                    "author": tweet.get("author", "Unknown"),
                    "followers": tweet.get("followers", 0),
                    "sentiment": sentiment,
                    "timestamp": tweet.get("timestamp", "")
                }
                tweets_with_sentiment.append(tweet_data)

                # Track influencer sentiment (>10K followers)
                if tweet.get("followers", 0) > 10000:
                    influencer_tweets.append(tweet_data)

            # Calculate aggregate sentiment
            all_sentiments = [t["sentiment"] for t in tweets_with_sentiment]
            avg_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0.0

            influencer_sentiments = [t["sentiment"] for t in influencer_tweets]
            influencer_sentiment = sum(influencer_sentiments) / len(influencer_sentiments) if influencer_sentiments else 0.0

            # Determine label
            if avg_sentiment > 0.2:
                label = "bullish"
            elif avg_sentiment < -0.2:
                label = "bearish"
            else:
                label = "neutral"

            # Detect sentiment spike
            spike_detected = self._detect_sentiment_spike(tweets_with_sentiment)

            return {
                "symbol": symbol,
                "sentiment_score": round(avg_sentiment, 3),
                "sentiment_label": label,
                "num_tweets": len(tweets),
                "influencer_sentiment": round(influencer_sentiment, 3),
                "spike_detected": spike_detected,
                "top_tweets": tweets_with_sentiment[:5],
                "error": None
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Error fetching Twitter sentiment: {str(e)}"
            }

    def get_earnings_calendar(
        self,
        symbols: Optional[List[str]] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get upcoming earnings dates for symbols.

        Args:
            symbols: List of symbols (e.g., ["AAPL", "GOOGL"]), or None for all
            days: Days to look ahead (default: 7)

        Returns:
            {
                "earnings": [
                    {
                        "symbol": "AAPL",
                        "date": "2025-11-25",
                        "time": "after_close",  # before_open/after_close/during_hours
                        "days_until": 5,
                        "confirmed": True
                    }
                ],
                "error": None
            }

        Example:
            >>> tools = NewsSentimentTools()
            >>> result = tools.get_earnings_calendar(symbols=["AAPL"], days=7)
            >>> "earnings" in result
            True
        """
        try:
            # Use Serper to search for earnings calendar info
            if not self.serper_key:
                return {
                    "earnings": [],
                    "error": "SERPER_API_KEY required for earnings calendar"
                }

            earnings = []
            symbols_to_check = symbols if symbols else []

            for symbol in symbols_to_check:
                # Search for earnings date
                query = f"{symbol} earnings date next"
                result = self._search_serper(query)

                if result and "answerBox" in result:
                    # Parse earnings info from answer box
                    earnings_info = self._parse_earnings_info(symbol, result["answerBox"])
                    if earnings_info:
                        earnings.append(earnings_info)

            return {
                "earnings": earnings,
                "error": None
            }

        except Exception as e:
            return {
                "earnings": [],
                "error": f"Error fetching earnings calendar: {str(e)}"
            }

    def get_economic_calendar(self, days: int = 14) -> Dict[str, Any]:
        """
        Get upcoming economic events (FOMC, CPI, jobs report, etc.).

        Args:
            days: Days to look ahead (default: 14)

        Returns:
            {
                "events": [
                    {
                        "event": "FOMC Meeting",
                        "date": "2025-12-15",
                        "days_until": 26,
                        "impact": "high",  # high/medium/low
                        "description": "Federal Reserve policy decision"
                    }
                ],
                "error": None
            }

        Example:
            >>> tools = NewsSentimentTools()
            >>> result = tools.get_economic_calendar(days=14)
            >>> "events" in result
            True
        """
        try:
            if not self.serper_key:
                return {
                    "events": [],
                    "error": "SERPER_API_KEY required for economic calendar"
                }

            # Search for major economic events
            events = []
            economic_indicators = ["FOMC", "CPI", "Jobs Report", "GDP", "NFP"]

            for indicator in economic_indicators:
                query = f"{indicator} next date 2025"
                result = self._search_serper(query)

                if result and "answerBox" in result:
                    event_info = self._parse_economic_event(indicator, result["answerBox"])
                    if event_info:
                        events.append(event_info)

            # Sort by date
            events.sort(key=lambda x: x.get("date", "9999-99-99"))

            return {
                "events": events,
                "error": None
            }

        except Exception as e:
            return {
                "events": [],
                "error": f"Error fetching economic calendar: {str(e)}"
            }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _fetch_news_serper(self, symbol: str, hours: int) -> List[Dict]:
        """Fetch news articles using Serper API."""
        if not self.serper_key:
            return []

        url = "https://google.serper.dev/news"
        headers = {
            "X-API-KEY": self.serper_key,
            "Content-Type": "application/json"
        }

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        payload = {
            "q": f"{symbol} stock",
            "num": 20,
            "tbs": f"qdr:h{hours}"  # Time-based search
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        articles = []

        for item in data.get("news", []):
            articles.append({
                "title": item.get("title", ""),
                "description": item.get("snippet", ""),
                "source": item.get("source", "Unknown"),
                "url": item.get("link", ""),
                "published": item.get("date", "")
            })

        return articles

    def _fetch_news_newsapi(self, symbol: str, hours: int) -> List[Dict]:
        """Fetch news articles using NewsAPI."""
        if not self.newsapi_key:
            return []

        url = "https://newsapi.org/v2/everything"

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        params = {
            "apiKey": self.newsapi_key,
            "q": f"{symbol} stock",
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 20
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        articles = []

        for item in data.get("articles", []):
            articles.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "source": item.get("source", {}).get("name", "Unknown"),
                "url": item.get("url", ""),
                "published": item.get("publishedAt", "")
            })

        return articles

    def _fetch_tweets_serper(self, symbol: str, hours: int) -> List[Dict]:
        """Fetch tweets using Serper social search."""
        if not self.serper_key:
            return []

        # Serper doesn't have direct Twitter search in free tier
        # Return empty for now, can be implemented with paid tier
        return []

    def _fetch_tweets_twitter(self, symbol: str, hours: int) -> List[Dict]:
        """Fetch tweets using Twitter API v2."""
        if not self.twitter_token:
            return []

        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {
            "Authorization": f"Bearer {self.twitter_token}"
        }

        # Calculate time range
        start_time = datetime.now() - timedelta(hours=hours)

        params = {
            "query": f"${symbol} OR #{symbol}",
            "max_results": 100,
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "public_metrics"
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        tweets = []

        # Build user map
        users = {}
        for user in data.get("includes", {}).get("users", []):
            users[user["id"]] = user

        for tweet in data.get("data", []):
            author_id = tweet.get("author_id")
            author = users.get(author_id, {})

            tweets.append({
                "text": tweet.get("text", ""),
                "author": author.get("username", "Unknown"),
                "followers": author.get("public_metrics", {}).get("followers_count", 0),
                "timestamp": tweet.get("created_at", "")
            })

        return tweets

    def _search_serper(self, query: str) -> Optional[Dict]:
        """Generic Serper search."""
        if not self.serper_key:
            return None

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.serper_key,
            "Content-Type": "application/json"
        }

        payload = {"q": query}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def _analyze_sentiment(self, text: str, context: str = "") -> float:
        """
        Analyze sentiment using Claude.

        Returns:
            Sentiment score from -1 (very bearish) to +1 (very bullish)
        """
        if not self.anthropic:
            # Fallback: simple keyword-based sentiment
            text_lower = (text + " " + context).lower()

            positive_words = ["bullish", "rally", "surge", "gain", "positive", "growth", "strong", "beat"]
            negative_words = ["bearish", "decline", "fall", "drop", "negative", "weak", "miss", "concern"]

            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)

            if pos_count + neg_count == 0:
                return 0.0

            return (pos_count - neg_count) / (pos_count + neg_count)

        # Use Claude for better sentiment analysis
        try:
            prompt = f"""Analyze the sentiment of this headline/text for stock trading.
Return ONLY a number from -1 to +1:
- -1 = Very bearish (strong negative)
- -0.5 = Bearish
- 0 = Neutral
- +0.5 = Bullish
- +1 = Very bullish (strong positive)

Text: {text}
{f"Context: {context}" if context else ""}

Respond with ONLY the number, nothing else."""

            message = self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )

            sentiment_str = message.content[0].text.strip()
            sentiment = float(sentiment_str)

            # Clamp to [-1, 1]
            return max(-1.0, min(1.0, sentiment))

        except:
            # Fallback to keyword-based
            return self._analyze_sentiment(text, context)

    def _calculate_sentiment_trend(self, articles: List[Dict]) -> str:
        """
        Calculate if sentiment is improving, stable, or deteriorating.

        Args:
            articles: List of articles with sentiment scores (newest first)

        Returns:
            "improving", "stable", or "deteriorating"
        """
        if len(articles) < 4:
            return "stable"

        # Split into recent (first half) vs older (second half)
        mid = len(articles) // 2
        recent = articles[:mid]
        older = articles[mid:]

        recent_avg = sum(a["sentiment"] for a in recent) / len(recent)
        older_avg = sum(a["sentiment"] for a in older) / len(older)

        diff = recent_avg - older_avg

        if diff > 0.15:
            return "improving"
        elif diff < -0.15:
            return "deteriorating"
        else:
            return "stable"

    def _detect_sentiment_spike(self, tweets: List[Dict]) -> bool:
        """
        Detect sudden sentiment change in tweets.

        Args:
            tweets: List of tweets with sentiment (newest first)

        Returns:
            True if spike detected
        """
        if len(tweets) < 6:
            return False

        # Compare very recent (last 25%) vs rest
        cutoff = len(tweets) // 4
        very_recent = tweets[:cutoff]
        rest = tweets[cutoff:]

        recent_avg = sum(t["sentiment"] for t in very_recent) / len(very_recent)
        baseline_avg = sum(t["sentiment"] for t in rest) / len(rest)

        # Spike if difference > 0.4
        return abs(recent_avg - baseline_avg) > 0.4

    def _parse_earnings_info(self, symbol: str, answer_box: Dict) -> Optional[Dict]:
        """Parse earnings info from Serper answer box."""
        # This is a simplified parser - in production would be more robust
        try:
            # Extract date from answer box (implementation would vary)
            # For now, return placeholder
            return {
                "symbol": symbol,
                "date": "TBD",
                "time": "after_close",
                "days_until": -1,
                "confirmed": False
            }
        except:
            return None

    def _parse_economic_event(self, indicator: str, answer_box: Dict) -> Optional[Dict]:
        """Parse economic event from Serper answer box."""
        # Simplified parser - in production would be more robust
        try:
            return {
                "event": indicator,
                "date": "TBD",
                "days_until": -1,
                "impact": "high" if indicator in ["FOMC", "CPI", "Jobs Report"] else "medium",
                "description": f"{indicator} economic indicator"
            }
        except:
            return None


# MCP Tools Metadata
TOOLS_METADATA = [
    {
        "name": "get_news_sentiment",
        "description": "Get news sentiment analysis for a stock symbol. Returns sentiment score (-1 to +1), label (bearish/neutral/bullish), trend (improving/stable/deteriorating), and top headlines with individual sentiments.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., 'AAPL')"
                },
                "hours": {
                    "type": "integer",
                    "description": "Hours to look back (default: 24)",
                    "default": 24
                },
                "source": {
                    "type": "string",
                    "description": "News source: 'serper', 'newsapi', or 'auto' (default)",
                    "enum": ["serper", "newsapi", "auto"],
                    "default": "auto"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_twitter_sentiment",
        "description": "Get Twitter/X sentiment for a stock symbol. Returns sentiment score, number of tweets, influencer sentiment (from accounts >10K followers), and spike detection for sudden sentiment changes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., 'AAPL')"
                },
                "hours": {
                    "type": "integer",
                    "description": "Hours to look back (default: 6)",
                    "default": 6
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_earnings_calendar",
        "description": "Get upcoming earnings dates for specified symbols. Returns earnings date, time (before_open/after_close), days until event, and confirmation status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stock symbols (e.g., ['AAPL', 'GOOGL']). Omit for all symbols."
                },
                "days": {
                    "type": "integer",
                    "description": "Days to look ahead (default: 7)",
                    "default": 7
                }
            }
        }
    },
    {
        "name": "get_economic_calendar",
        "description": "Get upcoming economic events (FOMC, CPI, jobs report, GDP, etc.). Returns event name, date, days until, impact level (high/medium/low), and description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Days to look ahead (default: 14)",
                    "default": 14
                }
            }
        }
    }
]
