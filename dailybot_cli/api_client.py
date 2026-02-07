"""HTTP client for DailyBot CLI API endpoints."""

from typing import Any, Optional

import httpx

from dailybot_cli.config import get_api_key, get_api_url, get_token


class APIError(Exception):
    """Raised when the API returns a non-success response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code: int = status_code
        self.detail: str = detail
        super().__init__(f"API error {status_code}: {detail}")


class DailyBotClient:
    """HTTP client for the DailyBot /v1/cli/* API endpoints."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_url: str = (api_url or get_api_url()).rstrip("/")
        self.token: Optional[str] = token or get_token()
        self.api_key: Optional[str] = api_key or get_api_key()
        self.timeout: float = timeout

    def _headers(self, authenticated: bool = True) -> dict[str, str]:
        """Build request headers."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if authenticated and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _agent_headers(self) -> dict[str, str]:
        """Build headers for agent API key authentication."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse API response and raise on errors."""
        if response.status_code >= 400:
            try:
                body: dict[str, Any] = response.json()
                detail: str = body.get("detail", body.get("error", str(body)))
            except Exception:
                detail = response.text or f"HTTP {response.status_code}"
            raise APIError(status_code=response.status_code, detail=detail)
        if response.status_code == 204:
            return {}
        return response.json()  # type: ignore[no-any-return]

    # --- Auth endpoints ---

    def request_code(self, email: str) -> dict[str, Any]:
        """POST /v1/cli/auth/request-code/"""
        response: httpx.Response = httpx.post(
            f"{self.api_url}/v1/cli/auth/request-code/",
            json={"email": email},
            headers=self._headers(authenticated=False),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def verify_code(
        self,
        email: str,
        code: str,
        organization_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """POST /v1/cli/auth/verify-code/"""
        payload: dict[str, Any] = {"email": email, "code": code}
        if organization_id is not None:
            payload["organization_id"] = organization_id
        response: httpx.Response = httpx.post(
            f"{self.api_url}/v1/cli/auth/verify-code/",
            json=payload,
            headers=self._headers(authenticated=False),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def auth_status(self) -> dict[str, Any]:
        """GET /v1/cli/auth/status/"""
        response: httpx.Response = httpx.get(
            f"{self.api_url}/v1/cli/auth/status/",
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def logout(self) -> dict[str, Any]:
        """POST /v1/cli/auth/logout/"""
        response: httpx.Response = httpx.post(
            f"{self.api_url}/v1/cli/auth/logout/",
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    # --- Update/Status endpoints ---

    def submit_update(
        self,
        message: Optional[str] = None,
        done: Optional[str] = None,
        doing: Optional[str] = None,
        blocked: Optional[str] = None,
    ) -> dict[str, Any]:
        """POST /v1/cli/updates/"""
        payload: dict[str, str] = {}
        if message:
            payload["message"] = message
        if done:
            payload["done"] = done
        if doing:
            payload["doing"] = doing
        if blocked:
            payload["blocked"] = blocked
        response: httpx.Response = httpx.post(
            f"{self.api_url}/v1/cli/updates/",
            json=payload,
            headers=self._headers(),
            timeout=120.0,
        )
        return self._handle_response(response)

    def get_status(self) -> dict[str, Any]:
        """GET /v1/cli/status/"""
        response: httpx.Response = httpx.get(
            f"{self.api_url}/v1/cli/status/",
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    # --- Agent endpoints ---

    def submit_agent_report(
        self,
        agent_name: str,
        content: str,
        structured: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """POST /v1/agent-reports/"""
        payload: dict[str, Any] = {
            "agent_name": agent_name,
            "content": content,
        }
        if structured:
            payload["structured"] = structured
        if metadata:
            payload["metadata"] = metadata
        response: httpx.Response = httpx.post(
            f"{self.api_url}/v1/agent-reports/",
            json=payload,
            headers=self._agent_headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)
