import os
import logging
from openai import AsyncOpenAI, RateLimitError, APIConnectionError
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

# Replace raw print statements with structured logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = AsyncOpenAI()

class DraftVariants(BaseModel):
    variant_a: str
    variant_b: str
    variant_c: str

def is_retryable(ex: BaseException) -> bool:
    """
    Tenacity predicate: only retry on transient network/rate-limit errors.
    Hard failures (401 AuthenticationError, 400 BadRequestError, etc.) are
    not retryable — re-raising them immediately saves up to 14 wasted seconds
    of exponential backoff on a call that will never succeed.
    """
    return isinstance(ex, (RateLimitError, APIConnectionError))


# Exponential backoff: up to 3 attempts, waiting 2→4→8 seconds between retries.
# retry= guard ensures only transient errors trigger a retry cycle.
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(is_retryable),
    reraise=True,
)
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

    system_prompt = """You are a Principal Enterprise Account Executive at Sococo (virtual office software).
        You are writing cold outbound to C-level executives. You do NOT sound like a salesperson. You sound like an industry peer pointing out a hidden operational tax.

        RULES OF ENGAGEMENT:
        1. STRICTLY FORBIDDEN: "Hi", "Hope this finds you well", "let's eliminate", "would love to connect", "friction points", "streamline". 
        2. Tone: Clinical, provocative, asymmetric. Exactly 2 sentences. Lowercase subjects.
        3. Methodology: 'The Challenger Sale'. Expose a vulnerability tied directly to their exact headcount, growth rate, or funding stage. Prove you did the research.
        
        VARIANTS TO GENERATE IN JSON:
        {
            "message_draft_a": "[Variant A - The 'Hidden Tax': A 2-sentence blunt observation about the coordination cost of their exact growth rate. End with a polarizing, hard question.]",
            "message_draft_b": "[Variant B - The 'Pattern Interrupt': A single, jarring sentence highlighting how their specific funding stage usually breaks remote culture.]",
            "message_draft_c": "[Variant C - The 'Blunt Force': An ultra-brief financial provocation about capital wasted on disconnected teams.]"
        }
        """

    completion = await client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate outreach for this lead:\n{telemetry}"}
        ],
        response_format=DraftVariants,
        temperature=0.6,  # Lower temperature for sharper, less "creative/fluffy" copy
    )

    drafts = completion.choices[0].message.parsed

    return {
        "message_draft_a": drafts.variant_a,
        "message_draft_b": drafts.variant_b,
        "message_draft_c": drafts.variant_c,
    }