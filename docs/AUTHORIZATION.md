# 🛡️ Authorization & RBAC Guide

This document describes the two-tiered authorization architecture in the ElderCare ChatBot backend: **Role-Based Access Control (RBAC)** and **Resource-Level Access Scoping**.

---

## 🏛️ Multi-Layer Authorization Model

ElderCare enforces security across three distinct authorization layers:

```text
Incoming Request
      │
      ▼
1. Authentication Layer (JWT Validation) ───▶ 401 Unauthorized if invalid/expired
      │
      ▼
2. Role-Based Access Control (RBAC) ────────▶ 403 Forbidden if role insufficient
      │
      ▼
3. Resource-Level Scoping ─────────────────▶ 403 Forbidden if not assigned to resident
      │
      ▼
4. Record Ownership Verification ──────────▶ 403 Forbidden if not author/admin
      │
      ▼
Authorized Handler Execution
```

---

## 👥 1. Role-Based Access Control (RBAC)

The system defines two primary operational roles:

* **`admin`**: Facility administrators and medical directors. Unrestricted management of users, residents, system permissions, and clinical audits.
* **`caregiver`**: Nurses, aides, and physical therapists. Operational access restricted to assigned residents and authored notes.

### Role Permission Matrix

| Operation / Endpoint | Admin | Caregiver |
| :--- | :---: | :---: |
| **List all system users** (`GET /api/v1/users`) | ✅ | ❌ (403) |
| **Create new user** (`POST /api/v1/users`) | ✅ | ❌ (403) |
| **Update any user profile** (`PATCH /api/v1/users/{id}`) | ✅ | ❌ (403)* |
| **Delete user** (`DELETE /api/v1/users/{id}`) | ✅ | ❌ (403) |
| **Admit/Create Resident** (`POST /api/v1/residents`) | ✅ | ❌ (403) |
| **Delete Resident** (`DELETE /api/v1/residents/{id}`) | ✅ | ❌ (403) |
| **Assign/Revoke Permissions** (`/api/v1/permissions/*`) | ✅ | ❌ (403) |
| **Delete Care Goals / Incidents** | ✅ | ❌ (403) |
| **List assigned residents** (`GET /api/v1/residents`) | ✅ (All) | ✅ (Assigned only) |
| **View/Edit assigned resident** (`GET/PATCH /residents/{id}`) | ✅ | ✅ (Assigned only) |
| **Create Care Reports & Goals** (`/care-reports`, `/care-goals`) | ✅ | ✅ (Assigned only) |
| **Log Incidents** (`POST /api/v1/incidents`) | ✅ | ✅ (Assigned only) |

*\*Note: Caregivers may view and update their own profile (`/api/v1/users/me` or `/api/v1/users/{id}` where `id == current_user.id`), but are prevented from altering their role.*

### Implementation: `require_role`
Implemented as a reusable FastAPI dependency factory in [`src/api/deps.py`](file:///d:/ElderCareChatBot/src/api/deps.py#L59):
```python
def require_role(*allowed_roles: str) -> Callable[[User], User]:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role",
            )
        return current_user
    return role_checker
```

---

## 🏥 2. Resource-Level Access Scoping

Caregivers must not be able to view, edit, or report on residents who are not under their direct clinical care.

### Permission Mapping Table: `user_resident_permissions`
Resource authorization relies on the junction table [`user_resident_permissions`](file:///d:/ElderCareChatBot/src/models/user_resident_permission.py):
* Primary Key: Composite `(user_id, resident_id)`
* Foreign Keys: Cascading references to `users(id)` and `residents(id)`.

### Implementation: `verify_resident_access`
Enforced at the route dependency level in [`src/api/deps.py`](file:///d:/ElderCareChatBot/src/api/deps.py#L79):
```python
def verify_resident_access(
    resident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resident:
    resident = get_resident_by_id(db, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    # Admins have global visibility
    if current_user.role == "admin":
        return resident

    # Caregivers require explicit mapping
    perm = get_user_resident_permission(db, current_user.id, resident_id)
    if not perm:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this resident's data",
        )
    return resident
```

---

## ✍️ 3. Ownership & Clinical Accountability

For medical and legal integrity, care report editing and deletion enforce author accountability:
* When a report is filed (`POST /api/v1/care-reports`), the system records `created_by = current_user.id`.
* Modifying (`PATCH /api/v1/care-reports/{id}`) or deleting (`DELETE /api/v1/care-reports/{id}`) verifies that:
  ```python
  if current_user.role != "admin" and report.created_by != current_user.id:
      raise HTTPException(
          status_code=403,
          detail="You are not authorized to edit reports authored by someone else",
      )
  ```
* This guarantees that caregivers cannot alter or delete clinical observations entered by their colleagues, preserving the clinical audit trail.
