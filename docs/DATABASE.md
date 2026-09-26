# 🗄️ Database Architecture

This document details the database schema, SQLAlchemy 2.0 models, table constraints, relationships, indexes, and connection management for the ElderCare system.

---

## 🏛️ Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    users ||--o{ user_resident_permissions : "granted"
    residents ||--o{ user_resident_permissions : "assigned"
    residents ||--o{ care_reports : "has"
    users ||--o{ care_reports : "authors"
    residents ||--o{ care_goals : "tracks"
    residents ||--o{ incidents : "records"

    users {
        int id PK
        string name
        string email UK
        string password_hash
        string role "admin | caregiver"
        datetime created_at
        datetime deleted_at "nullable (soft delete)"
    }

    residents {
        int id PK
        string name
        date date_of_birth
        string room_number
        datetime created_at
    }

    user_resident_permissions {
        int user_id PK, FK
        int resident_id PK, FK
        datetime granted_at
    }

    care_reports {
        int id PK
        int resident_id FK
        int created_by FK
        text content
        datetime report_date
    }

    care_goals {
        int id PK
        int resident_id FK
        string goal
        string status "active | achieved | cancelled"
        datetime created_at
    }

    incidents {
        int id PK
        int resident_id FK
        string type
        text description
        datetime timestamp
    }
```

---

## 📋 Tables Specification

### 1. `users` Table
Stores authenticated staff credentials, role tier, and status.
* Model: [`src.models.user.User`](file:///d:/ElderCareChatBot/src/models/user.py)
* **`id`**: `Integer`, Primary Key, autoincrement.
* **`name`**: `String(100)`, Not Null.
* **`email`**: `String(150)`, Unique, Indexed, Not Null.
* **`password_hash`**: `String(255)`, Bcrypt hash string, Not Null.
* **`role`**: `String(30)`, Defaults to `'caregiver'`. Valid options: `'admin'`, `'caregiver'`.
* **`created_at`**: `DateTime(timezone=True)`, Defaults to UTC now.
* **`deleted_at`**: `DateTime(timezone=True)`, Nullable. Used for soft deletion; non-null indicates inactive/archived account.

### 2. `residents` Table
Stores elderly resident demographic and room assignment data.
* Model: [`src.models.resident.Resident`](file:///d:/ElderCareChatBot/src/models/resident.py)
* **`id`**: `Integer`, Primary Key, autoincrement.
* **`name`**: `String(100)`, Not Null.
* **`date_of_birth`**: `Date`, Not Null.
* **`room_number`**: `String(20)`, Nullable.
* **`created_at`**: `DateTime(timezone=True)`, Defaults to UTC now.

### 3. `user_resident_permissions` Table
Junction table linking caregivers to residents they are authorized to manage.
* Model: [`src.models.user_resident_permission.UserResidentPermission`](file:///d:/ElderCareChatBot/src/models/user_resident_permission.py)
* **`user_id`**: `Integer`, Composite Primary Key, Foreign Key (`users.id`, ondelete `CASCADE`).
* **`resident_id`**: `Integer`, Composite Primary Key, Foreign Key (`residents.id`, ondelete `CASCADE`).
* **`granted_at`**: `DateTime(timezone=True)`, Defaults to UTC now.

### 4. `care_reports` Table
Stores clinical observations, routine checks, and caregiver notes.
* Model: [`src.models.care_report.CareReport`](file:///d:/ElderCareChatBot/src/models/care_report.py)
* **`id`**: `Integer`, Primary Key, autoincrement.
* **`resident_id`**: `Integer`, Foreign Key (`residents.id`, ondelete `CASCADE`), Indexed.
* **`created_by`**: `Integer`, Foreign Key (`users.id`, ondelete `SET NULL`), Nullable, Indexed.
* **`content`**: `Text`, Not Null.
* **`report_date`**: `DateTime(timezone=True)`, Defaults to UTC now.

### 5. `care_goals` Table
Tracks individualized rehabilitation, mobility, and behavioral goals.
* Model: [`src.models.care_goal.CareGoal`](file:///d:/ElderCareChatBot/src/models/care_goal.py)
* **`id`**: `Integer`, Primary Key, autoincrement.
* **`resident_id`**: `Integer`, Foreign Key (`residents.id`, ondelete `CASCADE`), Indexed.
* **`goal`**: `Text`, Not Null.
* **`status`**: `String(30)`, Defaults to `'active'`.
* **`created_at`**: `DateTime(timezone=True)`, Defaults to UTC now.

### 6. `incidents` Table
Logs safety events, medical emergencies, falls, or adverse resident occurrences.
* Model: [`src.models.incident.Incident`](file:///d:/ElderCareChatBot/src/models/incident.py)
* **`id`**: `Integer`, Primary Key, autoincrement.
* **`resident_id`**: `Integer`, Foreign Key (`residents.id`, ondelete `CASCADE`), Indexed.
* **`type`**: `String(50)`, Not Null (e.g., `'Fall'`, `'Medication Error'`, `'Behavioral'`).
* **`description`**: `Text`, Not Null.
* **`timestamp`**: `DateTime(timezone=True)`, Defaults to UTC now.

---

## 🔌 Connection Management & Pooling

Configured in [`src/database.py`](file:///d:/ElderCareChatBot/src/database.py):

* **Engine Configuration**:
  ```python
  engine = create_engine(
      settings.database_url,
      pool_pre_ping=True,  # Proactively verifies connection liveness
  )
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  ```
* **Supported Dialects**:
  * PostgreSQL: `postgresql+psycopg://user:password@host:5432/dbname`
  * SQLite (Test/Dev): `sqlite:///:memory:` or `sqlite:///./test.db`
* **Session Scope**: FastAPI requests utilize the `get_db` generator dependency yielding a session that automatically rolls back on error and closes on completion.
