"""Care domain service wrapper (Residents, Care Reports, Care Goals, Incidents, Permissions)."""

from datetime import date, datetime
from typing import Any

from frontend.services.api_client import APIClient


class CareService:
    """Service methods for `/residents`, `/care-reports`, `/care-goals`, `/incidents`, and `/permissions`."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    # =========================================================================
    # Residents
    # =========================================================================

    def list_residents(
        self,
        token: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List all residents accessible to the authenticated user."""
        return self.client.get(
            "/residents",
            token=token,
            params={"skip": skip, "limit": limit},
        )

    def get_resident(self, token: str, resident_id: int) -> dict[str, Any]:
        """Get a specific resident by ID."""
        return self.client.get(f"/residents/{resident_id}", token=token)

    def create_resident(
        self,
        token: str,
        name: str,
        date_of_birth: date | str | None = None,
        room_number: str | None = None,
    ) -> dict[str, Any]:
        """Admit/create a new resident (Admin only)."""
        payload: dict[str, Any] = {"name": name.strip()}
        if date_of_birth is not None:
            payload["date_of_birth"] = (
                date_of_birth.isoformat()
                if isinstance(date_of_birth, date)
                else str(date_of_birth)
            )
        if room_number:
            payload["room_number"] = room_number.strip()
        return self.client.post("/residents", token=token, json=payload)

    def update_resident(
        self,
        token: str,
        resident_id: int,
        name: str | None = None,
        date_of_birth: date | str | None = None,
        room_number: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing resident's profile."""
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name.strip()
        if date_of_birth is not None:
            payload["date_of_birth"] = (
                date_of_birth.isoformat()
                if isinstance(date_of_birth, date)
                else str(date_of_birth)
            )
        if room_number is not None:
            payload["room_number"] = room_number.strip()
        return self.client.patch(
            f"/residents/{resident_id}",
            token=token,
            json=payload,
        )

    def delete_resident(self, token: str, resident_id: int) -> None:
        """Delete a resident record (Admin only)."""
        self.client.delete(f"/residents/{resident_id}", token=token)

    # =========================================================================
    # Care Reports
    # =========================================================================

    def list_care_reports(
        self,
        token: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List all accessible care reports across residents."""
        return self.client.get(
            "/care-reports",
            token=token,
            params={"skip": skip, "limit": limit},
        )

    def list_resident_care_reports(
        self,
        token: str,
        resident_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List care reports for a specific resident."""
        return self.client.get(
            f"/care-reports/resident/{resident_id}",
            token=token,
            params={"skip": skip, "limit": limit},
        )

    def create_care_report(
        self,
        token: str,
        resident_id: int,
        content: str,
        report_date: datetime | str | None = None,
    ) -> dict[str, Any]:
        """Create a new clinical/daily care report."""
        payload: dict[str, Any] = {
            "resident_id": resident_id,
            "content": content.strip(),
        }
        if report_date is not None:
            payload["report_date"] = (
                report_date.isoformat()
                if isinstance(report_date, datetime)
                else str(report_date)
            )
        return self.client.post("/care-reports", token=token, json=payload)

    def update_care_report(
        self,
        token: str,
        report_id: int,
        content: str,
    ) -> dict[str, Any]:
        """Update an existing care report's content."""
        return self.client.patch(
            f"/care-reports/{report_id}",
            token=token,
            json={"content": content.strip()},
        )

    def delete_care_report(self, token: str, report_id: int) -> None:
        """Delete a care report."""
        self.client.delete(f"/care-reports/{report_id}", token=token)

    # =========================================================================
    # Care Goals
    # =========================================================================

    def list_resident_care_goals(
        self,
        token: str,
        resident_id: int,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List care goals for a specific resident."""
        return self.client.get(
            f"/care-goals/resident/{resident_id}",
            token=token,
            params={"status": status_filter, "skip": skip, "limit": limit},
        )

    def create_care_goal(
        self,
        token: str,
        resident_id: int,
        goal: str,
        status: str = "active",
    ) -> dict[str, Any]:
        """Create a new care goal for a resident."""
        return self.client.post(
            "/care-goals",
            token=token,
            json={
                "resident_id": resident_id,
                "goal": goal.strip(),
                "status": status,
            },
        )

    def update_care_goal(
        self,
        token: str,
        goal_id: int,
        goal: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Update a care goal's text or status."""
        payload: dict[str, Any] = {}
        if goal is not None:
            payload["goal"] = goal.strip()
        if status is not None:
            payload["status"] = status
        return self.client.patch(
            f"/care-goals/{goal_id}",
            token=token,
            json=payload,
        )

    def delete_care_goal(self, token: str, goal_id: int) -> None:
        """Delete a care goal (Admin only)."""
        self.client.delete(f"/care-goals/{goal_id}", token=token)

    # =========================================================================
    # Adverse Incidents
    # =========================================================================

    def list_resident_incidents(
        self,
        token: str,
        resident_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List adverse incidents for a specific resident."""
        return self.client.get(
            f"/incidents/resident/{resident_id}",
            token=token,
            params={"skip": skip, "limit": limit},
        )

    def create_incident(
        self,
        token: str,
        resident_id: int,
        incident_type: str,
        description: str,
        incident_date: datetime | str | None = None,
    ) -> dict[str, Any]:
        """Log a new adverse incident for a resident."""
        payload: dict[str, Any] = {
            "resident_id": resident_id,
            "type": incident_type.strip(),
            "description": description.strip(),
        }
        if incident_date is not None:
            payload["incident_date"] = (
                incident_date.isoformat()
                if isinstance(incident_date, datetime)
                else str(incident_date)
            )
        return self.client.post("/incidents", token=token, json=payload)

    def update_incident(
        self,
        token: str,
        incident_id: int,
        incident_type: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing incident record."""
        payload: dict[str, Any] = {}
        if incident_type is not None:
            payload["type"] = incident_type.strip()
        if description is not None:
            payload["description"] = description.strip()
        return self.client.patch(
            f"/incidents/{incident_id}",
            token=token,
            json=payload,
        )

    def delete_incident(self, token: str, incident_id: int) -> None:
        """Delete an incident record (Admin only)."""
        self.client.delete(f"/incidents/{incident_id}", token=token)

    # =========================================================================
    # Caregiver-Resident Permissions (Admin)
    # =========================================================================

    def list_resident_permissions(
        self,
        token: str,
        resident_id: int,
    ) -> list[dict[str, Any]]:
        """List caregiver permission links for a resident (Admin only)."""
        return self.client.get(
            f"/permissions/resident/{resident_id}",
            token=token,
        )

    def assign_permission(
        self,
        token: str,
        user_id: int,
        resident_id: int,
    ) -> dict[str, Any]:
        """Grant a user access permission to a resident (Admin only)."""
        return self.client.post(
            "/permissions",
            token=token,
            json={"user_id": user_id, "resident_id": resident_id},
        )

    def revoke_permission(
        self,
        token: str,
        user_id: int,
        resident_id: int,
    ) -> None:
        """Revoke a user's access permission for a resident (Admin only)."""
        self.client.delete(
            f"/permissions/{user_id}/{resident_id}",
            token=token,
        )

