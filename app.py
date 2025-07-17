"""
Streamlit entrypoint for Whoppah GEO Monitor.
"""
from __future__ import annotations

import streamlit as st

from data import init_db, get_results
from schedule import get_scheduler, run_queries
import ui


def main() -> None:
    """Launch the Streamlit dashboard."""
    st.set_page_config(page_title="Whoppah GEO Monitor", layout="wide")
    st.title("Whoppah GEO Monitor")
    st.markdown("**Comprehensive AI-powered tracking of Whoppah mentions across diverse query contexts**")

    # Initialize the database and background scheduler once per session
    init_db()
    get_scheduler()

    # Manual trigger for an immediate run
    if st.button("Run Now"):
        with st.spinner("Running queries …"):
            run_queries()
        st.success("Queries completed and data stored.")

    # Date-range selector and data visualisation
    start_date, end_date = ui.date_range_selector()
    df = get_results(start=start_date, end=end_date)
    ui.display_charts(df)
    ui.display_latest_excerpts()

    st.caption("Data updates automatically every day at 09:00 Europe/Amsterdam time.")


if __name__ == "__main__":
    main() 