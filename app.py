import streamlit as st
import requests
import json
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# API configuration
API_URL = os.getenv("API_URL", "https://mylance-api.herokuapp.com")

# Import the main application
from Home import main

if __name__ == "__main__":
    main() 