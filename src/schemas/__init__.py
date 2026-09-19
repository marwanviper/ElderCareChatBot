from src.schemas.care_goal import (
    CareGoalBase,
    CareGoalCreate,
    CareGoalResponse,
    CareGoalUpdate,
)
from src.schemas.care_report import (
    CareReportBase,
    CareReportCreate,
    CareReportResponse,
    CareReportUpdate,
)
from src.schemas.incident import (
    IncidentBase,
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
from src.schemas.resident import (
    ResidentBase,
    ResidentCreate,
    ResidentResponse,
    ResidentUpdate,
)
from src.schemas.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from src.schemas.user_resident_permission import (
    UserResidentPermissionBase,
    UserResidentPermissionCreate,
    UserResidentPermissionResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Resident
    "ResidentBase",
    "ResidentCreate",
    "ResidentUpdate",
    "ResidentResponse",
    # CareReport
    "CareReportBase",
    "CareReportCreate",
    "CareReportUpdate",
    "CareReportResponse",
    # CareGoal
    "CareGoalBase",
    "CareGoalCreate",
    "CareGoalUpdate",
    "CareGoalResponse",
    # Incident
    "IncidentBase",
    "IncidentCreate",
    "IncidentUpdate",
    "IncidentResponse",
    # UserResidentPermission
    "UserResidentPermissionBase",
    "UserResidentPermissionCreate",
    "UserResidentPermissionResponse",
]
