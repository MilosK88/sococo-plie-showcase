import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from database import get_db

router = APIRouter()

@router.post("/upload-csv/{tenant_id}")
async def upload_b2b_leads(tenant_id: int, file: UploadFile = File(...), conn = Depends(get_db)):
    """Ingests a CSV of B2B SaaS leads, standardizes domains, and queues them for enrichment."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # --- 1. DATA TRANSFORMATION & MAPPING ---
        # Standardize column headers to lowercase to survive messy sales exports
        df.columns = df.columns.str.lower().str.strip()
        
        # Map expected B2B CSV columns to our database schema
        column_mapping = {}
        
        # Map Company
        if 'company name' in df.columns:
            column_mapping['company name'] = 'company_name'
        elif 'company' in df.columns:
            column_mapping['company'] = 'company_name'
            
        # Map Contact Name
        if 'contact name' in df.columns:
            column_mapping['contact name'] = 'contact_name'
        elif 'name' in df.columns:
            column_mapping['name'] = 'contact_name'
        elif 'contact' in df.columns:
            column_mapping['contact'] = 'contact_name'
            
        # Map Domain
        if 'website' in df.columns:
            column_mapping['website'] = 'domain'
        elif 'url' in df.columns:
            column_mapping['url'] = 'domain'
            
        df.rename(columns=column_mapping, inplace=True)
        
        # --- 2. VALIDATION LAYER ---
        required_columns = ['company_name', 'contact_name', 'domain']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"CSV missing required columns. Expected equivalent of: {required_columns}. Missing: {missing_columns}"
            )
            
        # Drop rows missing essential B2B identity data
        df.dropna(subset=['company_name', 'domain'], inplace=True)
        
        # --- 3. RECORD COMPILATION ---
        records = []
        for _, row in df.iterrows():
            # Clean up domains (e.g., convert 'https://www.sococo.com/pricing' to 'sococo.com')
            raw_domain = str(row['domain']).strip().lower()
            clean_domain = raw_domain.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            
            records.append((
                tenant_id,
                str(row['company_name']).strip(),
                str(row['contact_name']).strip(),
                clean_domain
            ))
            
        # --- 4. DATABASE INSERTION ---
        if records:
            # ON CONFLICT DO NOTHING: Prevents duplicate domain ingestion per tenant.
            # Safely ignores duplicates without throwing an error.
            await conn.executemany("""
                INSERT INTO b2b_leads (tenant_id, company_name, contact_name, domain)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (tenant_id, domain) DO NOTHING
            """, records)
            
        return {
            "status": "success", 
            "message": f"Successfully processed {len(records)} B2B leads. Duplicates were ignored."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")