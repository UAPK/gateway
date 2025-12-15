"""Webhook connector - POST to configured URL."""

import ipaddress
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from app.gateway.connectors.base import ConnectorConfig, ConnectorResult, ToolConnector


class WebhookConnector(ToolConnector):
    """Connector that POSTs to a configured webhook URL.

    Configuration:
        url: The webhook URL to POST to
        headers: Optional headers to include
        timeout_seconds: Request timeout (default 30s)
        secret_refs: Map of header names to secret names for auth

    No retries are performed (retries=0 as per spec).
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
        if not config.url:
            raise ValueError("WebhookConnector requires a 'url' in config")

    def _validate_url_ssrf(self, url: str) -> tuple[bool, str | None]:
        """Validate URL against SSRF attacks.

        Returns (is_valid, error_message).

        Blocks:
        - Private IP ranges (RFC 1918, loopback, link-local)
        - Invalid URLs
        - Non-HTTP(S) schemes

        Enforces allowed_domains if configured.
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ("http", "https"):
                return False, f"Invalid URL scheme: {parsed.scheme}"

            # Check hostname is present
            if not parsed.hostname:
                return False, "Missing hostname in URL"

            # Check allowed_domains if configured
            allowed_domains = self.config.extra.get("allowed_domains", [])
            if allowed_domains:
                hostname = parsed.hostname.lower()
                if not any(hostname.endswith(domain.lower()) for domain in allowed_domains):
                    return False, f"Domain '{parsed.hostname}' not in allowed list"

            # Resolve hostname to IP and check against blocked ranges
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
            return False, f"Invalid URL: {str(e)}"

    async def execute(self, params: dict[str, Any]) -> ConnectorResult:
        """Execute the webhook by POSTing params to the configured URL."""
        start_time = time.monotonic()

        url = self.config.url

        # SSRF protection - validate URL before making request
        is_valid, error_msg = self._validate_url_ssrf(url)
        if not is_valid:
            return ConnectorResult(
                success=False,
                error={
                    "code": "SSRF_BLOCKED",
                    "message": error_msg,
                },
                duration_ms=0,
            )

        headers = self._build_headers()
        headers.setdefault("Content-Type", "application/json")
        timeout = self.config.timeout_seconds

        # Resolve any secrets in params
        resolved_params = self._resolve_all_params(params)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json=resolved_params,
                    headers=headers,
                )

            duration_ms = int((time.monotonic() - start_time) * 1000)

            if response.status_code >= 200 and response.status_code < 300:
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
                        "message": f"Webhook returned status {response.status_code}",
                    },
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

        except httpx.TimeoutException:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return ConnectorResult(
                success=False,
                error={
                    "code": "TIMEOUT",
                    "message": f"Webhook request timed out after {timeout}s",
                },
                duration_ms=duration_ms,
            )

        except httpx.RequestError as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return ConnectorResult(
                success=False,
                error={
                    "code": "REQUEST_ERROR",
                    "message": str(e),
                },
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return ConnectorResult(
                success=False,
                error={
                    "code": "UNKNOWN_ERROR",
                    "message": str(e),
                },
                duration_ms=duration_ms,
            )
