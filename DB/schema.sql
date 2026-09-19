
-- =========================================
-- ELDER CARE DATABASE
-- =========================================

-- 1. USERS
CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL,
	deleted_date TIMESTAMP,
);


-- 2. RESIDENTS
CREATE TABLE residents (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    room_number VARCHAR(20),
);


-- 3. CARE REPORTS
CREATE TABLE care_reports (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resident_id INTEGER NOT NULL,
    report_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    content TEXT NOT NULL,
    created_by INTEGER,

    CONSTRAINT fk_report_resident
        FOREIGN KEY (resident_id)
        REFERENCES residents(id),

    CONSTRAINT fk_report_user
        FOREIGN KEY (created_by)
        REFERENCES users(id)
);


-- 4. CARE GOALS
CREATE TABLE care_goals (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resident_id INTEGER NOT NULL,
    goal TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_goal_resident
        FOREIGN KEY (resident_id)
        REFERENCES residents(id)
);


-- 5. INCIDENTS
CREATE TABLE incidents (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resident_id INTEGER NOT NULL,
    incident_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    CONSTRAINT fk_incident_resident
        FOREIGN KEY (resident_id)
        REFERENCES residents(id)
);


-- 6. USER ↔ RESIDENT PERMISSIONS
CREATE TABLE user_resident_permissions (
    user_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,

    PRIMARY KEY (user_id, resident_id),

    CONSTRAINT fk_permission_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),

    CONSTRAINT fk_permission_resident
        FOREIGN KEY (resident_id)
        REFERENCES residents(id)
);
