"""
KUYAN - Monthly Net Worth Tracker
Reminder Page Module - Calendar reminder widget
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from components import render_calendar_widget


def page_reminder():
    """
    Render the reminder page for monthly balance update reminders.
    """
    st.title("🔔 Reminder")
    st.markdown("Set up calendar invites to remind you to update monthly balances")
    
    render_calendar_widget()
