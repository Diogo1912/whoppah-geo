"""
UI rendering helpers for Whoppah GEO Monitor.
"""
from __future__ import annotations

from datetime import date
from typing import Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from data import get_latest_excerpts


# ---------------------------------------------------------------------------
# UI components
# ---------------------------------------------------------------------------


def date_range_selector() -> Tuple[date, date]:
    """Render a two-value date input and return the chosen start & end dates."""

    today = date.today()
    default_start = today.replace(day=1)
    date_range = st.date_input(
        "Select date range",
        value=(default_start, today),
    )
    # Streamlit can return a single date if not used as range; normalise
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if isinstance(date_range, date) else today
    return start_date, end_date


def _plot_whoppah_mentions(df: pd.DataFrame) -> None:
    """Plot Whoppah mentions over time."""
    whoppah_df = df[df["whoppah_mentioned"] == True].copy()
    if whoppah_df.empty:
        st.info("No Whoppah mentions found in the selected date range.")
        return
    
    daily_counts = (
        whoppah_df.groupby(pd.Grouper(key="timestamp", freq="D"))
        .size()
        .reset_index()
    )
    daily_counts.columns = ["timestamp", "mentions"]

    fig = px.line(
        daily_counts,
        x="timestamp",
        y="mentions",
        title="Whoppah Mentions Over Time",
        markers=True,
    )
    fig.update_traces(line_color="#1f77b4")
    st.plotly_chart(fig, use_container_width=True)


def _plot_sentiment(df: pd.DataFrame) -> None:
    """Plot sentiment breakdown for Whoppah mentions."""
    whoppah_df = df[df["whoppah_mentioned"] == True].copy()
    if whoppah_df.empty:
        st.info("No Whoppah mentions found for sentiment analysis.")
        return
        
    sentiment_counts = whoppah_df.groupby("sentiment").size().reset_index()
    sentiment_counts.columns = ["sentiment", "count"]

    fig = px.bar(
        sentiment_counts,
        x="sentiment",
        y="count",
        title="Whoppah Mention Sentiment Breakdown",
        color="sentiment",
        color_discrete_map={"Positive": "#2ecc71", "Negative": "#e74c3c", "Neutral": "#95a5a6"}
    )
    st.plotly_chart(fig, use_container_width=True)


def _plot_context_categories(df: pd.DataFrame) -> None:
    """Plot context categories for Whoppah mentions."""
    whoppah_df = df[df["whoppah_mentioned"] == True].copy()
    if whoppah_df.empty:
        st.info("No Whoppah mentions found for context analysis.")
        return
        
    context_counts = whoppah_df.groupby("context_category").size().reset_index()
    context_counts.columns = ["context_category", "count"]

    fig = px.pie(
        context_counts,
        values="count",
        names="context_category",
        title="Whoppah Mention Context Categories",
    )
    st.plotly_chart(fig, use_container_width=True)


def display_charts(df: pd.DataFrame) -> None:
    """Render the primary charts given a DataFrame of results."""

    if df.empty:
        st.info("No data available for the selected date range.")
        return

    col1, col2 = st.columns(2)
    
    with col1:
        _plot_whoppah_mentions(df)
        _plot_sentiment(df)
    
    with col2:
        _plot_context_categories(df)
        
        # Show some key metrics
        whoppah_df = df[df["whoppah_mentioned"] == True]
        st.metric("Total Whoppah Mentions", len(whoppah_df))
        if not whoppah_df.empty:
            mention_rate = (len(whoppah_df) / len(df)) * 100
            st.metric("Mention Rate", f"{mention_rate:.1f}%")
            
            positive_rate = (len(whoppah_df[whoppah_df["sentiment"] == "Positive"]) / len(whoppah_df)) * 100
            st.metric("Positive Sentiment Rate", f"{positive_rate:.1f}%")


def display_latest_excerpts(limit: int = 10) -> None:
    """Show the latest excerpts in a Streamlit table, focusing on Whoppah mentions."""

    st.subheader(f"Latest {limit} Query Results")
    latest_df = get_latest_excerpts(limit=limit)
    
    if latest_df.empty:
        st.info("No data available yet. Click 'Run Now' to collect some data!")
        return
    
    # Add a column to highlight Whoppah mentions
    if "whoppah_mentioned" in latest_df.columns:
        latest_df["Has Whoppah"] = latest_df["whoppah_mentioned"].apply(lambda x: "✅" if x else "❌")
    
    # Display with better formatting
    st.dataframe(
        latest_df,
        use_container_width=True,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Timestamp", format="DD/MM/YY HH:mm"),
            "query": st.column_config.TextColumn("Query", width="medium"),
            "sentiment": st.column_config.TextColumn("Sentiment", width="small"),
            "context_category": st.column_config.TextColumn("Context", width="small"),
            "excerpt": st.column_config.TextColumn("Response Excerpt", width="large"),
            "Has Whoppah": st.column_config.TextColumn("Whoppah?", width="small"),
        }
    ) 