import streamlit as st
import requests
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Set up API URL
API_URL = os.getenv("API_URL", "https://mylance-api.herokuapp.com")

def save_thought_leadership_strategy(strategy):
    """Save thought leadership strategy to API"""
    try:
        response = requests.post(f"{API_URL}/save-thought-leadership", json={"strategy": strategy})
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Error saving thought leadership strategy: {e}")
        return False

def get_thought_leadership_strategy():
    """Get thought leadership strategy from API"""
    try:
        response = requests.get(f"{API_URL}/get-thought-leadership")
        response.raise_for_status()
        return response.json().get("strategy", "")
    except Exception as e:
        logging.error(f"Error getting thought leadership strategy: {e}")
        return ""

# Page configuration
st.set_page_config(page_title="Thought Leadership Strategy", page_icon="📊", layout="wide")

st.title("Thought Leadership Strategy")
st.markdown("""
This page helps you define Mylance's thought leadership strategy. This strategy will guide the content generation for all users.
""")

# Load current strategy
current_strategy = get_thought_leadership_strategy()

# Strategy input
with st.form("thought_leadership_form"):
    strategy = st.text_area(
        "Define Mylance's Thought Leadership Strategy",
        value=current_strategy,
        height=300,
        help="Enter the overall thought leadership strategy that will guide content generation for all users."
    )
    
    submit = st.form_submit_button("Save Strategy")
    
    if submit and strategy:
        if save_thought_leadership_strategy(strategy):
            st.success("Strategy saved successfully!")
        else:
            st.error("Failed to save strategy. Please try again.")
