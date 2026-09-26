# 🔌 API Documentation

This document describes the REST API endpoints, schemas, headers, status codes, and error formatting for the ElderCare ChatBot backend.

---

## 🌐 Overview & Protocols

* **Base URL**: `http://localhost:8000`
* **API Prefix**: `/api/v1`
* **Interactive Documentation (Swagger UI)**: `http://localhost:8000/docs`
* **Alternative Documentation (ReDoc)**: `http://localhost:8000/redoc`
* **OpenAPI Schema (JSON)**: `http://localhost:8000/openapi.json`
* **Content-Type**: `application/json` (except OAuth2 login form: `application/x-www-form-urlencoded`)

---

## 🔒 Authentication Header

Protected endpoints require the standard HTTP `Authorization` header containing a valid Bearer token:
```http
Authorization: Bearer <your_jwt_access_token>
```

---

## 📊 Standard Status Codes & Error Format

| Status Code | Meaning | Typical Trigger |
| :--- | :--- | :--- |
| **`200 OK`** | Success | Successful retrieval (`GET`) or update (`PATCH`). |
| **`201 Created`** | Created | Successful entity creation (`POST`). |
| **`204 No Content`** | Deleted | Successful deletion (`DELETE`). |
| **`400 Bad Request`** | Client Error | Malformed request or illegal query parameters. |
| **`401 Unauthorized`** | Auth Failed | Missing, malformed, expired, or rejected JWT token. |
| **`403 Forbidden`** | Access Denied | Insufficient role or caregiver lacking permission to resident. |
| **`404 Not Found`** | Missing Entity | Specified record ID does not exist. |
| **`409 Conflict`** | Conflict | Duplicate unique constraint (e.g. duplicate email, duplicate assignment). |
| **`422 Unprocessable Content`** | Validation Error | Pydantic schema validation failure (e.g., short password, invalid date). |
| **`500 Internal Server Error`** | Server Error | Uncaught server failure (logged; stack trace hidden from client). |

### Error Response Schema
```json
{
  "detail": "Descriptive message or list of validation errors"
}
```

---

## 📑 Endpoints Catalog

### 1. Authentication (`/api/v1/auth`)

| Method | Endpoint | Access | Summary | Request Body | Response Model |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public | Register a new user | `UserCreate` | `UserResponse` (201) |
| `POST` | `/api/v1/auth/login` | Public | OAuth2 Form login (Swagger) | Form (`username`, `password`) | `Token` (200) |
| `POST` | `/api/v1/auth/login/json` | Public | JSON REST client login | `LoginRequest` | `Token` (200) |
| `GET` | `/api/v1/auth/me` | Authenticated | Current user profile | None | `UserResponse` (200) |

#### Example: Login JSON Request
```http
POST /api/v1/auth/login/json
Content-Type: application/json

{
  "email": "sarah.nurse@eldercare.test",
  "password": "SecurePassword123!"
}
```
#### Example: Login Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer"
}
```

---

### 2. Users Management (`/api/v1/users`)

| Method | Endpoint | Access | Summary |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users` | **Admin only** | Paginated list of users (`skip`, `limit`, `include_deleted`). |
| `GET` | `/api/v1/users/{user_id}` | Admin or Self | Details of a user. Caregivers cannot view other users. |
| `POST` | `/api/v1/users` | **Admin only** | Create user with assigned role (`UserCreate`). |
| `PATCH` | `/api/v1/users/{user_id}` | Admin or Self | Update user (`UserUpdate`). Non-admins cannot edit `role`. |
| `DELETE` | `/api/v1/users/{user_id}` | **Admin only** | Soft delete (default) or hard delete (`?hard=true`). |

---

### 3. Residents Management (`/api/v1/residents`)

| Method | Endpoint | Access | Summary |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/residents` | Authenticated | List residents. Admin sees all; Caregiver sees assigned only. |
| `GET` | `/api/v1/residents/{resident_id}` | Admin / Assigned CG | View resident profile. Verified via permissions. |
| `POST` | `/api/v1/residents` | **Admin only** | Admit / create new resident (`ResidentCreate`). |
| `PATCH` | `/api/v1/residents/{resident_id}` | Admin / Assigned CG | Update resident details (`ResidentUpdate`). |
| `DELETE` | `/api/v1/residents/{resident_id}` | **Admin only** | Delete resident record. |

---

### 4. Clinical Care Reports (`/api/v1/care-reports`)

| Method | Endpoint | Access | Summary |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/care-reports` | Admin / Assigned CG | File observation report. Stamped with `created_by`. |
| `GET` | `/api/v1/care-reports` | Authenticated | List accessible reports (scoped to assigned residents). |
| `GET` | `/api/v1/care-reports/resident/{resident_id}` | Admin / Assigned CG | Chronological list of reports for a resident. |
| `GET` | `/api/v1/care-reports/{report_id}` | Admin / Assigned CG | View specific report details. |
| `PATCH` | `/api/v1/care-reports/{report_id}` | Author or Admin | Edit report content. Non-authors receive HTTP 403. |
| `DELETE` | `/api/v1/care-reports/{report_id}` | Author or Admin | Delete report. Non-authors receive HTTP 403. |

---

### 5. Rehabilitation & Care Goals (`/api/v1/care-goals`)

| Method | Endpoint | Access | Summary |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/care-goals` | Admin / Assigned CG | Create care goal for resident (`CareGoalCreate`). |
| `GET` | `/api/v1/care-goals/resident/{resident_id}` | Admin / Assigned CG | List goals for resident (`?status=active`). |
| `GET` | `/api/v1/care-goals/{goal_id}` | Admin / Assigned CG | View single goal details. |
| `PATCH` | `/api/v1/care-goals/{goal_id}` | Admin / Assigned CG | Update description or status (`CareGoalUpdate`). |
| `DELETE` | `/api/v1/care-goals/{goal_id}` | **Admin only** | Delete care goal. |

---

### 6. Adverse Incident Tracking (`/api/v1/incidents`)

| Method | Endpoint | Access | Summary |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/incidents` | Admin / Assigned CG | Report incident (`IncidentCreate`). |
| `GET` | `/api/v1/incidents/resident/{resident_id}` | Admin / Assigned CG | List incidents for resident in reverse chronological order. |
| `GET` | `/api/v1/incidents/{incident_id}` | Admin / Assigned CG | View incident record details. |
| `PATCH` | `/api/v1/incidents/{incident_id}` | Admin / Assigned CG | Add follow-up observations or notes. |
| `DELETE` | `/api/v1/incidents/{incident_id}` | **Admin only** | Remove incident record. |

---

### 7. User-Resident Access Permissions (`/api/v1/permissions`)

| Method | Endpoint | Access | Summary |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/permissions` | **Admin only** | Grant caregiver access to a resident. |
| `GET` | `/api/v1/permissions` | **Admin only** | List all assignment records. |
| `GET` | `/api/v1/permissions/user/{user_id}` | Admin or Self | List residents assigned to a given caregiver. |
| `GET` | `/api/v1/permissions/resident/{resident_id}` | **Admin only** | List all caregivers assigned to a given resident. |
| `DELETE` | `/api/v1/permissions/{user_id}/{resident_id}` | **Admin only** | Revoke caregiver permission to a resident. |

---

### 8. System Health (`/`)

* **Endpoint**: `GET /`
* **Access**: Public
* **Response**:
```json
{
  "status": "healthy",
  "app": "ElderCare Chatbot API",
  "version": "1.0.0",
  "docs": "/docs"
}
```
