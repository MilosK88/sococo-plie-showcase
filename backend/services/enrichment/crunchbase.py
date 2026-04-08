import asyncio
import random
import hashlib
from datetime import datetime, timedelta

class CrunchbaseMockClient:
    """Simulates Crunchbase API: funding rounds and total raised."""
    async def get_funding_data(self, domain: str):
        await asyncio.sleep(random.uniform(0.3, 0.9)) # Fast API response
        
        seed = int(hashlib.md5(domain.encode()).hexdigest(), 16)
        local_random = random.Random(seed)

        # 15% chance they are bootstrapped (no funding data found)
        if local_random.random() < 0.15:
            return None

        # Correlate stage with realistic funding amounts (in Millions)
        stages_logic = {
            "Seed": (1, 4),
            "Series A": (5, 18),
            "Series B": (19, 45),
            "Series C": (46, 120),
            "IPO": (150, 500)
        }
        
        stage = local_random.choice(list(stages_logic.keys()))
        raised = local_random.randint(stages_logic[stage][0], stages_logic[stage][1])
        
        # Generate a realistic date from the past 24 months
        days_ago = local_random.randint(30, 730)
        last_round = (datetime.utcnow() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        return {
            "funding_stage": stage,
            "total_raised_m": raised,
            "last_round_date": last_round,
            "source": "Crunchbase"
        }