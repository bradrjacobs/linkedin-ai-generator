import streamlit as st
import logging
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Debug secrets
st.write("### Debugging Secrets:")
try:
    # Show all available secrets (without revealing values)
    st.write("Available secret keys:", list(st.secrets.keys()))
    
    # Try to access the OpenAI key specifically
    api_key = st.secrets["OPENAI_API_KEY"]
    st.write("✅ Found OPENAI_API_KEY in secrets")
    st.write("Key length:", len(api_key))
    st.write("Key starts with:", api_key[:7] + "..." if api_key else "N/A")
except Exception as e:
    st.error(f"❌ Error accessing secrets: {str(e)}")
    st.write("Full error details:", e)
    st.stop()

# Initialize OpenAI client
try:
    # Create client with minimal configuration
    client = OpenAI()  # Let it use the environment variable
    os.environ["OPENAI_API_KEY"] = api_key  # Set the environment variable
    
    # Test with a simple API call
    response = client.models.list()
    st.success("✅ OpenAI client initialized and tested successfully!")
except Exception as e:
    st.error(f"❌ Error initializing OpenAI client: {str(e)}")
    st.write("Full error details:", e)
    st.write("OpenAI version:", OpenAI.__version__)  # Add version info for debugging
    st.stop()

# Initialize session state
if "profiles" not in st.session_state:
    st.session_state.profiles = []
if "current_profile" not in st.session_state:
    st.session_state.current_profile = None
if "thought_leadership_strategy" not in st.session_state:
    st.session_state.thought_leadership_strategy = ""

def load_profiles():
    """Load profiles from session state"""
    return st.session_state.profiles

def load_profile_data(profile_id):
    """Load profile data from session state"""
    for profile in st.session_state.profiles:
        if profile.get("profile_id") == profile_id:
            return profile
    return None

def save_profile_data(profile_data):
    """Save profile data to session state"""
    profiles = st.session_state.profiles
    profile_id = profile_data.get("profile_id")
    
    # Update existing profile or add new one
    updated = False
    for i, profile in enumerate(profiles):
        if profile.get("profile_id") == profile_id:
            profiles[i] = profile_data
            updated = True
            break
    
    if not updated:
        profiles.append(profile_data)
    
    st.session_state.profiles = profiles
    st.session_state.current_profile = profile_data

# Main app layout
st.set_page_config(page_title="LinkedIn AI Generator", page_icon="🚀", layout="wide")

st.title("LinkedIn AI Generator")
st.markdown("Welcome to the LinkedIn AI Generator! This tool helps you create engaging LinkedIn content based on your professional profile and target audience.")

# Profile selection
profiles = load_profiles()
profile_names = [f"{p.get('first_name', '')} {p.get('last_name', '')}" for p in profiles]
profile_names.append("Create New Profile")

selected_profile = st.selectbox(
    "Select or Create Profile",
    options=profile_names,
    index=len(profile_names)-1 if st.session_state.current_profile is None else profile_names.index(f"{st.session_state.current_profile.get('first_name', '')} {st.session_state.current_profile.get('last_name', '')}")
)

if selected_profile == "Create New Profile":
    st.session_state.current_profile = None
    with st.form("profile_form"):
        st.subheader("Create New Profile")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email (optional)")
        linkedin_url = st.text_input("LinkedIn URL (optional)")
        
        if st.form_submit_button("Create Profile"):
            if first_name and last_name:
                new_profile = {
                    "profile_id": f"{first_name.lower()}_{last_name.lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "linkedin_url": linkedin_url
                }
                save_profile_data(new_profile)
                st.success("Profile created successfully!")
                st.experimental_rerun()
            else:
                st.error("Please enter at least first and last name.")
else:
    # Load existing profile
    selected_idx = profile_names.index(selected_profile)
    profile_data = profiles[selected_idx]
    st.session_state.current_profile = profile_data
    
    # Display profile info
    st.subheader("Profile Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Name:** {profile_data.get('first_name', '')} {profile_data.get('last_name', '')}")
        st.write(f"**Email:** {profile_data.get('email', 'Not provided')}")
    with col2:
        st.write(f"**LinkedIn:** {profile_data.get('linkedin_url', 'Not provided')}")
        st.write(f"**Profile ID:** {profile_data.get('profile_id', '')}")

# Navigation instructions
st.markdown("---")
st.markdown("""
### Next Steps
1. 📊 Go to the **Thought Leadership** page to define your content strategy
2. 👥 Define your **Customer Data** to target the right audience
3. 📝 Generate **LinkedIn Posts** based on your strategy
""")
