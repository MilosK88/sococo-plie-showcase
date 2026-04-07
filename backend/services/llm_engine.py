import os
import logging
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

# Replace raw print statements with structured logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = AsyncOpenAI()

class DraftVariants(BaseModel):
    variant_a: str
    variant_b: str
    variant_c: str

# Exponential backoff: Retry up to 3 times, waiting 2, 4, then 8 seconds between attempts.
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_reactivation_drafts(lead: dict) -> dict:
    """
    Ingests a B2B SaaS lead's telemetry and generates 3 high-converting, 
    dense cold outreach emails based on the Hormozi/Cardone B2B framework.
    """
    
    # We use .get() here to safely handle the transition from the old gym schema 
    # to the new B2B Canonical Lead Object schema we will build next.
    first_name = lead.get('first_name', 'there')
    company_context = lead.get('score_explanation', 'High priority prospect.')
    
    # In Phase 2, this telemetry will be populated by the Mock API branch outputs
    telemetry = f"""
    Target Name: {first_name}
    Lead Context / Signals: {company_context}
    Raw Data: {lead}
    """

    system_prompt = """
    You are an elite B2B Sales SDR for Sococo, a virtual office software company.
    Your goal is to generate 3 distinct cold outreach emails for a prospect.

    CORE MARKETING RULES (STRICT STRICT STRICT):
    1. Relevance > Fluff: NO "Hope you're doing well" or "Loved your recent post." Start immediately with a sharp observation about their business or context.
    2. Clarity > Cleverness: One problem, one idea, one ask per email.
    3. Keep it Short & Dense: 50–120 words max per email. Every sentence must earn its place.
    4. Write like a human: Casual, direct, confident. 6th-8th grade reading level. NO marketing buzzwords ("synergy", "unlock growth").
    5. Specific Proof: Use numbers and familiar context. Avoid generic claims like "we help companies grow."
    6. Low-Friction CTA: DO NOT ask for a 30-minute call. End with soft, low-friction asks: "Worth a quick look?", "Open to seeing how this works?", or "Should I send a quick breakdown?"
    7. Format: Include a punchy, lowercase subject line at the top of each variant (e.g., "Subj: scaling the team").

    Generate 3 distinct variants based on these archetypes:
    - Variant A (The "Why Now" Trigger): Focus on rapid scaling or hiring signals. Connect team growth to the inevitable wall of coordination friction and siloes.
    - Variant B (The Pattern Interrupt): Contrarian approach. Point out that adding more scheduled Zoom calls causes burnout; teams actually miss spontaneous, unstructured presence.
    - Variant C (Financial/Ops Blunt Force): Focus on efficiency. Mention tech stack bloat (Slack + Zoom + Notion) and how consolidating the "office" feel saves massive context-switching hours.
    """

    try:
        completion = await client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate outreach for this lead:\n{telemetry}"}
            ],
            response_format=DraftVariants,
            temperature=0.6 # Slightly lowered temperature for sharper, less "creative/fluffy" copy
        )

        drafts = completion.choices[0].message.parsed
        
        return {
            "message_draft_a": drafts.variant_a,
            "message_draft_b": drafts.variant_b,
            "message_draft_c": drafts.variant_c
        }

    except Exception as e:
        logger.error(f"OpenAI Generation Failed for {lead.get('first_name', 'Unknown')}: {e}")
        # Let tenacity catch the exception and retry. If it exhausts all retries, return None.
        raise e