# backend/api/upload.py
import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
import asyncpg
import os

router = APIRouter()

async def get_db_connection():
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host="127.0.0.1",
        port=5432
    )

@router.post("/upload-csv/{tenant_id}")
async def upload_churn_data(tenant_id: int, file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # --- 1. CHURN FILTER ---
        # We only want inactive members. If 'Aktivan' exists, filter by it.
        if 'Aktivan' in df.columns:
            df = df[df['Aktivan'] == False].copy()
            
        # --- 2. DATA TRANSFORMATION ---
        
        # Handle the combined name column
        if 'Ime i prezime' in df.columns:
            df['first_name'] = df['Ime i prezime'].fillna('').str.strip()
        # Fallback just in case you upload the older format again
        elif 'Ime' in df.columns and 'Prezime' in df.columns:
            df['first_name'] = df['Ime'].fillna('') + ' ' + df['Prezime'].fillna('')
            df['first_name'] = df['first_name'].str.strip()
        
        # Parse the datetime string from the new column name
        if 'Zadnji dolazak' in df.columns:
            df['churn_date'] = pd.to_datetime(df['Zadnji dolazak'], errors='coerce').dt.date
        elif 'Datum I vreme isteka' in df.columns:
            df['churn_date'] = pd.to_datetime(df['Datum I vreme isteka'], errors='coerce').dt.date

        # Rename the remaining columns to our DB schema
        column_mapping = {
            'Telefon': 'phone_number',
            'Paket': 'preferred_zone'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # --- 3. VALIDATION LAYER ---
        required_columns = ['first_name', 'churn_date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing transformed columns: {missing_columns}."
            )
            
        # Drop rows with empty essential data (no name or no churn date)
        df.dropna(subset=['first_name', 'churn_date'], inplace=True)
        
        # --- 4. RECORD COMPILATION ---
        records = []
        for _, row in df.iterrows():
            # Calculate a basic data completeness score
            completeness = 0.5
            if pd.notna(row.get('phone_number')): completeness += 0.25
            if pd.notna(row.get('preferred_zone')): completeness += 0.25
            
            records.append((
                tenant_id,
                row['first_name'],
                str(row.get('phone_number')) if pd.notna(row.get('phone_number')) else None,
                row['churn_date'],
                None, # lifetime_value_eur
                None, # peak_attendance_time
                str(row.get('preferred_zone')) if pd.notna(row.get('preferred_zone')) else None,
                completeness
            ))
            
        # --- 5. DATABASE INSERTION ---
        conn = await get_db_connection()
        try:
            await conn.executemany("""
                INSERT INTO churned_members (
                    tenant_id, first_name, phone_number, churn_date, 
                    lifetime_value_eur, peak_attendance_time, preferred_zone, data_completeness
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, records)
        finally:
            await conn.close()
            
        return {
            "status": "success", 
            "message": f"Successfully processed and inserted {len(records)} churned members."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")