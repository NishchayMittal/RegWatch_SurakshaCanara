-- 1. DEPARTMENTS
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    contact_email VARCHAR(255),
    slack_webhook VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. CIRCULARS
CREATE TABLE circulars (
    id SERIAL PRIMARY KEY,
    source VARCHAR(20) NOT NULL CHECK (source IN ('RBI', 'SEBI', 'MCA', 'IRDAI')),
    title TEXT NOT NULL,
    url VARCHAR(1000),
    raw_text TEXT,
    published_at TIMESTAMP,
    ingested_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(30) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'processed', 'duplicate', 'failed')),
    dedup_hash VARCHAR(64) UNIQUE  -- Person A owns this
);

-- 3. MAPs (Mandatory Action Points)
CREATE TABLE maps (
    id SERIAL PRIMARY KEY,
    circular_id INT REFERENCES circulars(id) ON DELETE CASCADE,
    map_text TEXT NOT NULL,
    source_paragraph TEXT,        -- exact paragraph cited from circular
    confidence_score FLOAT,       -- 0.0 to 1.0, from MAP Extractor
    status VARCHAR(30) DEFAULT 'pending_review'
        CHECK (status IN (
            'pending_review', 'approved', 'assigned', 
            'in_progress', 'completed', 'disputed', 'escalated'
        )),
    extracted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(100)
);

-- 4. SLAs (rules per department per regulator)
CREATE TABLE slas (
    id SERIAL PRIMARY KEY,
    department_id INT REFERENCES departments(id),
    circular_source VARCHAR(20) CHECK (circular_source IN ('RBI', 'SEBI', 'MCA', 'IRDAI')),
    days_to_complete INT NOT NULL,
    UNIQUE(department_id, circular_source)
);

-- 5. TASKS (one MAP → many department tasks)
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    map_id INT REFERENCES maps(id) ON DELETE CASCADE,
    department_id INT REFERENCES departments(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    due_at TIMESTAMP,             -- assigned_at + SLA days
    completed_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'assigned'
        CHECK (status IN (
            'assigned', 'in_progress', 'completed', 
            'disputed', 'escalated', 'reassigned'
        )),
    evidence_url VARCHAR(1000),
    notes TEXT
);

-- 6. SUB-TASKS (task → many sub-tasks, partial re-escalation)
CREATE TABLE sub_tasks (
    id SERIAL PRIMARY KEY,
    task_id INT REFERENCES tasks(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed', 'disputed', 'escalated')),
    completed_at TIMESTAMP,
    evidence_url VARCHAR(1000)
);

-- 7. HUMAN REVIEW QUEUE
CREATE TABLE human_review_queue (
    id SERIAL PRIMARY KEY,
    map_id INT REFERENCES maps(id),
    reason TEXT,                  -- why it was flagged (low confidence, ambiguous dept)
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolution VARCHAR(30) CHECK (resolution IN ('approved', 'rejected', 'modified')),
    resolved_by VARCHAR(100)
);

-- 8. AUDIT LOG
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,   -- 'circular', 'map', 'task', 'sub_task'
    entity_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,       -- 'status_changed', 'assigned', 'escalated'
    actor VARCHAR(100),                 -- agent name or human user
    timestamp TIMESTAMP DEFAULT NOW(),
    payload JSONB                       -- full before/after diff
);

-- 9. NOTIFICATIONS LOG
CREATE TABLE notifications_log (
    id SERIAL PRIMARY KEY,
    task_id INT REFERENCES tasks(id),
    department_id INT REFERENCES departments(id),
    channel VARCHAR(20) CHECK (channel IN ('email', 'slack')),
    notification_type VARCHAR(30) 
        CHECK (notification_type IN ('assignment', 'reminder', 'escalation', 'breach')),
    sent_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) CHECK (status IN ('sent', 'failed', 'pending'))
);