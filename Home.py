import streamlit as st
import json
from datetime import datetime
import logging
import pytz
import os
from dotenv import load_dotenv
import time
from supabase import create_client, Client
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - APP_LOG - %(message)s')

# Load environment variables
supabase_url = st.secrets["SUPABASE_URL"]
# Ensure the URL ends with .supabase.co
if not supabase_url.endswith('.supabase.co'):
    supabase_url = f"https://{supabase_url}.supabase.co"
supabase_key = st.secrets["SUPABASE_KEY"]
openai_api_key = st.secrets["OPENAI_API_KEY"]

# Initialize Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize OpenAI client
openai_client = OpenAI(api_key=openai_api_key)

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
if "show_new_profile_form" not in st.session_state:
    st.session_state.show_new_profile_form = False

def load_profiles():
    """Load all profiles from Supabase"""
    try:
        response = supabase.table("profiles").select("*").execute()
        if hasattr(response, 'data'):
            return response.data
        return []
    except Exception as e:
        st.error(f"Failed to load profiles: {e}")
        return []

def load_profile_data(profile_id):
    """Load data for a specific profile"""
    try:
        response = supabase.table("profiles").select("*").eq("id", profile_id).single().execute()
        if hasattr(response, 'data'):
            return response.data
        return None
    except Exception as e:
        st.error(f"Failed to load profile data: {e}")
        return None

def save_profile_data(profile_id, data):
    """Save profile data"""
    try:
        response = supabase.table("profiles").update(data).eq("id", profile_id).execute()
        return True
    except Exception as e:
        st.error(f"Error saving profile data: {e}")
        return False

def generate_strategy(profile_id):
    """Generate content strategy using OpenAI"""
    try:
        profile_data = load_profile_data(profile_id)
        if not profile_data:
            return False

        prompt = f"""Create a content strategy for a LinkedIn profile with the following information:
        Ideal Customer: {profile_data.get('icp', '')}
        Pain Points: {profile_data.get('icp_pain_points', '')}
        Unique Value: {profile_data.get('unique_value', '')}
        Proof Points: {profile_data.get('proof_points', '')}
        Topics: {profile_data.get('energizing_topics', '')}
        Decision Makers: {profile_data.get('decision_makers', '')}
        """

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        strategy = response.choices[0].message.content
        save_profile_data(profile_id, {"content_strategy": strategy})
        return True
    except Exception as e:
        st.error(f"Failed to generate strategy: {e}")
        return False

def generate_prompts(profile_id):
    """Generate LinkedIn prompts"""
    try:
        profile_data = load_profile_data(profile_id)
        if not profile_data:
            return False

        prompt = f"""Generate 30 LinkedIn post prompts based on this strategy:
        {profile_data.get('content_strategy', '')}
        
        Format each prompt as:
        1. Hook: [attention-grabbing opening]
        2. Content: [main post content]
        3. Style: [First-Person Anecdotes/Listicles/Educational/Thought Leadership/Case Studies/Questions]
        """

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        prompts = response.choices[0].message.content
        save_profile_data(profile_id, {"linkedin_prompts": prompts})
        return True
    except Exception as e:
        st.error(f"Error generating prompts: {e}")
        return False

# Sidebar for profile selection
with st.sidebar:
    st.title("👤 Profile Management")
    
    # Add New Profile button at the top
    if st.button("➕ New Profile", key="new_profile_button"):
        st.session_state.show_new_profile_form = not st.session_state.show_new_profile_form
    
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
        with st.form("new_profile_form"):
            st.subheader("Create New Profile")
            first_name = st.text_input("First Name", key="new_first_name")
            last_name = st.text_input("Last Name", key="new_last_name")
            email = st.text_input("Email (Optional)", key="new_email")
            linkedin_url = st.text_input("LinkedIn URL (Optional)", key="new_linkedin_url")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Profile")
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_new_profile_form = False
                    st.rerun()
            
            if submit:
                if first_name and last_name:
                    profile_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email if email else None,
                        "linkedin_url": linkedin_url if linkedin_url else None,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    try:
                        response = supabase.table("profiles").insert(profile_data).execute()
                        if hasattr(response, 'data'):
                            st.success("Profile created successfully!")
                            st.session_state.show_new_profile_form = False
                            st.rerun()
                        else:
                            st.error("Failed to create profile")
                    except Exception as e:
                        st.error(f"Error creating profile: {e}")
                else:
                    st.error("First name and last name are required")

# Main content
if st.session_state.selected_profile:
    profile = st.session_state.selected_profile
    
    st.title(f"📊 Content Strategy for {profile['first_name']} {profile['last_name']}")
    
    # 1. Customer Data Section
    st.header("👥 Customer Data")
    with st.form("customer_data_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            icp = st.text_area("Ideal Customer Profile (ICP)", value=profile.get("icp", ""))
            pain_points = st.text_area("ICP Pain Points", value=profile.get("icp_pain_points", ""))
            unique_value = st.text_area("Unique Value Add", value=profile.get("unique_value", ""))
        
        with col2:
            proof_points = st.text_area("Proof Points", value=profile.get("proof_points", ""))
            energizing_topics = st.text_area("Energizing Topics", value=profile.get("energizing_topics", ""))
            decision_makers = st.text_area("Decision Makers", value=profile.get("decision_makers", ""))
        
        if st.form_submit_button("Save Customer Data"):
            update_data = {
                "icp": icp,
                "icp_pain_points": pain_points,
                "unique_value": unique_value,
                "proof_points": proof_points,
                "energizing_topics": energizing_topics,
                "decision_makers": decision_makers,
                "updated_at": datetime.now().isoformat()
            }
            try:
                response = supabase.table("profiles").update(update_data).eq("id", profile["id"]).execute()
                if hasattr(response, 'data'):
                    st.success("Customer data saved!")
                    st.session_state.profile_data = load_profile_data(profile["id"])
                else:
                    st.error("Failed to save customer data")
            except Exception as e:
                st.error(f"Error saving customer data: {e}")

    # Display last updated time if available
    if profile.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(profile["updated_at"].replace("Z", "+00:00"))
            local_tz = pytz.timezone("America/Los_Angeles")  # Using Pacific Time
            local_time = updated_at.astimezone(local_tz)
            st.info(f"Last updated: {local_time.strftime('%Y-%m-%d %I:%M %p %Z')}")
        except Exception as e:
            st.info("Last updated: Unknown")
            logging.warning(f"Error formatting timestamp: {e}")
    
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
                st.session_state.previous_strategy = profile.get("content_strategy")
                st.session_state.profile_data = load_profile_data(profile["id"])
                st.rerun()
            else:
                st.error("Failed to generate strategy")
    
    # Display and edit strategy
    strategy = profile.get("content_strategy", "")
    if strategy:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Current Strategy")
            # Display last updated timestamp if available
            updated_at = profile.get("updated_at")
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
                            response = openai_client.chat.completions.create(
                                model="gpt-4",
                                messages=[{"role": "user", "content": feedback}],
                                temperature=0.7,
                                max_tokens=1000
                            )
                            new_strategy = response.choices[0].message.content
                            if save_profile_data(profile["id"], {"content_strategy": new_strategy}):
                                st.success("Strategy updated based on feedback!")
                                st.session_state.profile_data = load_profile_data(profile["id"])
                                st.rerun()
                            else:
                                st.error("Failed to save updated strategy")
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
        pillars = profile.get("content_pillars", []) or []
        
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
    prompts = profile.get("linkedin_prompts", [])
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
