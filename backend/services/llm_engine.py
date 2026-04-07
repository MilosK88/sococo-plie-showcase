# backend/services/llm_engine.py
import os
import json
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import List

# Initialize the async client. It automatically picks up OPENAI_API_KEY from the environment.
client = AsyncOpenAI()

# We define the exact structure we want OpenAI to return using Pydantic.
# This prevents the LLM from rambling or returning broken JSON.
class DraftVariants(BaseModel):
    variant_a: str
    variant_b: str
    variant_c: str

async def generate_reactivation_drafts(member: dict) -> dict:
    """
    Takes a churned member's telemetry and generates 3 hyper-personalized
    reactivation messages strictly in Serbian Ekavica.
    """
    
    # Construct the telemetry string to feed the AI
    # 1. Menjamo labelu koju šaljemo modelu. 
    # Umesto "Preferred Zone", jasno mu kažemo da je to tip članarine.
    telemetry = f"""
    Name: {member['first_name']}
    Churned Date: {member['churn_date']}
    Last Membership Package: {member['preferred_zone']}
    """

    # 2. Refaktorisana logika u promptu
    system_prompt = """
    You are an elite gym manager writing to a former member. 
    Your goal is reactivation. 
    
    RULES:
    1. You MUST write strictly in the Serbian ekavica dialect (e.g., 'ovde', 'promena', 'menjati'). Ijekavica is strictly forbidden.
    2. Tone must be casual, friendly, and non-corporate. Do not sound like a marketing robot. Use 'ti' (informal) but speak from a team perspective ('Nedostajes nam', 'Zeleli smo'). Never speak in first person perspective ('Zeleo sam', 'Zelela sam', 'Nedostajes mi').
    3. You MUST enforce a Personalization Fingerprint: You must explicitly mention their name. 
    4. CRITICAL DATA HANDLING: The data labeled 'Last Membership Package' represents their financial package (e.g., 'Mesecna clanarina', 'Dnevna clanarina'). DO NOT treat this as a physical space or an experience. If you mention it, use it only as an administrative time reference (e.g., "Proslo je neko vreme od tvoje poslednje mesecne clanarine" or "Znamo da ti je istekla dnevna clanarina"). DO NOT ask them if they 'remember' their membership.
    5. Keep messages under 3 sentences. Perfect for Viber/WhatsApp.
    
    Generate 3 distinct variants:
    - Variant A: Direct. Remind them of the time passed since their 'Churned Date' or their 'Last Membership Package' expiring, and invite them back for a workout.
    - Variant B: A casual "we miss you" check-in to see how their training is going. No sales pressure.
    - Variant C: Action-oriented, focusing on the atmosphere, good vibe, or equipment, inviting them for a new session.
    """

    try:
        completion = await client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06", # We use the model that supports strict structured parsing
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate drafts for this member:\n{telemetry}"}
            ],
            response_format=DraftVariants,
            temperature=0.7 # Slight creativity, but focused
        )

        # Extract the cleanly parsed Pydantic object
        drafts = completion.choices[0].message.parsed
        
        return {
            "message_draft_a": drafts.variant_a,
            "message_draft_b": drafts.variant_b,
            "message_draft_c": drafts.variant_c
        }

    except Exception as e:
        print(f"OpenAI Generation Failed for {member['first_name']}: {e}")
        return None