"""
Live news fetcher for the European Gas Thesis Tracker.
Pulls headlines from Google News RSS feeds, grouped by thesis-relevant
categories (Gas/LNG, Geopolitical, Equities, Oil). Deduplicates and
filters to the last 48 hours by default.
"""

import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import pandas as pd

try:
    import feedparser
except ImportError:
    feedparser = None


def fetch_google_news_rss(query, max_results=5):
    """Fetch news headlines from Google News RSS for a search query."""
    if feedparser is None:
        raise ImportError("feedparser is required: pip install feedparser")

    url = (
        f"https://news.google.com/rss/search?"
        f"q={urllib.parse.quote(query)}&hl=en&gl=US&ceid=US:en"
    )
    feed = feedparser.parse(url)
    results = []

    for entry in feed.entries[:max_results]:
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        source = "Unknown"
        if hasattr(entry, "source") and hasattr(entry.source, "title"):
            source = entry.source.title

        results.append({
            "title": entry.get("title", "N/A"),
            "source": source,
            "published": published,
            "link": entry.get("link", ""),
            "query": query,
        })

    return results


def fetch_all_news(queries_dict, max_per_query=5):
    """
    Fetch news for all categories and queries.

    Parameters
    ----------
    queries_dict : dict
        Mapping of category -> list of search queries.
        e.g. {"Gas/LNG": ["TTF gas price", ...], "Oil": [...]}
    max_per_query : int
        Max headlines per individual query.

    Returns
    -------
    pd.DataFrame with columns: title, source, published, link, category, query
    """
    all_results = []

    for category, queries in queries_dict.items():
        for query in queries:
            try:
                items = fetch_google_news_rss(query, max_results=max_per_query)
                for item in items:
                    item["category"] = category
                all_results.extend(items)
            except Exception as e:
                print(f"  Warning: failed to fetch '{query}': {e}")
            time.sleep(0.3)  # polite rate limiting

    if not all_results:
        return pd.DataFrame(columns=["title", "source", "published", "link", "category", "query"])

    return pd.DataFrame(all_results)


def categorize_and_deduplicate(df, hours=48):
    """
    Deduplicate headlines and filter to the last N hours.

    Parameters
    ----------
    df : pd.DataFrame
        Raw news DataFrame from fetch_all_news.
    hours : int
        Only keep headlines from the last N hours.

    Returns
    -------
    pd.DataFrame, deduplicated and sorted by published date descending.
    """
    if df.empty:
        return df

    # Deduplicate by normalised headline
    df["title_norm"] = df["title"].str.lower().str.strip()
    df = df.drop_duplicates(subset="title_norm", keep="first")
    df = df.drop(columns=["title_norm"])

    # Filter to last N hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    if df["published"].notna().any():
        df = df[df["published"].isna() | (df["published"] >= cutoff)]

    # Sort by date descending
    df = df.sort_values("published", ascending=False, na_position="last")

    return df.reset_index(drop=True)


def format_news_table(df):
    """Format news DataFrame as a readable CLI table."""
    if df.empty:
        return "No recent news found."

    lines = []
    for category in df["category"].unique():
        lines.append(f"\n{'=' * 60}")
        lines.append(f"  {category}")
        lines.append(f"{'=' * 60}")

        cat_df = df[df["category"] == category]
        for _, row in cat_df.iterrows():
            date_str = row["published"].strftime("%b %d %H:%M") if pd.notna(row["published"]) else "Unknown"
            lines.append(f"  [{date_str}] {row['title']}")
            lines.append(f"             Source: {row['source']}")

    lines.append(f"\nLast refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)
