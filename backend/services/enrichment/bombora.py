import asyncio
import random
import hashlib

class BomboraMockClient:
    """Simulates Bombora Intent Data: high-intent topic spikes."""
    async def get_intent_data(self, domain: str):
        await asyncio.sleep(random.uniform(1.0, 2.0)) # Intent data is notoriously slow
        
        seed = int(hashlib.md5(domain.encode()).hexdigest(), 16)
        local_random = random.Random(seed)

        score = local_random.randint(40, 95)
        topics = [
            "Virtual Office Software", 
            "Remote Collaboration", 
            "Employee Engagement", 
            "Hybrid Work Policy",
            "Distributed Team Management"
        ]
        
        return {
            "intent_score": score,
            "top_topic": local_random.choice(topics),
            "is_spiking": score >= 75,
            "source": "Bombora"
        }