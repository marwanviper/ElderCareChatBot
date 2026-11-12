"""Core HTTP client for communicating with the FastAPI backend."""

from typing import Any

import httpx

from frontend.config import frontend_config


class APIError(Exception):
    """Structured exception raised when the FastAPI backend returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def __str__(self) -> str:
        if self.status_code:
            return f"[HTTP {self.status_code}] {self.message}"
        return self.message


class APIClient:
    """Thin HTTP client wrapper around httpx with JWT Bearer injection and error parsing."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or frontend_config.api_v1_url).rstrip("/")
        self.root_url = (base_url or frontend_config.API_BASE_URL).rstrip("/")
        self.timeout = timeout or frontend_config.REQUEST_TIMEOUT_SECONDS
        self._transport = transport

    def _build_headers(self, token: str | None = None) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _extract_error_message(self, response: httpx.Response) -> str:
        """Extract human-readable error message from FastAPI JSON error responses."""
        try:
            data = response.json()
            if isinstance(data, dict):
                detail = data.get("detail")
                if isinstance(detail, str):
                    return detail
                if isinstance(detail, list):
                    parts = []
                    for item in detail:
                        if isinstance(item, dict):
                            loc = ".".join(str(x) for x in item.get("loc", []) if x != "body")
                            msg = item.get("msg", "Validation error")
                            parts.append(f"{loc}: {msg}" if loc else msg)
                        else:
                            parts.append(str(item))
                    return "; ".join(parts)
            return str(data)
        except Exception:
            return response.text or f"HTTP {response.status_code} Error"

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        use_root_url: bool = False,
    ) -> Any:
        """Execute an HTTP request against the FastAPI backend."""
        base = self.root_url if use_root_url else self.base_url
        url = f"{base}/{path.lstrip('/')}"
        headers = self._build_headers(token)

        # Clean None values from query parameters
        clean_params = (
            {k: v for k, v in params.items() if v is not None}
            if params
            else None
        )

        try:
            with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
                response = client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=clean_params,
                    json=json,
                )
        except httpx.ConnectError as exc:
            raise APIError(
                f"Cannot connect to ElderCare Backend API at {base}. "
                "Please ensure the FastAPI server is running (`uvicorn src.main:app --reload`)."
            ) from exc
        except httpx.TimeoutException as exc:
            raise APIError(
                f"Request to {path} timed out after {self.timeout}s."
            ) from exc
        except httpx.RequestError as exc:
            raise APIError(f"Network error while contacting backend: {exc}") from exc

        if response.status_code >= 400:
            error_msg = self._extract_error_message(response)
            payload = None
            try:
                payload = response.json()
            except Exception:
                payload = response.text
            raise APIError(
                message=error_msg,
                status_code=response.status_code,
                payload=payload,
            )

        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    def get(
        self,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self.request("GET", path, token=token, params=params)

    def post(
        self,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self.request("POST", path, token=token, json=json, params=params)

    def patch(
        self,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        return self.request("PATCH", path, token=token, json=json)

    def delete(
        self,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self.request("DELETE", path, token=token, params=params)

    def check_health(self) -> dict[str, Any]:
        """Check backend `/health` endpoint."""
        return self.request("GET", "/health", use_root_url=True)

