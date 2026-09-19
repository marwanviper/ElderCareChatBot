from src.crud.care_goal import (
    create_care_goal,
    delete_care_goal,
    get_all_care_goals,
    get_care_goal_by_id,
    get_care_goals_by_resident,
    update_care_goal,
)
from src.crud.care_report import (
    create_care_report,
    delete_care_report,
    get_all_care_reports,
    get_care_report_by_id,
    get_care_reports_by_resident,
    update_care_report,
)
from src.crud.incident import (
    create_incident,
    delete_incident,
    get_all_incidents,
    get_incident_by_id,
    get_incidents_by_resident,
    update_incident,
)
from src.crud.resident import (
    create_resident,
    delete_resident,
    get_all_residents,
    get_resident_by_id,
    update_resident,
)
from src.crud.user import (
    create_user,
    delete_user_hard,
    delete_user_soft,
    get_user_by_email,
    get_user_by_id,
    get_users,
    update_user,
)
from src.crud.user_resident_permission import (
    create_user_resident_permission,
    delete_user_resident_permission,
    get_all_user_resident_permissions,
    get_permissions_by_resident,
    get_permissions_by_user,
    get_user_resident_permission,
)

__all__ = [
    # User
    "create_user",
    "get_user_by_id",
    "get_user_by_email",
    "get_users",
    "update_user",
    "delete_user_soft",
    "delete_user_hard",
    # Resident
    "create_resident",
    "get_resident_by_id",
    "get_all_residents",
    "update_resident",
    "delete_resident",
    # CareReport
    "create_care_report",
    "get_care_report_by_id",
    "get_care_reports_by_resident",
    "get_all_care_reports",
    "update_care_report",
    "delete_care_report",
    # CareGoal
    "create_care_goal",
    "get_care_goal_by_id",
    "get_care_goals_by_resident",
    "get_all_care_goals",
    "update_care_goal",
    "delete_care_goal",
    # Incident
    "create_incident",
    "get_incident_by_id",
    "get_incidents_by_resident",
    "get_all_incidents",
    "update_incident",
    "delete_incident",
    # UserResidentPermission
    "create_user_resident_permission",
    "get_user_resident_permission",
    "get_permissions_by_user",
    "get_permissions_by_resident",
    "get_all_user_resident_permissions",
    "delete_user_resident_permission",
]
