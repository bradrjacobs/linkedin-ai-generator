import os
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import asyncio
from typing import List, Dict, Any, Optional
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logging.error("Missing OPENAI_API_KEY environment variable.")
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=openai_api_key)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# In-memory storage
storage = {
    "thought_leadership_strategy": "",
    "profiles": [],
    "posts": [],
    "brand_analysis": []
}

class ThoughtLeadershipRequest(BaseModel):
    strategy: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/save-thought-leadership")
async def save_thought_leadership(request: ThoughtLeadershipRequest):
    logging.info("Saving global thought leadership strategy...")
    try:
        storage["thought_leadership_strategy"] = request.strategy
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error in save_thought_leadership: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while saving thought leadership strategy.")

@app.get("/get-thought-leadership")
async def get_thought_leadership():
    logging.info("Getting global thought leadership strategy...")
    try:
        return {"strategy": storage["thought_leadership_strategy"]}
    except Exception as e:
        logging.error(f"Error in get_thought_leadership: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while getting thought leadership strategy.")

# Rest of your API endpoints using storage instead of Supabase
# ... existing code ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
