import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import supabase
from datetime import datetime, timedelta, timezone
import asyncio
from typing import List, Dict, Any, Optional
import json
import logging
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load values from .env
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Check if environment variables are loaded
if not all([supabase_url, supabase_key, openai_api_key]):
    logging.error("Missing environment variables. Ensure SUPABASE_URL, SUPABASE_KEY, and OPENAI_API_KEY are set.")
    raise ValueError("Missing environment variables.")

# Initialize global variables with default values
ideal_customer = ""
ideal_problem = ""
brand_philosophy = ""
primary_strategy = ""
secondary_strategy = ""
brand_voice = ""
voice_examples = []
pillars = {
    "pillar_1": "",
    "pillar_2": "",
    "pillar_3": ""
}

# Initialize Supabase client
try:
    supabase_client: Client = create_client(supabase_url, supabase_key)
    logging.info("Supabase client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Supabase client: {e}")
    raise

# Initialize OpenAI client
try:
    client = OpenAI(api_key=openai_api_key)
    logging.info("OpenAI client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize OpenAI client: {e}")
    raise

# Cache configuration
CACHE_DURATION = timedelta(hours=24)
brand_analysis_cache = {
    "data": None,
    "timestamp": None
}

# Load initial data from Supabase
def load_initial_data():
    """Load initial data from Supabase"""
    logging.info("Attempting to load initial data from Supabase...")
    try:
        response = supabase_client.table("brand_analysis").select("*").limit(1).execute()
        logging.info(f"Supabase response for load_initial_data: {response}")
        if response.data and len(response.data) > 0:
            data = response.data[0]
            global ideal_customer, ideal_problem, brand_philosophy, primary_strategy, secondary_strategy, brand_voice, voice_examples, pillars
            
            ideal_customer = data.get("ideal_customer", "")
            ideal_problem = data.get("ideal_problem", "")
            brand_philosophy = data.get("brand_philosophy", "")
            primary_strategy = data.get("primary_strategy", "")
            secondary_strategy = data.get("secondary_strategy", "")
            brand_voice = data.get("brand_voice", "")
            voice_examples = data.get("voice_examples", [])
            pillars = data.get("pillars", {
                "pillar_1": "",
                "pillar_2": "",
                "pillar_3": ""
            })
            logging.info(f"Successfully loaded initial data: Customer='{ideal_customer}', Problem='{ideal_problem}', Philosophy='{brand_philosophy}'")
            return True
        else:
            logging.warning("No data found in brand_analysis table during initial load.")
            return False
    except Exception as e:
        logging.error(f"Error loading initial data from Supabase: {e}", exc_info=True)
        return False

# Load initial data on startup
if not load_initial_data():
    logging.warning("Initial data load failed or returned no data. Using default global variables.")

print("SUPABASE_URL:", supabase_url)  # Debugging

app = FastAPI()

class ProfileData(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    linkedin_url: str | None = None

class ProfileListItem(BaseModel):
    profile_id: str
    full_name: str

class GeneratePostRequest(BaseModel):
    recent_post: str
    impressions: int
    likes: int
    comments: int
    tone_description: str

class AddPostRequest(ProfileData): # Inherit ProfileData
    content: str
    impressions: int
    likes: int
    comments: int

class IdealCustomerRequest(ProfileData):
    customer: str
    problem: str
    philosophy: str = ""

class StrategyRequest(ProfileData):
    customer: str
    problem: str
    philosophy: str

class StrategiesUpdateRequest(ProfileData):
    primary_strategy: str
    secondary_strategy: str

class ProfileCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    linkedin_url: str | None = None

class Post(BaseModel):
    id: str
    content: str
    impressions: int | None = None
    likes: int | None = None
    comments: int | None = None
    embedding: list[float] | None = None
    created_at: datetime | None = None
    profile_id: str | None = None # Add profile_id here for response if needed

# Add new models for customer data
class CustomerDataRequest(ProfileData):
    ideal_customer: str
    icp_pain_points: str
    unique_value: str  # Changed from customer_value_add
    proof_points: str  # Changed from customer_proof_points
    energizing_topics: str
    decision_maker: str  # Changed from ideal_decision_maker

class ContentStrategyRequest(ProfileData):
    ideal_customer: str
    icp_pain_points: str
    unique_value: str  # Changed from customer_value_add
    proof_points: str  # Changed from customer_proof_points
    energizing_topics: str
    decision_maker: str  # Changed from ideal_decision_maker

class ThoughtLeadershipRequest(BaseModel):
    strategy: str

class LinkedInPrompt(BaseModel):
    prompt: str
    hook: str
    style: str

class ProfileUpdate(BaseModel):
    id: str
    data: dict

@app.post("/save-ideal-customer")
async def save_ideal_customer(request: IdealCustomerRequest):
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Saving ideal customer..." ) # Simplified log
    try:
        upsert_data = {
            "ideal_customer": request.customer,
            "ideal_problem": request.problem,
            "brand_philosophy": request.philosophy,
            "updated_at": datetime.now().isoformat()
        }
        # Use profile_id in the .eq() filter for update/upsert targeting
        response = supabase_client.table("brand_analysis").update(upsert_data).eq("profile_id", profile_id).execute()
        logging.info(f"Profile [{profile_id}]: Supabase response for save_ideal_customer: {response}")
        # Check if update affected any rows, if not maybe insert (or rely on profile existing)
        if not response.data and not hasattr(response, 'error'): # Check if update succeeded but affected 0 rows
             logging.warning(f"Profile [{profile_id}]: Save ideal customer didn't update any rows. Profile might not exist?")
             # Decide if we should insert here or assume profile exists
             # For now, we just log.

        if hasattr(response, 'error') and response.error:
             logging.error(f"Profile [{profile_id}]: Error saving ideal customer data: {response.error}")
             raise HTTPException(status_code=500, detail="Failed to save ideal customer data")

        logging.info(f"Profile [{profile_id}]: Successfully saved ideal customer data.")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Profile [{profile_id}]: Error in save_ideal_customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-strategies")
async def save_strategies(request: StrategiesUpdateRequest):
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Saving strategies...") # Simplified log
    try:
        update_data = {
            "primary_strategy": request.primary_strategy,
            "secondary_strategy": request.secondary_strategy,
            "updated_at": datetime.now().isoformat()
        }
        response = supabase_client.table("brand_analysis").update(update_data).eq("profile_id", profile_id).execute()
        logging.info(f"Profile [{profile_id}]: Supabase response for save_strategies: {response}")
        # Add check for affected rows similar to save_ideal_customer if needed

        if hasattr(response, 'error') and response.error:
             logging.error(f"Profile [{profile_id}]: Error saving strategies: {response.error}")
             raise HTTPException(status_code=500, detail="Failed to save strategies")

        logging.info(f"Profile [{profile_id}]: Successfully saved strategies.")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Profile [{profile_id}]: Error in save_strategies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while saving strategies.")

@app.post("/get-initial-data") 
async def get_initial_data_endpoint(request: ProfileData): 
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Received request for initial data.")
    try:
        response = supabase_client.table("brand_analysis").select("*").eq("profile_id", profile_id).limit(1).execute()
        if response.data:
             data = response.data[0]
             # Log the raw data for debugging
             logging.info(f"Profile [{profile_id}]: Raw data from Supabase: {data}")
             
             # Get all customer data fields
             customer_value = data.get("ideal_customer", "")
             problem_value = data.get("ideal_problem", "")
             icp_pain_points = data.get("icp_pain_points", "")
             unique_value = data.get("unique_value", "")
             proof_points = data.get("proof_points", "")
             energizing_topics = data.get("energizing_topics", "")
             decision_maker = data.get("decision_maker", "")
             
             # Log the extracted values
             logging.info(f"Profile [{profile_id}]: Extracted customer value: '{customer_value}'")
             logging.info(f"Profile [{profile_id}]: Extracted problem value: '{problem_value}'")
             logging.info(f"Profile [{profile_id}]: Extracted pain points: '{icp_pain_points}'")
             logging.info(f"Profile [{profile_id}]: Extracted unique value: '{unique_value}'")
             
             return {
                "profile_id": data.get("profile_id", ""),
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
                "email": data.get("email", ""),
                "linkedin_url": data.get("linkedin_url", ""),
                "ideal_customer": customer_value,
                "ideal_problem": problem_value,
                "icp_pain_points": icp_pain_points,
                "unique_value": unique_value,
                "proof_points": proof_points,
                "energizing_topics": energizing_topics,
                "decision_maker": decision_maker,
                "brand_philosophy": data.get("brand_philosophy", ""),
                "primary_strategy": data.get("primary_strategy", ""),
                "secondary_strategy": data.get("secondary_strategy", ""),
                "brand_voice": data.get("brand_voice", ""),
                "voice_examples": data.get("voice_examples", [])
             }
        else: # Return defaults
            logging.info(f"Profile [{profile_id}]: No data found, returning defaults")
            return {
                "profile_id": profile_id,
                "first_name": "",
                "last_name": "",
                "email": "",
                "linkedin_url": "",
                "ideal_customer": "",
                "ideal_problem": "",
                "icp_pain_points": "",
                "unique_value": "",
                "proof_points": "",
                "energizing_topics": "",
                "decision_maker": "",
                "brand_philosophy": "",
                "primary_strategy": "",
                "secondary_strategy": "",
                "brand_voice": "",
                "voice_examples": []
            }

    except Exception as e:
        logging.error(f"Profile [{profile_id}]: Error in get_initial_data_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve user data.")

@app.post("/analyze-brand") 
async def analyze_brand(request: ProfileData):
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Received request to analyze brand.")
    
    # Fetch user's posts using profile_id
    try:
        posts_response = supabase_client.table("posts").select("content").eq("profile_id", profile_id).order("likes", desc=True).limit(5).execute()
        # ... (rest of the logic, ensuring analysis results are saved using profile_id) ...
        pass # Placeholder
        # Ensure the final db update uses .eq("profile_id", profile_id)
        # Ensure the final return includes profile-specific data

        # --- Mockup of the save part --- 
        # Assume results parsed into: parsed_voice, parsed_examples, parsed_primary, etc.
        try:
            logging.info(f"Profile [{profile_id}]: Saving brand analysis results to Supabase.")
            update_data = { # No profile_id needed here, targeted by .eq()
                "ideal_customer": parsed_customer,
                "ideal_problem": parsed_problem,
                # ... other parsed fields ...
                 "updated_at": datetime.now().isoformat()
            }
            db_response = supabase_client.table("brand_analysis").update(update_data).eq("profile_id", profile_id).execute()
            # ... logging and error check ...
        except Exception as e:
             logging.error(f"Profile [{profile_id}]: Error saving analysis results: {e}", exc_info=True)
        
        # Fetch current philosophy to include in return
        # ... (Fetch philosophy logic using profile_id) ...

        # Return analysis_result dictionary (same structure as before)
        return analysis_result # Make sure analysis_result is defined and populated

    except Exception as e:
         logging.error(f"Profile [{profile_id}]: Error in analyze_brand: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Failed during brand analysis.")


@app.post("/generate-strategy") 
async def generate_strategy(request: StrategyRequest): # Already includes profile_id via inheritance
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Generating strategy...") # Simplified log
    try:
        # ... (OpenAI call logic remains the same) ...
        recommendation = json.loads(response.choices[0].message.content)

        # Save the recommendation using profile_id
        logging.info(f"Profile [{profile_id}]: Saving generated strategy recommendation.")
        strategy_update_data = {
            "primary_strategy": recommendation.get("strategy", ""),
            "secondary_strategy": recommendation.get("rationale", ""),
            # Maybe update customer/problem/philosophy too if needed?
            "updated_at": datetime.now().isoformat()
        }
        db_response = supabase_client.table("brand_analysis").update(strategy_update_data).eq("profile_id", profile_id).execute()
        # ... (logging and error check for db_response) ...
        return {"recommendation": recommendation}
    except Exception as e:
        # ... (error handling) ...
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-topics") 
async def generate_topics(request: ProfileData): # Inherits profile_id
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Generating topics.")
    
    # Fetch current strategy, customer, problem for this profile_id
    try:
        user_data_resp = supabase_client.table("brand_analysis").select("primary_strategy, secondary_strategy, ideal_customer, ideal_problem").eq("profile_id", profile_id).limit(1).execute()
        # ... (rest of the logic using fetched user_data, OpenAI call, topic parsing) ...
        pass # Placeholder
        return {"topics": topics} # Assuming topics is parsed list
    except Exception as e:
        logging.error(f"Profile [{profile_id}]: Error generating topics: {e}", exc_info=True)
        return {"topics": []}

@app.post("/generate-posts") 
async def generate_posts(data: GeneratePostRequest): # Still doesn't need profile_id directly
    # ... (logic remains the same, assuming context is in data) ...
    pass # Placeholder
    return {"posts": posts}

@app.post("/add-post")
async def add_post(data: AddPostRequest): # Already includes profile_id
    profile_id = data.profile_id
    logging.info(f"Profile [{profile_id}]: Adding post.")
    try:
        response = supabase_client.table("posts").insert({
            "profile_id": profile_id, # Include profile_id
            "content": data.content,
            # ... other fields ...
        }).execute()
        # ... (Error handling) ...
        return {"status": "success"}
    except Exception as e:
        # ... (Error handling) ...
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-posts") 
async def get_posts(request: ProfileData): # Inherits profile_id
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Retrieving posts.")
    try:
        # Filter posts by profile_id
        response = supabase_client.table("posts").select("*").eq("profile_id", profile_id).execute()
        return {"posts": response.data if response.data else []}
    except Exception as e:
        # ... (Error handling) ...
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed-posts") 
async def embed_existing_posts(request: ProfileData): # Inherits profile_id
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Embedding posts.")
    try:
        # Fetch posts for the specific profile_id
        response = supabase_client.table("posts").select("id, content").eq("profile_id", profile_id).is_("embedding", None).execute() # Only fetch posts needing embedding
        posts_to_embed = response.data
        # ... (rest of embedding logic, ensuring updates use .eq("id", post["id"])) ...
        updates = [] # Placeholder for actual update logic
        # Example loop (needs async gather etc.)
        # for post in posts_to_embed:
        #    embedding = await generate_embedding(post['content'])
        #    supabase_client.table("posts").update({"embedding": embedding}).eq("id", post["id"]).execute()
        #    updates.append(post['id'])
        pass # Placeholder for embedding logic
        return {"status": "success", "embedded_count": len(updates)}
    except Exception as e:
        # ... (Error handling) ...
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to fetch profiles for dropdown
@app.get("/get-profiles", response_model=list[ProfileListItem])
async def get_profiles():
    """Fetch all profiles (id, first_name, last_name) for the dropdown."""
    logging.info("Fetching list of profiles.")
    try:
        response = supabase_client.table("brand_analysis").select("profile_id, first_name, last_name").execute()
        profiles = []
        if response.data:
            for profile in response.data:
                full_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
                if not full_name:
                    full_name = f"Profile ({profile['profile_id'][:8]}...)" # Fallback name
                profiles.append(ProfileListItem(profile_id=profile['profile_id'], full_name=full_name))
        logging.info(f"Found {len(profiles)} profiles.")
        return profiles
    except Exception as e:
        logging.error(f"Error fetching profiles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch profiles")

# Endpoint to create a new profile
@app.post("/profiles")
async def create_profile(profile: ProfileData):
    """Create a new profile"""
    try:
        data = profile.dict(exclude_none=True)
        data["updated_at"] = datetime.now().isoformat()
        response = supabase_client.table("profiles").insert(data).execute()
        return response.data[0]
    except Exception as e:
        logging.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create profile")

# Add new endpoints for customer data
@app.post("/save-customer-data")
async def save_customer_data(request: CustomerDataRequest):
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Saving customer data...")
    try:
        update_data = {
            "ideal_customer": request.ideal_customer,
            "icp_pain_points": request.icp_pain_points,
            "unique_value": request.unique_value,  # Changed from customer_value_add
            "proof_points": request.proof_points,  # Changed from customer_proof_points
            "energizing_topics": request.energizing_topics,
            "decision_maker": request.decision_maker,  # Changed from ideal_decision_maker
            "updated_at": datetime.now().isoformat()
        }
        response = supabase_client.table("brand_analysis").update(update_data).eq("profile_id", profile_id).execute()
        
        if hasattr(response, 'error') and response.error:
            logging.error(f"Profile [{profile_id}]: Error saving customer data: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to save customer data")
        
        logging.info(f"Profile [{profile_id}]: Successfully saved customer data")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Profile [{profile_id}]: Error in save_customer_data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-customer-data")
async def get_customer_data(request: ProfileData):
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Retrieving customer data...")
    try:
        response = supabase_client.table("brand_analysis").select(
            "ideal_customer",
            "icp_pain_points",  # Fixed: Changed from ideal_problem to icp_pain_points
            "unique_value",
            "proof_points",
            "energizing_topics",
            "decision_maker"
        ).eq("profile_id", profile_id).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            data = response.data[0]
            return {
                "ideal_customer": data.get("ideal_customer", ""),
                "icp_pain_points": data.get("icp_pain_points", ""),  # Fixed: Changed from ideal_problem to icp_pain_points
                "unique_value": data.get("unique_value", ""),
                "proof_points": data.get("proof_points", ""),
                "energizing_topics": data.get("energizing_topics", ""),
                "decision_maker": data.get("decision_maker", "")
            }
        else:
            return {
                "ideal_customer": "",
                "icp_pain_points": "",  # Fixed: Changed from ideal_problem to icp_pain_points
                "unique_value": "",
                "proof_points": "",
                "energizing_topics": "",
                "decision_maker": ""
            }
    except Exception as e:
        logging.error(f"Profile [{profile_id}]: Error in get_customer_data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve customer data")

@app.post("/generate-content-strategy")
async def generate_content_strategy(request: ContentStrategyRequest):
    profile_id = request.profile_id
    logging.info(f"Profile [{profile_id}]: Generating content strategy...")
    try:
        # Create a prompt for the content strategy generation
        prompt = f"""Based on the following customer data, generate a comprehensive content strategy:

Ideal Customer: {request.ideal_customer}
Pain Points: {request.icp_pain_points}
Value Add: {request.unique_value}
Proof Points: {request.proof_points}
Energizing Topics: {request.energizing_topics}
Ideal Decision Maker: {request.decision_maker}

Please provide:
1. Primary Content Strategy
2. Secondary Content Strategy
3. Content Pillars (3-4 key themes)
4. Brand Voice Guidelines
5. Key Topics to Focus On

Format the response as a JSON object with these keys:
{{
    "primary_strategy": "string",
    "secondary_strategy": "string",
    "content_pillars": ["string"],
    "brand_voice": "string",
    "key_topics": ["string"]
}}"""

        # Call OpenAI to generate the strategy
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a content strategy expert. Generate a comprehensive content strategy based on the provided customer data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # Parse the response
        strategy_data = json.loads(response.choices[0].message.content)
        
        # Save the generated strategy
        update_data = {
            "primary_strategy": strategy_data.get("primary_strategy", ""),
            "secondary_strategy": strategy_data.get("secondary_strategy", ""),
            "content_pillars": strategy_data.get("content_pillars", []),
            "brand_voice": strategy_data.get("brand_voice", ""),
            "key_topics": strategy_data.get("key_topics", []),
            "updated_at": datetime.now().isoformat()
        }
        
        db_response = supabase_client.table("brand_analysis").update(update_data).eq("profile_id", profile_id).execute()
        
        if hasattr(db_response, 'error') and db_response.error:
            logging.error(f"Profile [{profile_id}]: Error saving content strategy: {db_response.error}")
            raise HTTPException(status_code=500, detail="Failed to save content strategy")
        
        logging.info(f"Profile [{profile_id}]: Successfully generated and saved content strategy")
        return strategy_data
    except Exception as e:
        logging.error(f"Profile [{profile_id}]: Error in generate_content_strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# init-db likely doesn't make sense in a multi-user context, remove or rethink
# @app.post("/init-db")

@app.post("/save-thought-leadership")
async def save_thought_leadership(request: ThoughtLeadershipRequest):
    logging.info("Saving global thought leadership strategy...")
    try:
        update_data = {
            "key": "thought_leadership_strategy",
            "value": request.strategy,
            "updated_at": datetime.now().isoformat()
        }
        
        # First try to update
        response = supabase_client.table("global_settings").update(update_data).eq("key", "thought_leadership_strategy").execute()
        
        # If no rows were updated (first time), then insert
        if not response.data:
            response = supabase_client.table("global_settings").insert(update_data).execute()

        if hasattr(response, 'error') and response.error:
            logging.error(f"Error saving thought leadership strategy: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to save thought leadership strategy")

        logging.info("Successfully saved thought leadership strategy.")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error in save_thought_leadership: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while saving thought leadership strategy.")

@app.get("/get-thought-leadership")
async def get_thought_leadership():
    logging.info("Getting global thought leadership strategy...")
    try:
        response = supabase_client.table("global_settings").select("value").eq("key", "thought_leadership_strategy").limit(1).execute()
        
        if response.data and len(response.data) > 0:
            return {"strategy": response.data[0].get("value", "")}
        else:
            return {"strategy": ""}
    except Exception as e:
        logging.error(f"Error in get_thought_leadership: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while getting thought leadership strategy.")

@app.get("/profiles")
async def get_profiles():
    """Get all profiles"""
    try:
        response = supabase_client.table("profiles").select("*").execute()
        return response.data
    except Exception as e:
        logging.error(f"Error fetching profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profiles")

@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a specific profile"""
    try:
        response = supabase_client.table("profiles").select("*").eq("id", profile_id).single().execute()
        return response.data
    except Exception as e:
        logging.error(f"Error fetching profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

@app.put("/profiles/{profile_id}")
async def update_profile(profile_id: str, update: ProfileUpdate):
    """Update a profile"""
    try:
        # Extract the data from the update request
        update_data = update.data
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Update the profile
        response = supabase_client.table("profiles").update(update_data).eq("id", profile_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        return response.data[0]
    except Exception as e:
        logging.error(f"Error updating profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profiles/{profile_id}/generate-strategy")
async def generate_strategy(profile_id: str):
    """Generate content strategy based on customer data and Mylance strategy"""
    try:
        # Get profile data
        profile_response = supabase_client.table("profiles").select("*").eq("id", profile_id).execute()
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        profile = profile_response.data[0]

        # Get Mylance thought leadership strategy
        try:
            strategy_response = supabase_client.table("global_settings").select("value").eq("key", "thought_leadership_strategy").execute()
            mylance_strategy = strategy_response.data[0]["value"] if strategy_response.data else ""
        except Exception as e:
            logging.warning(f"Could not fetch thought leadership strategy: {e}")
            mylance_strategy = ""

        # Prepare the prompt for OpenAI
        prompt = f"""Based on the following customer data and Mylance's thought leadership strategy, generate a comprehensive content strategy:

Customer Data:
- Ideal Customer Profile: {profile.get('icp', 'Not specified')}
- Pain Points: {profile.get('icp_pain_points', 'Not specified')}
- Unique Value Add: {profile.get('unique_value', 'Not specified')}
- Proof Points: {profile.get('proof_points', 'Not specified')}
- Energizing Topics: {profile.get('energizing_topics', 'Not specified')}
- Decision Makers: {profile.get('decision_makers', 'Not specified')}

Mylance Thought Leadership Strategy:
{mylance_strategy}

Please generate a detailed content strategy that:
1. Aligns with the customer's target audience and pain points
2. Incorporates Mylance's thought leadership approach
3. Focuses on providing value and building authority
4. Includes specific content themes and topics
5. Outlines the tone and style of communication
6. Suggests content formats and distribution channels

Format the response as a JSON object with these keys:
{{
    "content_strategy": "string",
    "content_pillars": ["string", "string", "string"]
}}"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert content strategist who creates comprehensive, data-driven content strategies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # Extract the generated strategy
        generated_data = json.loads(response.choices[0].message.content)
        generated_strategy = generated_data.get("content_strategy", "")
        content_pillars = generated_data.get("content_pillars", [])

        # Update the profile with the generated strategy and pillars
        update_response = supabase_client.table("profiles").update({
            "content_strategy": generated_strategy,
            "content_pillars": content_pillars,
            "updated_at": datetime.now().isoformat()
        }).eq("id", profile_id).execute()

        if not update_response.data:
            raise HTTPException(status_code=500, detail="Failed to update profile with generated strategy")

        return {
            "content_strategy": generated_strategy,
            "content_pillars": content_pillars
        }

    except Exception as e:
        logging.error(f"Error generating strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate strategy")

@app.post("/profiles/{profile_id}/generate-prompts")
async def generate_prompts(profile_id: str):
    """Generate LinkedIn prompts based on strategy"""
    try:
        # Get profile data
        profile_response = supabase_client.table("profiles").select("*").eq("id", profile_id).execute()
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        profile = profile_response.data[0]

        # Prepare the prompt for OpenAI
        prompt = f"""Based on the following profile data, generate 30 LinkedIn prompts:

Customer Data:
- Ideal Customer Profile: {profile.get('icp', 'Not specified')}
- Pain Points: {profile.get('icp_pain_points', 'Not specified')}
- Unique Value Add: {profile.get('unique_value', 'Not specified')}
- Proof Points: {profile.get('proof_points', 'Not specified')}
- Energizing Topics: {profile.get('energizing_topics', 'Not specified')}
- Decision Makers: {profile.get('decision_makers', 'Not specified')}

Content Strategy:
{profile.get('content_strategy', 'Not specified')}

Content Pillars:
{', '.join(profile.get('content_pillars', []))}

Please generate 30 LinkedIn prompts that:
1. Align with the customer's target audience and pain points
2. Follow the content strategy and pillars
3. Include a mix of different styles (Professional, Casual, Storytelling, Educational, Conversational, Inspirational)
4. Each prompt should have:
   - The main prompt text
   - A hook to grab attention
   - A recommended style

Format the response as a JSON array of objects, each with these keys:
{{
    "prompt": "string",
    "hook": "string",
    "style": "string"
}}"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert LinkedIn content creator who creates engaging, value-driven posts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        # Extract the generated prompts
        prompts = json.loads(response.choices[0].message.content)

        # Update profile with generated prompts
        update_response = supabase_client.table("profiles").update({
            "linkedin_prompts": prompts,
            "updated_at": datetime.now().isoformat()
        }).eq("id", profile_id).execute()

        if not update_response.data:
            raise HTTPException(status_code=500, detail="Failed to update profile with generated prompts")

        return prompts

    except Exception as e:
        logging.error(f"Error generating prompts for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate prompts")

@app.post("/profiles/{profile_id}/update-strategy")
async def update_strategy(profile_id: str, feedback: dict):
    """Update content strategy based on feedback"""
    try:
        # Get current profile data
        profile_response = supabase_client.table("profiles").select("*").eq("id", profile_id).execute()
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = profile_response.data[0]
        current_strategy = profile.get("content_strategy", "")
        
        # Prepare the prompt for OpenAI
        prompt = f"""Based on the following content strategy and feedback, please provide an improved version of the strategy that addresses the feedback while maintaining the core message and goals.

Current Strategy:
{current_strategy}

Feedback:
{feedback['feedback']}

Please provide an improved version of the strategy that:
1. Addresses the specific feedback points
2. Maintains the core message and goals
3. Is clear and actionable
4. Follows the same format and structure

Return the response as a JSON object with a single key 'content_strategy' containing the updated strategy text."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a content strategy expert. Provide clear, actionable improvements to content strategies based on feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse the response
        try:
            # Get the content from the response
            content = response.choices[0].message.content
            # Try to parse as JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, use the content directly as the strategy
                result = {"content_strategy": content}
            
            updated_strategy = result.get("content_strategy", "")
            
            if not updated_strategy:
                raise HTTPException(status_code=500, detail="No strategy content received from OpenAI")
            
            # Update the profile in the database
            update_data = {
                "content_strategy": updated_strategy,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            update_response = supabase_client.table("profiles").update(update_data).eq("id", profile_id).execute()
            
            if not update_response.data:
                raise HTTPException(status_code=500, detail="Failed to update profile")
            
            return {"content_strategy": updated_strategy}
            
        except Exception as e:
            logging.error(f"Error processing OpenAI response: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing OpenAI response: {str(e)}")
            
    except Exception as e:
        logging.error(f"Error in update_strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))
