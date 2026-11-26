"""
SSRF-Safe URL Validator & HTTP Fetcher for Job Description Import
Phase 6 | Feature 34: Job Description URL Import
"""

import ipaddress
import logging
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse, urlunparse

import httpx

logger = logging.getLogger(__name__)

MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB
REQUEST_TIMEOUT_SECONDS = 10.0
CONNECT_TIMEOUT_SECONDS = 5.0

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata",
    "metadata.google.internal",
    "metadata.goog",
    "169.254.169.254",
}

UNSUPPORTED_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "pinterest.com",
    "google.com",
    "bing.com",
    "netflix.com",
    "spotify.com",
}

SUPPORTED_BOARD_HINTS = {
    "linkedin.com": "linkedin",
    "indeed.com": "indeed",
    "wellfound.com": "wellfound",
    "angel.co": "wellfound",
    "naukri.com": "naukri",
}


class JobImportError(Exception):
    """Base error for job URL import."""

    def __init__(self, message: str, status_code: int = 422, code: str = "JOB_IMPORT_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class URLValidationError(JobImportError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400, code="INVALID_URL")


class UnsupportedDomainError(JobImportError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422, code="UNSUPPORTED_DOMAIN")


class SSRFBlockedError(JobImportError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400, code="SSRF_BLOCKED")


class JobImportBlockedError(JobImportError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422, code="ACCESS_BLOCKED")


class JobImportSizeError(JobImportError):
    def __init__(self, message: str):
        super().__init__(message, status_code=413, code="RESPONSE_TOO_LARGE")


class JobImportFetchError(JobImportError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, status_code=status_code, code="FETCH_FAILED")


@dataclass
class FetchedPage:
    final_url: str
    html: str
    content_type: str
    source_platform: str


def _is_public_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return (
        ip_obj.is_global
        and not ip_obj.is_private
        and not ip_obj.is_loopback
        and not ip_obj.is_link_local
        and not ip_obj.is_multicast
        and not ip_obj.is_reserved
        and not ip_obj.is_unspecified
    )


def _match_domain(hostname: str, domain_set: set[str]) -> Optional[str]:
    for domain in domain_set:
        if hostname == domain or hostname.endswith(f".{domain}"):
            return domain
    return None


def _detect_source_platform(hostname: str) -> str:
    matched = _match_domain(hostname, set(SUPPORTED_BOARD_HINTS.keys()))
    if matched:
        return SUPPORTED_BOARD_HINTS[matched]
    return "company_career_page"


def _validate_host_security(hostname: str) -> None:
    host = hostname.strip().lower().rstrip(".")
    if not host:
        raise URLValidationError("URL must include a valid hostname.")

    if (
        host in BLOCKED_HOSTNAMES
        or host.endswith(".local")
        or host.endswith(".internal")
        or host.endswith(".localhost")
        or host.endswith(".arpa")
    ):
        raise SSRFBlockedError("Access to localhost or internal network addresses is not permitted.")

    # Check if host is a direct IP literal
    try:
        ip_obj = ipaddress.ip_address(host)
    except ValueError:
        ip_obj = None

    if ip_obj is not None:
        if not _is_public_ip(str(ip_obj)):
            raise SSRFBlockedError("Access to private, loopback, or reserved IP addresses is not permitted.")
        return

    if _match_domain(host, UNSUPPORTED_DOMAINS):
        raise UnsupportedDomainError(
            f"Unsupported website '{host}'. Please provide a job board or company career page URL, or use manual input."
        )

    # Resolve DNS and verify every resolved IP is public
    try:
        addr_info = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise JobImportFetchError(f"Could not resolve domain '{host}'.", status_code=422)

    resolved_ips = {info[4][0] for info in addr_info if info and info[4]}
    if not resolved_ips:
        raise JobImportFetchError(f"Could not resolve IP address for '{host}'.", status_code=422)

    for ip_str in resolved_ips:
        # Strip IPv6 scope ID if present (e.g. fe80::1%eth0)
        clean_ip = ip_str.split("%", 1)[0]
        if not _is_public_ip(clean_ip):
            raise SSRFBlockedError(
                "Target domain resolves to a private, loopback, or restricted network address."
            )


def normalize_and_validate_url(raw_url: str) -> tuple[str, str]:
    """
    Validates URL format, scheme (HTTP/HTTPS only), port, and SSRF safety.
    Returns (normalized_url, source_platform).
    """
    if not raw_url or not isinstance(raw_url, str):
        raise URLValidationError("Job posting URL is required.")

    cleaned = raw_url.strip()
    if len(cleaned) > 2048:
        raise URLValidationError("URL exceeds maximum length of 2048 characters.")

    parsed = urlparse(cleaned)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise URLValidationError("Only HTTP and HTTPS URLs are supported.")

    if not parsed.netloc or not parsed.hostname:
        raise URLValidationError("Invalid URL format: missing hostname.")

    if parsed.username or parsed.password:
        raise URLValidationError("URLs containing embedded credentials are not permitted.")

    try:
        port = parsed.port
    except ValueError:
        raise URLValidationError("Invalid port in URL.")

    if port is not None and port not in (80, 443):
        raise URLValidationError("Only standard HTTP (80) and HTTPS (443) ports are permitted.")

    _validate_host_security(parsed.hostname)
    platform = _detect_source_platform(parsed.hostname.lower())

    normalized = urlunparse(
        (
            scheme,
            parsed.netloc,
            parsed.path or "/",
            parsed.params,
            parsed.query,
            "",  # Strip fragment
        )
    )
    return normalized, platform


async def fetch_job_page(
    url: str,
    client: Optional[httpx.AsyncClient] = None,
) -> FetchedPage:
    """
    Fetches a public job posting HTML page with SSRF redirect re-validation,
    strict timeouts, content-type verification, and response size limits.
    """
    current_url, platform = normalize_and_validate_url(url)

    headers = {
        "User-Agent": "NexoraAI-JobImporter/1.0 (+https://nexora.ai)",
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    owns_client = client is None
    if owns_client:
        timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS)
        client = httpx.AsyncClient(follow_redirects=False, timeout=timeout, headers=headers)

    try:
        for _ in range(MAX_REDIRECTS + 1):
            current_url, platform = normalize_and_validate_url(current_url)

            try:
                async with client.stream("GET", current_url) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if not location:
                            raise JobImportFetchError("Redirect response missing Location header.")
                        current_url = urljoin(current_url, location)
                        continue

                    if response.status_code in (401, 403):
                        raise JobImportBlockedError(
                            "This page requires authentication or blocked automated access. Please paste the job description manually."
                        )

                    if response.status_code == 429:
                        raise JobImportBlockedError(
                            "The target website rate-limited this request. Please try again later or paste the job description manually."
                        )

                    if response.status_code >= 400:
                        raise JobImportFetchError(
                            f"Target website returned HTTP {response.status_code}.",
                            status_code=502,
                        )

                    content_type = (response.headers.get("content-type") or "").lower()
                    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                        raise JobImportError(
                            f"Unsupported content type '{content_type or 'unknown'}'. Expected an HTML job page.",
                            status_code=422,
                            code="UNSUPPORTED_CONTENT_TYPE",
                        )

                    content_length_hdr = response.headers.get("content-length")
                    if content_length_hdr:
                        try:
                            if int(content_length_hdr) > MAX_RESPONSE_BYTES:
                                raise JobImportSizeError(
                                    f"Response exceeds maximum allowed size of {MAX_RESPONSE_BYTES // (1024 * 1024)} MB."
                                )
                        except ValueError:
                            pass

                    chunks: list[bytes] = []
                    total_bytes = 0
                    async for chunk in response.aiter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > MAX_RESPONSE_BYTES:
                            raise JobImportSizeError(
                                f"Response exceeds maximum allowed size of {MAX_RESPONSE_BYTES // (1024 * 1024)} MB."
                            )
                        chunks.append(chunk)

                    raw_bytes = b"".join(chunks)
                    encoding = response.encoding or "utf-8"
                    html = raw_bytes.decode(encoding, errors="replace")
                    return FetchedPage(
                        final_url=current_url,
                        html=html,
                        content_type=content_type,
                        source_platform=platform,
                    )

            except httpx.TimeoutException:
                raise JobImportFetchError(
                    "Request timed out while fetching the job posting. Please try again or enter the job description manually.",
                    status_code=504,
                )
            except httpx.RequestError as exc:
                logger.warning("Network error fetching %s: %s", current_url, exc)
                raise JobImportFetchError(
                    "Unable to reach the target website. Please verify the URL or enter the job description manually.",
                    status_code=502,
                )

        raise JobImportFetchError("Too many redirects while fetching the job posting.", status_code=502)
    finally:
        if owns_client:
            await client.aclose()
