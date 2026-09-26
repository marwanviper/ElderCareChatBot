# 📜 Logging & Diagnostics

This document outlines the logging framework, HTTP request profiling middleware, exception handlers, and security/privacy rules implemented in the ElderCare ChatBot backend.

---

## 🏗️ Logging Architecture

Centralized logging is configured in [`src/core/logging.py`](file:///d:/ElderCareChatBot/src/core/logging.py) and initialized on application startup via the lifespan handler in [`src/main.py`](file:///d:/ElderCareChatBot/src/main.py#L16).

### Log Message Format
All logs adhere to a consistent standard with timestamps, log levels, logger name, line number, and messages:
```text
[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s
```
*Example Output:*
```text
[2026-09-26 22:51:09] [INFO] [eldercare:40] - User registered successfully with ID 1
[2026-09-26 22:51:09] [INFO] [eldercare:62] - POST /api/v1/auth/register - 201 (203.60ms)
[2026-09-26 22:52:04] [WARNING] [eldercare:64] - Access denied for user 2 with role 'caregiver'. Required one of: ('admin',)
```

### Log Level Configuration
The minimum threshold for logging is dynamically controlled via the `LOG_LEVEL` environment variable in `.env`:
* `DEBUG`: Detailed diagnostic output (SQL statements, internal state).
* `INFO`: Standard operational messages (logins, admissions, request durations).
* `WARNING`: Non-fatal issues (failed logins, 403 access rejections, 409 conflicts).
* `ERROR`: Operational failures (database connection drop, unhandled exception).
* `CRITICAL`: System unavailability.

---

## ⏱️ Request Profiling Middleware

FastAPI includes an asynchronous HTTP middleware (`log_requests_middleware` in [`src/main.py`](file:///d:/ElderCareChatBot/src/main.py#L52)) that automatically monitors all incoming network calls:

1. **High-Resolution Clock**: Measures exact round-trip latency using `time.perf_counter()`.
2. **Access Log**: Emits an `INFO` entry recording:
   * HTTP Method (`GET`, `POST`, `PATCH`, `DELETE`)
   * Request Path (e.g. `/api/v1/residents/10`)
   * HTTP Response Status Code (`200`, `201`, `403`, etc.)
   * Execution Duration in milliseconds (`12.35ms`)
3. **Failure Logging**: If an unhandled exception occurs inside a handler, the middleware captures the exception, logs full trace diagnostics with `logger.exception()`, and re-raises for the global error handler.

---

## 🔒 Security & Privacy (PII) Redaction Rules

Because ElderCare processes medical and elderly care data, strict rules apply to all logging calls:

1. **Never Log Passwords**: Neither plaintext passwords nor bcrypt hashes may appear in logs or error messages.
2. **Never Log Bearer Tokens**: JWT strings must never be printed to stdout, files, or log collectors.
3. **Redact Sensitive Resident PII**: While resident IDs and care report IDs are permissible in operational logs, full patient names, dates of birth, medical diagnoses, and notes must remain strictly in the database layer.
4. **No Token Echoing in Headers**: Authentication failure warnings only state the reason (e.g. `Token decoding failed or token expired`), never echoing token contents.

---

## 🛡️ Exception Handlers & Information Leakage Prevention

To ensure that internal system architecture, stack traces, and database schemas are never exposed to attackers or clients, [`src/main.py`](file:///d:/ElderCareChatBot/src/main.py#L82) defines custom exception handlers:

* **`HTTPException` Handler**: Returns clean, normalized JSON responses `{"detail": exc.detail}`.
* **`RequestValidationError` Handler**: Catches Pydantic schema validation failures, returning HTTP `422 Unprocessable Content` with specific field issues.
* **`Global Exception Handler` (`Exception`)**: Catches all unhandled exceptions:
  * Logs the full internal stack trace safely to the server logs.
  * Emits an opaque response to the client:
    ```json
    {
      "detail": "An internal server error occurred"
    }
    ```
  * Returns HTTP `500 Internal Server Error`, completely shielding internal implementation details from external inspection.
