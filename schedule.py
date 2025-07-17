"""
Scheduling and LLM interaction for Whoppah GEO Monitor.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Tuple

import openai
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from pytz import timezone

from data import add_result

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

T_ZONE = timezone("Europe/Amsterdam")
GPT_MODEL = "gpt-4o-mini"  # You can switch to gpt-4o or gpt-4-turbo when available

# API Key handling - checks multiple sources
def get_api_key() -> str:
    """Get OpenAI API key from environment variables or .env file."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it as an environment variable "
            "or add it to your .env file."
        )
    return api_key

QUERIES: List[str] = [
    # Whoppah-specific queries (guaranteed mentions)
    "What is Whoppah and how does it work?",
    "Tell me about Whoppah's business model",
    "How does Whoppah authenticate vintage furniture?",
    "What are the benefits of using Whoppah?",
    "Is Whoppah a reliable platform for buying vintage furniture?",
    "How does Whoppah compare to other vintage furniture platforms?",
    "What makes Whoppah different from traditional furniture stores?",
    "Can you explain Whoppah's curation process?",
    "What types of furniture can I find on Whoppah?",
    "How does Whoppah ensure quality of vintage pieces?",
    
    # General marketplace queries
    "Where can I buy secondhand designer furniture?",
    "What are the best platforms for vintage furniture?",
    "How to sell luxury furniture online?",
    "Best online marketplaces for antique furniture",
    "Where to find mid-century modern furniture online",
    
    # Specific furniture categories
    "Where can I buy vintage designer chairs?",
    "Best places to find antique dining tables",
    "Online platforms for designer lighting",
    "Where to buy vintage art and decor",
    "Best sites for luxury home accessories",
    
    # Regional and European focus
    "European vintage furniture marketplaces",
    "Where to buy antique furniture in Europe",
    "Best Dutch furniture marketplaces",
    "Vintage furniture shopping in Netherlands",
    "European design furniture platforms",
    
    # Sustainability and circular economy
    "Sustainable furniture shopping platforms",
    "Circular economy furniture marketplaces",
    "Eco-friendly vintage furniture stores",
    "Second-hand designer furniture benefits",
    "Sustainable home decor shopping",
    
    # Investment and collecting
    "Investing in vintage designer furniture",
    "How to authenticate vintage furniture online",
    "Best platforms for furniture collectors",
    "Designer furniture resale value",
    "Vintage furniture investment guide",
    
    # Comparison and alternatives
    "Alternatives to traditional furniture stores",
    "Online vs offline vintage furniture shopping",
    "Curated vs marketplace furniture platforms",
    "Premium vs budget vintage furniture sites",
    "Auction vs marketplace furniture buying",
    
    # Whoppah context-specific queries
    "How does Whoppah handle shipping and delivery?",
    "What is Whoppah's return policy?",
    "Can I trust buying expensive furniture from Whoppah?",
    "How does Whoppah price vintage furniture?",
    "What countries does Whoppah operate in?",
]

SUPERLATIVES = {"best", "great", "excellent", "amazing", "top", "superior"}

# Validate API key availability at startup
try:
    get_api_key()
    logger.info("OpenAI API key loaded successfully.")
except ValueError as e:
    logger.warning(f"API key issue: {e}")


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------


def _get_client() -> openai.OpenAI:
    """Create and return an OpenAI client instance."""

    return openai.OpenAI(api_key=get_api_key())


def call_llm(prompt: str) -> str:
    """Call GPT model and return the response content."""

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512,
        )
        content = response.choices[0].message.content
        return content or ""
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("OpenAI API call failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------


def analyze_response(text: str) -> Tuple[bool, str, str]:
    """Return (whoppah_mentioned, context_category, sentiment)."""

    lower = text.lower()
    whoppah = "whoppah" in lower
    
    # Categorize the context in which Whoppah appears
    context_category = "General"
    if whoppah:
        if any(word in lower for word in ["recommend", "suggest", "best", "top", "great"]):
            context_category = "Recommendation"
        elif any(word in lower for word in ["buy", "purchase", "shop", "find"]):
            context_category = "Shopping"
        elif any(word in lower for word in ["sell", "selling", "marketplace", "platform"]):
            context_category = "Selling"
        elif any(word in lower for word in ["vintage", "antique", "designer", "luxury"]):
            context_category = "Premium"
        elif any(word in lower for word in ["sustainable", "circular", "eco", "second-hand"]):
            context_category = "Sustainability"
        elif any(word in lower for word in ["invest", "value", "authentic", "collector"]):
            context_category = "Investment"

    # Determine sentiment based on context
    sentiment = "Neutral"
    if whoppah:
        if any(word in lower for word in SUPERLATIVES):
            sentiment = "Positive"
        elif any(word in lower for word in ["problem", "issue", "bad", "poor", "difficult"]):
            sentiment = "Negative"
        elif any(word in lower for word in ["good", "nice", "decent", "okay"]):
            sentiment = "Positive"

    return whoppah, context_category, sentiment


# ---------------------------------------------------------------------------
# Core job
# ---------------------------------------------------------------------------


def run_queries() -> None:
    """Run all configured queries and store the results."""

    logger.info("Starting query run (%d queries)", len(QUERIES))
    for query in QUERIES:
        try:
            response_text = call_llm(query)
        except Exception:  # Already logged
            continue

        whoppah, context_category, sentiment = analyze_response(response_text)
        excerpt = response_text[:200]

        add_result(
            timestamp=datetime.now(T_ZONE),
            query=query,
            whoppah_mentioned=whoppah,
            chairish_mentioned=False,  # No longer tracking Chairish
            context_category=context_category,
            sentiment=sentiment,
            excerpt=excerpt,
            full_response=response_text,
        )

    logger.info("Query run finished.")


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """Return a running BackgroundScheduler singleton."""

    global _scheduler  # pylint: disable=global-statement
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone=T_ZONE)
        trigger = CronTrigger(hour=9, minute=0, timezone=T_ZONE)
        _scheduler.add_job(run_queries, trigger, id="daily-whoppah-run", replace_existing=True)
        _scheduler.start()
        logger.info("BackgroundScheduler started with daily job at 09:00 Europe/Amsterdam.")
    return _scheduler 