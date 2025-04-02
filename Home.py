import streamlit as st
import requests
import json
from datetime import datetime
import logging
import pytz
import os
from dotenv import load_dotenv
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - APP_LOG - %(message)s')

# Set page config
st.set_page_config(page_title="LinkedIn Content Strategy", layout="wide", initial_sidebar_state="expanded")

# Add custom CSS for the New Profile button
st.markdown("""
<style>
.stButton > button {
    background-color: #537FFF;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    width: 100%;
    margin-bottom: 1rem;
}
.stButton > button:hover {
    background-color: #3B5CD9;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = None
if "profile_data" not in st.session_state:
    st.session_state.profile_data = None

# API configuration
API_URL = "http://localhost:8000"

def load_profiles():
    """Load all profiles from the backend"""
    try:
        response = requests.get(f"{API_URL}/profiles")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to load profiles: {e}")
        return []

def load_profile_data(profile_id):
    """Load data for a specific profile"""
    try:
        response = requests.get(f"{API_URL}/profiles/{profile_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to load profile data: {e}")
        return None

def save_profile_data(profile_id, data):
    """Save profile data"""
    try:
        response = requests.put(
            f"{API_URL}/profiles/{profile_id}",
            json={"id": profile_id, "data": data}
        )
        if response.status_code == 200:
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Failed to save profile data: {error_detail}")
            return False
    except Exception as e:
        st.error(f"Error saving profile data: {e}")
        return False

def generate_strategy(profile_id):
    """Generate content strategy"""
    try:
        response = requests.post(f"{API_URL}/profiles/{profile_id}/generate-strategy")
        return response.status_code == 200
    except Exception as e:
        st.error(f"Failed to generate strategy: {e}")
        return False

def generate_prompts(profile_id):
    """Generate LinkedIn prompts"""
    try:
        response = requests.post(f"{API_URL}/profiles/{profile_id}/generate-prompts")
        if response.status_code == 200:
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Failed to generate prompts: {error_detail}")
            return False
    except Exception as e:
        st.error(f"Error generating prompts: {e}")
        return False

# Sidebar for profile selection
with st.sidebar:
    st.title("👤 Profile Management")
    
    # Add New Profile button at the top
    if st.button("➕ New Profile"):
        st.session_state.show_new_profile_form = True
    else:
        st.session_state.show_new_profile_form = False
    
    # Profile selection
    profiles = load_profiles()
    profile_names = [f"{p['first_name']} {p['last_name']}" for p in profiles]
    
    selected_profile = st.selectbox(
        "Select Profile",
        profile_names,
        key="profile_selector"
    )
    
    # Show new profile form when button is clicked
    if st.session_state.show_new_profile_form:
        st.subheader("Create New Profile")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email (Optional)")
        linkedin_url = st.text_input("LinkedIn URL (Optional)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Create Profile"):
                if first_name and last_name:
                    profile_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email if email else None,
                        "linkedin_url": linkedin_url if linkedin_url else None
                    }
                    try:
                        response = requests.post(f"{API_URL}/profiles", json=profile_data)
                        if response.status_code == 200:
                            st.success("Profile created successfully!")
                            st.session_state.show_new_profile_form = False
                            st.rerun()
                        else:
                            error_detail = response.json().get("detail", "Unknown error")
                            st.error(f"Failed to create profile: {error_detail}")
                    except Exception as e:
                        st.error(f"Error creating profile: {e}")
        with col2:
            if st.button("Cancel"):
                st.session_state.show_new_profile_form = False
                st.rerun()
    else:
        # Find selected profile
        selected_profile_data = next((p for p in profiles if f"{p['first_name']} {p['last_name']}" == selected_profile), None)
        if selected_profile_data:
            st.session_state.selected_profile = selected_profile_data
            if not st.session_state.profile_data:
                st.session_state.profile_data = load_profile_data(selected_profile_data["id"])

# Main content
if st.session_state.selected_profile and st.session_state.profile_data:
    profile = st.session_state.selected_profile
    data = st.session_state.profile_data
    
    st.title(f"📊 Content Strategy for {profile['first_name']} {profile['last_name']}")
    
    # 1. Customer Data Section
    st.header("👥 Customer Data")
    with st.form("customer_data_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            icp = st.text_area("Ideal Customer Profile (ICP)", value=data.get("icp", ""))
            pain_points = st.text_area("ICP Pain Points", value=data.get("icp_pain_points", ""))
            unique_value = st.text_area("Unique Value Add", value=data.get("unique_value", ""))
        
        with col2:
            proof_points = st.text_area("Proof Points", value=data.get("proof_points", ""))
            energizing_topics = st.text_area("Energizing Topics", value=data.get("energizing_topics", ""))
            decision_makers = st.text_area("Decision Makers", value=data.get("decision_makers", ""))
        
        if st.form_submit_button("Save Customer Data"):
            update_data = {
                "icp": icp,
                "icp_pain_points": pain_points,
                "unique_value": unique_value,
                "proof_points": proof_points,
                "energizing_topics": energizing_topics,
                "decision_makers": decision_makers
            }
            if save_profile_data(profile["id"], update_data):
                st.success("Customer data saved!")
                st.session_state.profile_data = load_profile_data(profile["id"])
            else:
                st.error("Failed to save customer data")
    
    # 2. Content Strategy Section
    st.header("🎯 Content Strategy")
    
    # Store previous strategy in session state if not exists
    if "previous_strategy" not in st.session_state:
        st.session_state.previous_strategy = None
    
    # Generate strategy button
    if st.button("Generate Content Strategy"):
        with st.spinner("Generating content strategy based on your customer data..."):
            if generate_strategy(profile["id"]):
                st.success("Strategy generated!")
                # Store the current strategy before updating
                st.session_state.previous_strategy = data.get("content_strategy")
                st.session_state.profile_data = load_profile_data(profile["id"])
                st.rerun()
            else:
                st.error("Failed to generate strategy")
    
    # Display and edit strategy
    strategy = data.get("content_strategy", "")
    if strategy:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Current Strategy")
            # Display last updated timestamp if available
            updated_at = data.get("updated_at")
            if updated_at:
                try:
                    logging.info(f"Raw updated_at value: {updated_at}")
                    # Convert ISO format to datetime with timezone
                    dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    # Convert to local timezone (Pacific Time)
                    local_tz = pytz.timezone('America/Los_Angeles')
                    local_dt = dt.astimezone(local_tz)
                    # Format with timezone abbreviation
                    formatted_date = local_dt.strftime("%B %d, %Y at %I:%M %p %Z")
                    st.caption(f"Last updated: {formatted_date}")
                except Exception as e:
                    logging.error(f"Error formatting timestamp: {e}")
                    st.caption(f"Last updated: {updated_at}")  # Show raw timestamp if formatting fails
            else:
                logging.warning("No updated_at timestamp found in data")
                st.caption("Last updated: Unknown")
            
            strategy_text = st.text_area("Content Strategy", value=strategy, height=300)
            
            # Save button for manual edits
            if st.button("Save Strategy"):
                if save_profile_data(profile["id"], {"content_strategy": strategy_text}):
                    st.success("Strategy saved!")
                    st.session_state.profile_data = load_profile_data(profile["id"])
                else:
                    st.error("Failed to save strategy")
        
        with col2:
            st.subheader("Strategy Feedback")
            feedback = st.text_area("Provide feedback to improve the strategy:", height=150)
            
            if st.button("Update Based on Feedback"):
                if feedback:
                    with st.spinner("Updating strategy based on feedback..."):
                        # Store current strategy before updating
                        st.session_state.previous_strategy = strategy_text
                        
                        # Call OpenAI to update strategy based on feedback
                        try:
                            response = requests.post(
                                f"{API_URL}/profiles/{profile['id']}/update-strategy",
                                json={"feedback": feedback}
                            )
                            if response.status_code == 200:
                                new_strategy = response.json().get("content_strategy")
                                if save_profile_data(profile["id"], {"content_strategy": new_strategy}):
                                    st.success("Strategy updated based on feedback!")
                                    st.session_state.profile_data = load_profile_data(profile["id"])
                                    st.rerun()
                                else:
                                    st.error("Failed to save updated strategy")
                            else:
                                st.error("Failed to update strategy")
                        except Exception as e:
                            st.error(f"Error updating strategy: {e}")
                else:
                    st.warning("Please provide feedback before updating")
            
            # Undo button
            if st.session_state.previous_strategy:
                if st.button("Undo Last Change"):
                    if save_profile_data(profile["id"], {"content_strategy": st.session_state.previous_strategy}):
                        st.success("Strategy restored to previous version!")
                        st.session_state.profile_data = load_profile_data(profile["id"])
                        st.rerun()
                    else:
                        st.error("Failed to restore previous strategy")
    else:
        st.info("No strategy generated yet. Click the 'Generate Content Strategy' button above to create one based on your customer data.")
    
    # 3. Content Pillars Section
    st.header("📌 Content Pillars")
    with st.form("pillars_form"):
        # Ensure pillars is a list, even if None
        pillars = data.get("content_pillars", []) or []
        
        for i in range(3):
            pillar = st.text_input(f"Pillar {i+1}", value=pillars[i] if i < len(pillars) else "")
            if i >= len(pillars):
                pillars.append(pillar)
            else:
                pillars[i] = pillar
        
        if st.form_submit_button("Save Pillars"):
            if save_profile_data(profile["id"], {"content_pillars": pillars}):
                st.success("Pillars saved!")
                st.session_state.profile_data = load_profile_data(profile["id"])
            else:
                st.error("Failed to save pillars")
    
    # 4. LinkedIn Prompts Section
    st.header("💡 LinkedIn Prompts")
    
    # Generate prompts button
    if st.button("Generate 30 LinkedIn Prompts"):
        with st.spinner("Generating 30 LinkedIn prompts based on your strategy..."):
            if generate_prompts(profile["id"]):
                st.success("Prompts generated!")
                # Reload profile data to get the new prompts
                st.session_state.profile_data = load_profile_data(profile["id"])
                st.rerun()  # Force a rerun to show the new prompts
            else:
                st.error("Failed to generate prompts")
    
    # Display prompts
    prompts = data.get("linkedin_prompts", [])
    if prompts:
        st.write(f"Found {len(prompts)} prompts")
        
        # Add a search box to filter prompts
        search_term = st.text_input("Search prompts...", "").lower()
        
        for i, prompt in enumerate(prompts):
            # Skip if doesn't match search
            if search_term and search_term not in prompt.get("prompt", "").lower():
                continue
                
            with st.expander(f"Prompt {i+1}: {prompt.get('style', '')}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Prompt:**")
                    st.write(prompt.get("prompt", ""))
                    st.markdown("**Hook:**")
                    st.write(prompt.get("hook", ""))
                    st.markdown("**Style:**")
                    st.write(prompt.get("style", ""))
                
                with col2:
                    # Create a copy button that copies all prompt details
                    prompt_text = f"""Prompt: {prompt.get('prompt', '')}
Hook: {prompt.get('hook', '')}
Style: {prompt.get('style', '')}"""
                    
                    if st.button("Copy to Clipboard", key=f"copy_{i}"):
                        st.write("Copied to clipboard!")
                        st.code(prompt_text, language=None)
    else:
        st.info("No prompts generated yet. Click the 'Generate 30 LinkedIn Prompts' button above to create prompts based on your strategy.")
else:
    st.info("Please select or create a profile to get started.")
