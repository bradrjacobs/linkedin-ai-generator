import streamlit as st
import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Basic logging setup
logging.basicConfig(level=logging.INFO)

# Server URL
SERVER_URL = os.getenv("API_URL", "https://mylance-api.herokuapp.com")  # Replace with your actual API URL

def make_request(method, endpoint, json=None):
    """Simple request handler"""
    try:
        response = requests.request(method, f"{SERVER_URL}/{endpoint}", json=json)
        if response.status_code == 200:
            return response.json()
        logging.error(f"Request failed: {response.text}")
        return None
    except Exception as e:
        logging.error(f"Request error: {e}")
        return None

def strip_prefix(value, prefixes):
    """Remove known prefixes from values"""
    if not value:
        return ""
    for prefix in prefixes:
        if value.startswith(prefix):
            return value.replace(prefix, "").strip()
    return value.strip()

def load_customer_data(profile_id):
    """Load customer data for a profile"""
    if not profile_id:
        return
    
    data = make_request("POST", "get-customer-data", json={"profile_id": profile_id})
    if data:
        # Clean up the data by removing prefixes
        cleaned_data = {
            "ideal_customer": strip_prefix(data.get("ideal_customer"), ["ICP: "]),
            "ideal_problem": strip_prefix(data.get("ideal_problem"), ["ICP Pain points: "]),
            "unique_value": strip_prefix(data.get("unique_value"), ["Unique value: "]),
            "proof_points": strip_prefix(data.get("proof_points"), ["Proof points: "]),
            "energizing_topics": strip_prefix(data.get("energizing_topics"), ["Energizing topics: "]),
            "decision_maker": strip_prefix(data.get("decision_maker"), ["Decision maker: "])
        }
        return cleaned_data
    return None

# Main UI
st.title("👥 Customer Data & Information")

# Show profile name if selected
if st.session_state.get("selected_profile_name"):
    st.subheader(f"Editing Profile: {st.session_state['selected_profile_name']}")
    st.divider()

# Load data for the selected profile
data = None
if st.session_state.get("selected_profile_id"):
    data = load_customer_data(st.session_state["selected_profile_id"])
    # Add debug logging for loaded data
    if data:
        logging.info("Data loaded successfully:")
        logging.info(f"Keys in data: {data.keys()}")
        logging.info(f"ideal_customer value: {data.get('ideal_customer')}")
        logging.info(f"ideal_problem value: {data.get('ideal_problem')}")

# Form layout
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("🎯 Customer Profile")
    ideal_customer = st.text_area(
        "Ideal Customer",
        value=data.get("ideal_customer", "") if data else "",
        key="ideal_customer_input"
    )
    
    ideal_problem = st.text_area(
        "ICP Pain Points",
        value=data.get("ideal_problem", "") if data else "",
        key="ideal_problem_input"
    )
    
    unique_value = st.text_area(
        "Unique Value",
        value=data.get("unique_value", "") if data else "",
        key="unique_value_input"
    )

with right_col:
    st.subheader("💡 Customer Insights")
    proof_points = st.text_area(
        "Proof Points",
        value=data.get("proof_points", "") if data else "",
        key="proof_points_input"
    )
    
    energizing_topics = st.text_area(
        "Energizing Topics",
        value=data.get("energizing_topics", "") if data else "",
        key="energizing_topics_input"
    )
    
    decision_maker = st.text_area(
        "Decision Maker",
        value=data.get("decision_maker", "") if data else "",
        key="decision_maker_input"
    )

# Save button
if st.button("💾 Save Customer Data", key="save_button"):
    if not st.session_state.get("selected_profile_id"):
        st.error("Please select a profile first")
    else:
        # Add prefixes back when saving
        save_data = {
            "profile_id": st.session_state["selected_profile_id"],
            "ideal_customer": f"ICP: {ideal_customer}",
            "ideal_problem": f"ICP Pain points: {ideal_problem}",
            "unique_value": f"Unique value: {unique_value}",
            "proof_points": f"Proof points: {proof_points}",
            "energizing_topics": f"Energizing topics: {energizing_topics}",
            "decision_maker": f"Decision maker: {decision_maker}"
        }
        
        if make_request("POST", "save-customer-data", json=save_data):
            st.success("Saved successfully!")
        else:
            st.error("Failed to save data") 