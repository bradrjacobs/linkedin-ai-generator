import streamlit as st
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Page configuration
st.set_page_config(page_title="Thought Leadership Strategy", page_icon="📊", layout="wide")

st.title("Thought Leadership Strategy")
st.markdown("""
This page helps you define Mylance's thought leadership strategy. This strategy will guide the content generation for all users.
""")

# Strategy input
with st.form("thought_leadership_form"):
    strategy = st.text_area(
        "Define Mylance's Thought Leadership Strategy",
        value=st.session_state.thought_leadership_strategy,
        height=300,
        help="Enter the overall thought leadership strategy that will guide content generation for all users."
    )
    
    submit = st.form_submit_button("Save Strategy")
    
    if submit and strategy:
        st.session_state.thought_leadership_strategy = strategy
        st.success("Strategy saved successfully!")
