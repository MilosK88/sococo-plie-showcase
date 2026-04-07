-- backend/core/schema.sql

CREATE TABLE IF NOT EXISTS gym_tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    language_locale VARCHAR(10) DEFAULT 'sr_RS', -- sr_RS for Serbian Ekavica
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS churned_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER REFERENCES gym_tenants(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(50),
    churn_date DATE NOT NULL,
    lifetime_value_eur NUMERIC(10, 2),
    peak_attendance_time VARCHAR(50), -- e.g., '19:00' or 'Morning'
    preferred_zone VARCHAR(100),      -- e.g., 'Free Weights', 'Yoga'
    data_completeness NUMERIC(3, 2),  -- 0.00 to 1.00
    cre_score INTEGER,                -- 0 to 100
    score_explanation TEXT,
    message_draft_a TEXT,
    message_draft_b TEXT,
    message_draft_c TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast querying by tenant and score
CREATE INDEX IF NOT EXISTS idx_members_tenant_score ON churned_members(tenant_id, cre_score DESC);