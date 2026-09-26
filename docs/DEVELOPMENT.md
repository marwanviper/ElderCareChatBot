# 🛠️ Developer Guide

This guide describes standard conventions and step-by-step workflows for extending the ElderCare ChatBot backend with new models, schemas, CRUD operations, API routes, and automated tests.

---

## 🪜 10-Step Workflow for Adding a Feature

Whenever adding a new resource or database table (e.g. `MedicationSchedule`), follow this structured sequence to preserve architectural modularity:

```text
1. Model ──▶ 2. Model Export ──▶ 3. Pydantic Schemas ──▶ 4. Schema Export ──▶ 5. CRUD Operations
                                                                                   │
10. Test Run ◀── 9. Automated Tests ◀── 8. Router Mount ◀── 7. API Router ◀── 6. CRUD Export
```

### Step 1: Create SQLAlchemy Model
Create `src/models/<entity_name>.py`:
```python
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resident_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("residents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dosage: Mapped[str] = mapped_column(String(50), nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

### Step 2: Re-Export in `src/models/__init__.py`
Import the new model and add it to `__all__`.

### Step 3: Define Pydantic v2 Schemas
Create `src/schemas/<entity_name>.py` with `Base`, `Create`, `Update`, and `Response` models:
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class MedicationScheduleBase(BaseModel):
    resident_id: int = Field(..., description="Resident ID")
    medication_name: str = Field(..., min_length=1, max_length=100)
    dosage: str = Field(..., min_length=1, max_length=50)
    scheduled_time: datetime

class MedicationScheduleCreate(MedicationScheduleBase):
    pass

class MedicationScheduleUpdate(BaseModel):
    medication_name: str | None = None
    dosage: str | None = None
    scheduled_time: datetime | None = None

class MedicationScheduleResponse(MedicationScheduleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

### Step 4: Re-Export in `src/schemas/__init__.py`
Import the new schemas and add them to `__all__`.

### Step 5: Implement CRUD Operations
Create `src/crud/<entity_name>.py`:
```python
from sqlalchemy.orm import Session
from src.models.medication_schedule import MedicationSchedule
from src.schemas.medication_schedule import MedicationScheduleCreate, MedicationScheduleUpdate

def create_schedule(db: Session, schedule_data: MedicationScheduleCreate) -> MedicationSchedule:
    db_obj = MedicationSchedule(**schedule_data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_schedules_by_resident(db: Session, resident_id: int) -> list[MedicationSchedule]:
    return db.query(MedicationSchedule).filter(MedicationSchedule.resident_id == resident_id).all()
```

### Step 6: Re-Export in `src/crud/__init__.py`
Add CRUD functions to `src/crud/__init__.py` and include them in `__all__`.

### Step 7: Create FastAPI Router
Create `src/api/routes/<entity_name>.py`:
* Inject `db: Session = Depends(get_db)`
* Verify resident permissions using `_resident = Depends(verify_resident_access)`
* Enforce RBAC where required using `_admin = Depends(require_role("admin"))`

### Step 8: Mount Router in `src/api/routes/__init__.py`
Register router with `api_router.include_router(medication_router)`.

### Step 9: Write Unit & Integration Tests
* Unit tests in `tests/test_<entity_name>.py` extending `BaseTestCase` (`tests/test_base.py`).
* API integration tests in `tests/test_api_<entity_name>.py` extending `ApiTestCase` (`tests/test_api_base.py`).

### Step 10: Run the Full Test Suite
Ensure all existing and new tests pass cleanly:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📐 Coding Conventions

* **Typing**: Use standard Python 3.10+ union syntax (`str | None`, `list[int]`).
* **Pydantic**: Use `model_dump()` instead of deprecated `.dict()`.
* **SQLAlchemy**: Use `Mapped[T]` and `mapped_column()` annotations for model declarations.
* **Exceptions**: Raise `HTTPException` with explicit `status_code` and descriptive `detail`. Never leak internal traces in client responses.
* **Logging**: Use `%s` formatting with `src.core.logging.logger` instead of f-strings in logging calls to leverage lazy string interpolation.
