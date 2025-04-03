import streamlit as st
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize session state for storage
if "thought_leadership_strategy" not in st.session_state:
    st.session_state.thought_leadership_strategy = ""

# Import the main application
from Home import main

if __name__ == "__main__":
    main() 