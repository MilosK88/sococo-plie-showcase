import asyncio
import random
import hashlib

class ApolloMockClient:
    """
    Simulates the Apollo.io Enrichment API.
    Returns firmographic data (headcount, industry, growth).
    """
    async def get_company_data(self, domain: str):
        # Simulate network latency (0.5 to 1.5 seconds)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Seed randomness with the domain so data is deterministic per company
        seed = int(hashlib.md5(domain.encode()).hexdigest(), 16)
        local_random = random.Random(seed)

        # Simulate a 5% chance the company is too small/new to be in Apollo
        if local_random.random() < 0.05:
            return None
        
        # Simulate realistic B2B data payload
        return {
            "headcount_current": local_random.randint(50, 500),
            "headcount_growth_pct": round(local_random.uniform(-10.0, 45.0), 1),
            "industry": local_random.choice(["Software / SaaS", "Fintech", "Healthtech", "Enterprise IT", "E-Learning"]),
            "hq_location": local_random.choice(["San Francisco, CA", "New York, NY", "Austin, TX", "London, UK", "Remote-First"]),
            "source": "Apollo.io"
        }