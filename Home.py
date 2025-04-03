import streamlit as st
import requests
import json
import logging
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
import time
from supabase import create_client, Client
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize session state for storing data locally
if 'profiles' not in st.session_state:
    st.session_state.profiles = []
if 'current_profile' not in st.session_state:
    st.session_state.current_profile = None

# Set page config
st.set_page_config(page_title="Mylance Content Generator", layout="wide", initial_sidebar_state="expanded")

# Add custom CSS for Mylance branding
st.markdown("""
<style>
/* Global styles */
[data-testid="stAppViewContainer"] {
    background-color: #FAFAFA;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    color: #2D3142;
    font-weight: 600;
}

/* Logo and title container */
.logo-title-container {
    margin-bottom: 2rem;
}

.logo-title-container h1 {
    margin: 0;
    padding: 0;
    font-size: 2rem;
    color: #2D3142;
}

/* Buttons */
.stButton > button {
    background-color: #00BFB3 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background-color: #00A89D !important;
    transform: translateY(-1px);
}

/* Secondary buttons (like in forms) */
.stButton > button[kind="secondary"] {
    background-color: #537FFF !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #3B5CD9 !important;
}

/* Form inputs */
[data-testid="stTextInput"] input, 
[data-testid="stNumberInput"] input, 
[data-testid="stTextArea"] textarea {
    border-radius: 8px;
    border: 1px solid #E0E0E0;
}

/* Expanders/Cards */
.streamlit-expanderHeader {
    background-color: white;
    border-radius: 8px;
    border: 1px solid #E0E0E0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: white;
    border-right: 1px solid #E0E0E0;
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    padding: 0 1rem;
}

/* Progress bars */
[data-testid="stProgressBar"] {
    background-color: #E0E0E0;
}

[data-testid="stProgressBar"] > div {
    background-color: #00BFB3;
}

/* Headers with icons */
.header-with-icon {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

/* Success/Info messages */
.stSuccess {
    background-color: #E6FFF9;
    border: 1px solid #00BFB3;
    color: #00806C;
}

.stInfo {
    background-color: #F0F4FF;
    border: 1px solid #537FFF;
    color: #2D3142;
}

/* Container styling */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
    background-color: white;
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid #E0E0E0;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# Update header with title only
st.markdown("""
<div class="logo-title-container">
    <h1>Content Generator</h1>
</div>
""", unsafe_allow_html=True)

def load_profiles():
    """Load all profiles from session state"""
    return st.session_state.profiles

def load_profile_data(profile_id):
    """Load profile data from session state"""
    for profile in st.session_state.profiles:
        if profile.get('profile_id') == profile_id:
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
        save_profile_data({"profile_id": profile_id, "content_strategy": strategy})
        return True
    except Exception as e:
        st.error(f"Failed to generate strategy: {e}")
        return False

def generate_prompts(profile_id, total_prompts=30):
    """Generate LinkedIn prompts in batches"""
    try:
        profile_data = load_profile_data(profile_id)
        if not profile_data:
            return False

        all_prompts = []
        BATCH_SIZE = 5  # Generate 5 prompts at a time
        TOTAL_PROMPTS = total_prompts  # Use the passed in total_prompts parameter
        num_batches = (TOTAL_PROMPTS + BATCH_SIZE - 1) // BATCH_SIZE  # Calculate total number of batches, rounding up
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create containers for displaying prompts in real-time
        prompt_container = st.container()
        with prompt_container:
            st.subheader("Generated Prompts")
            # Create sections for each category
            category_displays = {
                "First-Person Anecdote": st.empty(),
                "Listicle with a Hook": st.empty(),
                "Educational How-To Post": st.empty(),
                "Thought Leadership/Opinion Piece": st.empty(),
                "Case Study/Success Story": st.empty(),
                "Engagement-Driven Question": st.empty()
            }

        for batch_start in range(0, TOTAL_PROMPTS, BATCH_SIZE):
            batch_number = (batch_start // BATCH_SIZE) + 1
            status_text.text(f"Generating batch {batch_number} of {num_batches}...")
            
            # Calculate the actual batch size for this iteration
            current_batch_size = min(BATCH_SIZE, TOTAL_PROMPTS - batch_start)

            prompt = f"""Generate {current_batch_size} unique LinkedIn post prompts that directly ask the user questions they can answer from their experience:

Strategy: {profile_data.get('content_strategy', '')}
Content Pillars: {', '.join(profile_data.get('content_pillars', []))}

Each prompt should be a direct question or invitation that makes it easy for the user to write about their own experiences. For example:

- "Tell us about a time when you had to pivot your entire project strategy. What was at stake, and how did you handle the uncertainty?"
- "What's the biggest misconception people have about freelance consulting? Share a story that changed your perspective."
- "Looking back at your first year of consulting, what advice would you give yourself? Share 3 lessons that surprised you."

Make each prompt personal and specific, asking about:
1. Real experiences and challenges they've faced
2. Specific decisions or turning points in their career
3. Lessons learned from successes or failures
4. Unique insights from their industry expertise
5. Stories that demonstrate their value proposition

Each prompt MUST be categorized as EXACTLY one of these post types (use the exact text, no variations):
1. First-Person Anecdote
2. Listicle with a Hook
3. Educational How-To Post
4. Thought Leadership/Opinion Piece
5. Case Study/Success Story
6. Engagement-Driven Question

Return ONLY a JSON array of {current_batch_size} prompt objects. Each object must have these exact keys:
- prompt: A direct question or invitation for the user to share their experience
- hook: A suggested opening line they can use to start their story
- type_of_post: Must be EXACTLY one of the six categories listed above, no variations

Return the response in this exact format:
[
    {{
        "prompt": "What's the most challenging leadership decision you've had to make as a consultant? Walk us through your thought process and what it taught you about decision-making under pressure.",
        "hook": "Last month, I faced a decision that tested everything I believed about leadership.",
        "type_of_post": "First-Person Anecdote"
    }},
    ... {current_batch_size-1} more objects
]

Guidelines for prompts:
1. Ask direct questions the user can answer from their experience
2. Focus on specific moments or decisions they can share
3. Encourage storytelling with concrete details
4. Make it easy for them to showcase their expertise
5. Keep it conversational but professional
6. Focus on topics that demonstrate their value
7. Ask for specific examples rather than general advice

Ensure an even distribution of post types across all prompts. Do not include any other text, only the JSON array."""

            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a LinkedIn content expert who helps users share their professional experiences through engaging stories. Return only valid JSON arrays of prompt objects, using the exact post type categories specified."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )

                try:
                    batch_prompts = json.loads(response.choices[0].message.content)
                    if isinstance(batch_prompts, list):
                        all_prompts.extend(batch_prompts)
                        
                        # Organize prompts by category
                        category_prompts = {
                            "First-Person Anecdote": [],
                            "Listicle with a Hook": [],
                            "Educational How-To Post": [],
                            "Thought Leadership/Opinion Piece": [],
                            "Case Study/Success Story": [],
                            "Engagement-Driven Question": []
                        }
                        
                        # Add new prompts to their categories
                        for p in batch_prompts:
                            post_type = p.get('type_of_post', '')
                            if post_type in category_prompts:
                                category_prompts[post_type].append(p)
                        
                        # Update display for each category
                        for category, prompts in category_prompts.items():
                            if prompts:
                                display_text = f"**{category}**\n\n"
                                for i, p in enumerate(prompts, start=1):
                                    display_text += f"🔹 **Hook:** {p.get('hook', '')}\n"
                                    display_text += f"**Content:** {p.get('prompt', '')}\n\n"
                                category_displays[category].markdown(display_text)
                    else:
                        st.warning(f"Batch {batch_number} did not return a list of prompts")
                        continue
                except json.JSONDecodeError as e:
                    st.warning(f"Could not parse JSON in batch {batch_number}: {e}")
                    continue
                
                # Update progress
                progress = (batch_start + current_batch_size) / TOTAL_PROMPTS
                progress_bar.progress(progress)
                
                # Small delay to avoid rate limits
                time.sleep(0.5)

            except Exception as e:
                st.error(f"Error generating batch {batch_number}: {e}")
                continue

        progress_bar.progress(1.0)
        status_text.text("Finished generating prompts!")

        # Save all prompts
        if len(all_prompts) > 0:
            try:
                # Ensure the prompts are properly formatted before saving
                formatted_prompts = []
                for p in all_prompts:
                    if isinstance(p, dict) and "prompt" in p and "hook" in p and "type_of_post" in p:
                        formatted_prompts.append({
                            "prompt": str(p["prompt"]),
                            "hook": str(p["hook"]),
                            "type_of_post": str(p["type_of_post"])
                        })
                
                if save_profile_data({"profile_id": profile_id, "linkedin_prompts": formatted_prompts}):
                    return True
                else:
                    st.error("Failed to save prompts to database")
                    return False
            except Exception as e:
                st.error(f"Error formatting prompts for save: {e}")
                return False
        else:
            st.warning("No valid prompts were generated")
            return False

    except Exception as e:
        st.error(f"Error generating prompts: {e}")
        return False

def generate_pillars(profile_id):
    """Generate content pillars using OpenAI"""
    try:
        profile_data = load_profile_data(profile_id)
        if not profile_data:
            return False

        prompt = f"""Based on the following information, generate 3 unique content themes for LinkedIn content. Each theme should be a complete sentence that captures a specific area of expertise, experience, or value the person brings:

Content Strategy: {profile_data.get('content_strategy', '')}
Ideal Customer: {profile_data.get('icp', '')}
Pain Points: {profile_data.get('icp_pain_points', '')}
Unique Value: {profile_data.get('unique_value', '')}
Proof Points: {profile_data.get('proof_points', '')}
Topics: {profile_data.get('energizing_topics', '')}
Decision Makers: {profile_data.get('decision_makers', '')}

Create 3 distinct themes that:
1. Demonstrate specific value and expertise
2. Share learnings and experiences
3. Show what they can deliver or have achieved

Each theme should be:
- A complete sentence
- Focused on a unique aspect (no overlap between themes)
- Specific enough to generate multiple content pieces from
- Aligned with the overall content strategy
- Written from a position of authority and experience

Format your response EXACTLY like this, with numbers and quotes:
1. "First theme sentence here."
2. "Second theme sentence here."
3. "Third theme sentence here."

Make sure each theme is on its own line and includes the number and quotes exactly as shown above.
"""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        # Process the response to extract just the theme text without numbers and quotes
        content = response.choices[0].message.content.strip()
        themes = []
        for line in content.split('\n'):
            # Extract the text between quotes, ignoring the number prefix
            if '"' in line:
                theme = line.split('"')[1]  # Get the text between first and second quote
                themes.append(theme)
            elif "'" in line:
                theme = line.split("'")[1]  # Handle single quotes as well
                themes.append(theme)
        
        # Ensure we have exactly 3 themes
        while len(themes) < 3:
            themes.append("")  # Add empty strings if we somehow got fewer than 3 themes
        themes = themes[:3]  # Trim to 3 themes if we somehow got more
        
        save_profile_data({"profile_id": profile_id, "content_pillars": themes})
        return True
    except Exception as e:
        st.error(f"Failed to generate pillars: {e}")
        return False

# Sidebar for profile selection
with st.sidebar:
    st.markdown("""
    <div class="header-with-icon">
        <h3>👤 Profile Management</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Add New Profile button at the top
    if st.button("➕ Create New Profile", key="new_profile_button", use_container_width=True):
        st.session_state.show_new_profile_form = not st.session_state.show_new_profile_form
    
    # Profile selection
    profiles = load_profiles()
    profile_names = [f"{p.get('first_name', '')} {p.get('last_name', '')}" for p in profiles]
    profile_names.append("Create New Profile")
    
    # Set default index based on previously selected profile
    default_index = len(profile_names) - 1 if st.session_state.current_profile is None else profile_names.index(f"{st.session_state.current_profile.get('first_name', '')} {st.session_state.current_profile.get('last_name', '')}")
    
    selected_profile = st.selectbox(
        "Select or Create Profile",
        options=profile_names,
        index=default_index,
        key="profile_selector"
    )
    
    # Update session state with the selected profile
    if selected_profile != st.session_state.current_profile_name or not st.session_state.current_profile:
        st.session_state.current_profile_name = selected_profile
        selected_profile_data = next((p for p in profiles if f"{p['first_name']} {p['last_name']}" == selected_profile), None)
        if selected_profile_data:
            st.session_state.current_profile = selected_profile_data
    
    # Show new profile form when button is clicked
    if st.session_state.show_new_profile_form:
        with st.form("profile_form"):
            st.subheader("Create New Profile")
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email (optional)")
            linkedin_url = st.text_input("LinkedIn URL (optional)")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Profile")
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_new_profile_form = False
                    st.rerun()
            
            if submit:
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
                    st.session_state.show_new_profile_form = False
                    st.rerun()
                else:
                    st.error("First name and last name are required")

# Main content
if st.session_state.current_profile:
    profile = st.session_state.current_profile
    
    st.markdown(f"""
    <div class="header-with-icon">
        <h1>Content Strategy for {profile['first_name']} {profile['last_name']}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Update section headers with consistent styling
    st.markdown("""
    <div class="header-with-icon">
        <h2>👥 Customer Data</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Customer Data Section
    with st.form("customer_data_form"):
        st.markdown("""
        <style>
        [data-testid="stForm"] {
            border: 1px solid #E0E0E0;
            border-radius: 12px;
            padding: 2rem;
            background-color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        
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
                save_profile_data({"profile_id": profile["profile_id"], **update_data})
                st.success("Customer data saved!")
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
    st.markdown("""
    <div class="header-with-icon">
        <h2>🎯 Content Strategy</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate strategy button
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Generate Content Strategy", key="generate_strategy_btn", use_container_width=True):
            with st.spinner("Generating content strategy based on your customer data..."):
                if generate_strategy(profile["profile_id"]):
                    st.success("Strategy generated!")
                    st.rerun()
                else:
                    st.error("Failed to generate strategy")
    
    # Display and edit strategy
    strategy = profile.get("content_strategy", "")
    if strategy:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Current Strategy")
            strategy_text = st.text_area("Content Strategy", value=strategy, height=300, key="strategy_text")
            
            # Save button for manual edits
            if st.button("Save Strategy", key="save_strategy_btn"):
                if save_profile_data({"profile_id": profile["profile_id"], "content_strategy": strategy_text}):
                    st.success("Strategy saved!")
                    st.rerun()
        
        with col2:
            st.subheader("Strategy Feedback")
            feedback = st.text_area("Provide feedback to improve the strategy:", height=150, key="strategy_feedback")
            
            if st.button("Update Based on Feedback", key="update_strategy_feedback_btn"):
                if feedback:
                    with st.spinner("Updating strategy based on feedback..."):
                        st.session_state.previous_strategy = strategy_text
                        try:
                            response = openai_client.chat.completions.create(
                                model="gpt-4",
                                messages=[{"role": "user", "content": feedback}],
                                temperature=0.7,
                                max_tokens=1000
                            )
                            new_strategy = response.choices[0].message.content
                            if save_profile_data({"profile_id": profile["profile_id"], "content_strategy": new_strategy}):
                                st.success("Strategy updated based on feedback!")
                                st.session_state.profile_data = load_profile_data(profile["profile_id"])
                                st.rerun()
                            else:
                                st.error("Failed to save updated strategy")
                        except Exception as e:
                            st.error(f"Error updating strategy: {e}")
                else:
                    st.warning("Please provide feedback before updating")
            
            # Undo button
            if st.session_state.previous_strategy:
                if st.button("Undo Last Change", key="undo_strategy_btn"):
                    if save_profile_data({"profile_id": profile["profile_id"], "content_strategy": st.session_state.previous_strategy}):
                        st.success("Strategy restored to previous version!")
                        st.session_state.profile_data = load_profile_data(profile["profile_id"])
                        st.rerun()
                    else:
                        st.error("Failed to restore previous strategy")
    else:
        st.info("No strategy generated yet. Click the 'Generate Content Strategy' button above to create one based on your customer data.")
    
    # 3. Content Pillars Section
    st.markdown("""
    <div class="header-with-icon">
        <h2>📌 Content Pillars</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Generate pillars button
        if st.button("Generate Content Pillars", key="generate_pillars_btn"):
            with st.spinner("Generating content pillars based on your data..."):
                if generate_pillars(profile["profile_id"]):
                    st.success("Pillars generated!")
                    st.session_state.profile_data = load_profile_data(profile["profile_id"])
                    st.rerun()
                else:
                    st.error("Failed to generate pillars")
        
        with st.form(key="pillars_form"):
            # Ensure pillars is a list, even if None
            pillars = profile.get("content_pillars", []) or []
            
            for i in range(3):
                pillar = st.text_input(f"Pillar {i+1}", value=pillars[i] if i < len(pillars) else "", key=f"pillar_{i+1}")
                if i >= len(pillars):
                    pillars.append(pillar)
                else:
                    pillars[i] = pillar
            
            if st.form_submit_button("Save Pillars"):
                st.session_state.previous_pillars = profile.get("content_pillars", [])
                if save_profile_data({"profile_id": profile["profile_id"], "content_pillars": pillars}):
                    st.success("Pillars saved!")
                    st.session_state.profile_data = load_profile_data(profile["profile_id"])
                else:
                    st.error("Failed to save pillars")
    
    with col2:
        st.subheader("Pillar Feedback")
        feedback = st.text_area("Provide feedback to improve the pillars:", height=150, key="pillar_feedback")
        
        if st.button("Update Based on Feedback", key="update_pillars_feedback_btn"):
            if feedback:
                with st.spinner("Updating pillars based on feedback..."):
                    st.session_state.previous_pillars = profile.get("content_pillars", [])
                    try:
                        current_pillars = profile.get("content_pillars", [])
                        prompt = f"""Current content themes:
                        {', '.join(current_pillars)}
                        
                        User feedback:
                        {feedback}
                        
                        Based on this feedback, generate 3 improved content themes. Each theme should be a complete sentence that captures a specific area of expertise, experience, or value the person brings.

                        Each theme should be:
                        - A complete sentence
                        - Focused on a unique aspect (no overlap between themes)
                        - Specific enough to generate multiple content pieces from
                        - Written from a position of authority and experience
                        - Incorporating the user's feedback while maintaining professionalism

                        Format the response as a list of exactly 3 sentence-length themes, one per line.
                        """
                        
                        response = openai_client.chat.completions.create(
                            model="gpt-4",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.7,
                            max_tokens=300
                        )
                        
                        new_pillars = response.choices[0].message.content.strip().split('\n')[:3]
                        if save_profile_data({"profile_id": profile["profile_id"], "content_pillars": new_pillars}):
                            st.success("Pillars updated based on feedback!")
                            st.session_state.profile_data = load_profile_data(profile["profile_id"])
                            st.rerun()
                        else:
                            st.error("Failed to save updated pillars")
                    except Exception as e:
                        st.error(f"Error updating pillars: {e}")
            else:
                st.warning("Please provide feedback before updating")
        
        # Undo button
        if st.session_state.previous_pillars:
            if st.button("Undo Last Change", key="undo_pillars_btn"):
                if save_profile_data({"profile_id": profile["profile_id"], "content_pillars": st.session_state.previous_pillars}):
                    st.success("Pillars restored to previous version!")
                    st.session_state.profile_data = load_profile_data(profile["profile_id"])
                    st.rerun()
                else:
                    st.error("Failed to restore previous pillars")
    
    # 4. LinkedIn Prompts Section
    st.markdown("""
    <div class="header-with-icon">
        <h2>💡 LinkedIn Prompts</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Add number input for prompt count
    col1, col2 = st.columns([2, 1])
    with col1:
        num_prompts = st.number_input("Number of prompts to generate:", min_value=1, max_value=50, value=30, step=1, help="Choose how many prompts you want to generate (maximum 50)")
    
    # First, generate a sample prompt
    if st.button("Generate Sample Prompt", key="generate_sample_btn"):
        with st.spinner("Generating a sample prompt based on your content pillars..."):
            try:
                pillars = profile.get("content_pillars", [])
                if not pillars:
                    st.warning("Please generate content pillars first!")
                else:
                    sample_prompt = f"""Generate 1 unique LinkedIn post prompt based on one of these content pillars:
Content Pillars: {', '.join(pillars)}

The prompt should be framed as either:
1. A specific question the user can answer based on their experience
2. A story prompt about a specific moment or lesson from their career
3. A concrete example or case they can share from their work

Make it personal and specific, making it easy for the user to write about their own experiences and insights.

Return ONLY a JSON object with these exact keys:
- prompt: A specific question or story prompt they can answer from experience
- hook: An attention-grabbing opening line that sets up their story
- type_of_post: Must be EXACTLY one of these (no variations):
  - First-Person Anecdote
  - Listicle with a Hook
  - Educational How-To Post
  - Thought Leadership/Opinion Piece
  - Case Study/Success Story
  - Engagement-Driven Question

Return the response in this exact format:
{{
    "prompt": "Tell us about a time when...",
    "hook": "Last year, I discovered...",
    "type_of_post": "First-Person Anecdote"
}}"""

                    response = openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a LinkedIn content expert. Return only a valid JSON object with the specified format."},
                            {"role": "user", "content": sample_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )

                    sample = json.loads(response.choices[0].message.content)
                    
                    st.markdown("### 📝 Sample Prompt")
                    st.markdown(f"""
                    **Type:** {sample['type_of_post']}
                    
                    **Hook:** {sample['hook']}
                    
                    **Prompt:** {sample['prompt']}
                    """)
                    
                    # If they like the style, they can generate more
                    if st.button(f"Generate {num_prompts} More Like This", key="generate_more_btn"):
                        with st.spinner(f"Generating {num_prompts} LinkedIn prompts based on your strategy..."):
                            if generate_prompts(profile["profile_id"], num_prompts):
                                st.success("Prompts generated!")
                                st.session_state.profile_data = load_profile_data(profile["profile_id"])
                                st.rerun()
                            else:
                                st.error("Failed to generate prompts")
            except Exception as e:
                st.error(f"Error generating sample prompt: {e}")
    
    # Display prompts
    prompts = profile.get("linkedin_prompts", [])
    if prompts:
        st.write(f"Found {len(prompts)} prompts")
        
        # Add a search box to filter prompts
        search_term = st.text_input("Search prompts...", "", key="prompt_search").lower()
        
        for i, prompt in enumerate(prompts):
            # Skip if doesn't match search
            if search_term and search_term not in prompt.get("prompt", "").lower():
                continue
                
            with st.expander(f"Prompt {i+1}: {prompt.get('type_of_post', '')}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Prompt:**")
                    st.write(prompt.get("prompt", ""))
                    st.markdown("**Hook:**")
                    st.write(prompt.get("hook", ""))
                    st.markdown("**Type of Post:**")
                    st.write(prompt.get("type_of_post", ""))
                
                with col2:
                    prompt_text = f"""Prompt: {prompt.get('prompt', '')}
Hook: {prompt.get('hook', '')}
Type of Post: {prompt.get('type_of_post', '')}"""
                    
                    if st.button("Copy to Clipboard", key=f"copy_prompt_{i}"):
                        st.write("Copied to clipboard!")
                        st.code(prompt_text, language=None)
                    
                    # Create a unique key for each Write Post button by including timestamp
                    write_post_key = f"write_post_{i}_{prompt.get('type_of_post', '').replace(' ', '_')}"
                    if st.button("✍️ Write Post", key=write_post_key):
                        with st.spinner("Drafting LinkedIn post..."):
                            try:
                                write_prompt = f"""Write a complete LinkedIn post based on this prompt:

Hook: {prompt.get('hook', '')}
Main Content: {prompt.get('prompt', '')}
Type of Post: {prompt.get('type_of_post', '')}

Guidelines:
1. Start with the hook to grab attention
2. Develop the main content into a compelling narrative
3. Use appropriate formatting (line breaks, emojis, bullet points)
4. End with a clear call-to-action
5. Keep it professional but engaging
6. Use LinkedIn-style formatting (short paragraphs, spaces between paragraphs)
7. Include 3-5 relevant hashtags at the end

Return only the formatted post, ready to be copied to LinkedIn."""

                                response = openai_client.chat.completions.create(
                                    model="gpt-4",
                                    messages=[
                                        {"role": "system", "content": "You are a LinkedIn content expert who writes engaging, professional posts."},
                                        {"role": "user", "content": write_prompt}
                                    ],
                                    temperature=0.7,
                                    max_tokens=1000
                                )
                                
                                drafted_post = response.choices[0].message.content
                                st.markdown("### 📝 Drafted Post")
                                st.markdown(drafted_post)
                                st.code(drafted_post, language=None)
                            except Exception as e:
                                st.error(f"Error drafting post: {e}")
    else:
        st.info("No prompts generated yet. Click the 'Generate Prompts' button above to create prompts based on your strategy.")
else:
    st.info("Please select or create a profile to get started.")
