"""HTTP Request connector - generic HTTP requests with domain allowlist."""

import ipaddress
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.gateway.connectors.base import ConnectorConfig, ConnectorResult, ToolConnector


class HttpRequestConnector(ToolConnector):
    """Connector for generic HTTP requests with strict domain allowlist.

    Configuration:
        url: The URL template (can contain {param} placeholders)
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        headers: Optional headers
        timeout_seconds: Request timeout
        extra.allowed_domains: List of allowed domains (overrides global setting)

    Security:
        - Only requests to allowlisted domains are permitted
        - SSRF protection: blocks private IP ranges
        - URL is validated before request
    """

    # Private IP ranges to block (SSRF protection)
    BLOCKED_IP_RANGES = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),  # IPv6 localhost
        ipaddress.ip_network("fc00::/7"),  # IPv6 ULA
        ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
    ]

    def __init__(self, config: ConnectorConfig, secrets: dict[str, str] | None = None) -> None:
        super().__init__(config, secrets)
        self.settings = get_settings()

    def _get_allowed_domains(self) -> list[str]:
        """Get the list of allowed domains."""
        # First check connector-specific allowlist
        if self.config.extra.get("allowed_domains"):
            return self.config.extra["allowed_domains"]
        # Fall back to global setting
        return self.settings.gateway_allowed_webhook_domains

    def _validate_url(self, url: str) -> tuple[bool, str | None]:
        """Validate URL is in allowed domains and not targeting private IPs.

        Returns (is_valid, error_message).
        """
        allowed_domains = self._get_allowed_domains()

        # If no domains configured, deny by default for security
        if not allowed_domains:
            return False, "No allowed domains configured"

        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ("http", "https"):
                return False, f"Invalid URL scheme: {parsed.scheme}"

            # Check hostname is present
            if not parsed.hostname:
                return False, "Missing hostname in URL"

            domain = parsed.hostname.lower()

            # Check against allowed domains
            domain_allowed = False
            for allowed in allowed_domains:
                allowed = allowed.lower()
                # Exact match or subdomain match
                if domain == allowed or domain.endswith(f".{allowed}"):
                    domain_allowed = True
                    break

            if not domain_allowed:
                return False, f"Domain '{domain}' not in allowlist"

            # SSRF protection - check for private IP ranges
            try:
                # Get all IP addresses for the hostname
                addr_info = socket.getaddrinfo(parsed.hostname, None)
                for info in addr_info:
                    ip_str = info[4][0]
                    ip_addr = ipaddress.ip_address(ip_str)

                    # Check if IP is in any blocked range
                    for blocked_range in self.BLOCKED_IP_RANGES:
                        if ip_addr in blocked_range:
                            return False, f"Access to private/internal IP {ip_str} blocked (SSRF protection)"

            except socket.gaierror:
                return False, f"Could not resolve hostname: {parsed.hostname}"

            return True, None

        except Exception as e:
            return False, f"Invalid URL: {e}"

    def _build_url(self, params: dict[str, Any]) -> str:
        """Build the final URL, substituting placeholders."""
        url = self.config.url or ""

        # Substitute {param} placeholders
        for key, value in params.items():
            placeholder = f"{{{key}}}"
            if placeholder in url:
                url = url.replace(placeholder, str(value))

        return url

    async def execute(self, params: dict[str, Any]) -> ConnectorResult:
        """Execute the HTTP request."""
        start_time = time.monotonic()

        # Build and validate URL
        url = self._build_url(params)
        is_valid, error = self._validate_url(url)

        if not is_valid:
            return ConnectorResult(
                success=False,
                error={
                    "code": "DOMAIN_NOT_ALLOWED",
                    "message": error or "URL validation failed",
                },
                duration_ms=int((time.monotonic() - start_time) * 1000),
            )

        method = self.config.method.upper()
        headers = self._build_headers()
        timeout = self.config.timeout_seconds

        # Resolve secrets in params
        resolved_params = self._resolve_all_params(params)

        # Remove params that were used in URL template
        body_params = {k: v for k, v in resolved_params.items() if f"{{{k}}}" not in (self.config.url or "")}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method in ("GET", "DELETE"):
                    response = await client.request(
                        method,
                        url,
                        params=body_params if body_params else None,
                        headers=headers,
                    )
                else:
                    headers.setdefault("Content-Type", "application/json")
                    response = await client.request(
                        method,
                        url,
                        json=body_params if body_params else None,
                        headers=headers,
                    )

            duration_ms = int((time.monotonic() - start_time) * 1000)

            if 200 <= response.status_code < 300:
                try:
                    data = response.json()
                except Exception:
                    data = {"raw_response": response.text}

                result = ConnectorResult(
                    success=True,
                    data=data,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )
                result.result_hash = result.compute_hash()
                return result
            else:
                return ConnectorResult(
                    success=False,
                    error={
                        "code": f"HTTP_{response.status_code}",
                        "message": f"Request returned status {response.status_code}",
                    },
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

        except httpx.TimeoutException:
            return ConnectorResult(
                success=False,
                error={
                    "code": "TIMEOUT",
                    "message": f"Request timed out after {timeout}s",
                },
                duration_ms=int((time.monotonic() - start_time) * 1000),
            )

        except httpx.RequestError as e:
            return ConnectorResult(
                success=False,
                error={
                    "code": "REQUEST_ERROR",
                    "message": str(e),
                },
                duration_ms=int((time.monotonic() - start_time) * 1000),
            )

        except Exception as e:
            return ConnectorResult(
                success=False,
                error={
                    "code": "UNKNOWN_ERROR",
                    "message": str(e),
                },
                duration_ms=int((time.monotonic() - start_time) * 1000),
            )
