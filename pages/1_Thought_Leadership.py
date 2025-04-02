import streamlit as st
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Server configuration
SERVER_URL = "http://localhost:8000"

def save_thought_leadership(strategy: str) -> bool:
    """Save global thought leadership strategy to the backend"""
    try:
        response = requests.post(
            f"{SERVER_URL}/save-thought-leadership",
            json={"strategy": strategy}
        )
        response.raise_for_status()
        st.success("Thought leadership strategy saved successfully!")
        return True
    except Exception as e:
        st.error(f"Error saving thought leadership strategy: {str(e)}")
        logging.error(f"Error saving thought leadership strategy: {e}", exc_info=True)
        return False

def get_thought_leadership() -> str:
    """Get global thought leadership strategy from the backend"""
    try:
        response = requests.get(f"{SERVER_URL}/get-thought-leadership")
        response.raise_for_status()
        return response.json().get("strategy", "")
    except Exception as e:
        st.error(f"Error loading thought leadership strategy: {str(e)}")
        logging.error(f"Error loading thought leadership strategy: {e}", exc_info=True)
        return ""

def main():
    st.title("Mylance Thought Leadership Strategy")
    
    # Add some context about what this page is for
    st.markdown("""
    This page contains Mylance's global thought leadership strategy. This strategy will be used across all content generation
    to maintain consistent messaging and positioning.
    
    Use this space to define:
    - Key themes and topics
    - Core messaging points
    - Brand voice and tone
    - Content pillars
    - Target audience perspectives
    """)
    
    # Get existing strategy
    current_strategy = get_thought_leadership()
    
    # Create a text area for the strategy
    strategy = st.text_area(
        "Global Thought Leadership Strategy",
        value=current_strategy,
        height=400,
        help="Write the detailed thought leadership strategy here. This will be used across all content generation to maintain consistent messaging."
    )
    
    # Add a save button
    if st.button("Save Global Strategy"):
        if strategy.strip():  # Only save if there's content
            save_thought_leadership(strategy)
        else:
            st.warning("Please enter a strategy before saving.")

if __name__ == "__main__":
    main()
