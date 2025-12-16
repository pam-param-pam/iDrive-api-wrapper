import json
import logging
import time
from json import JSONDecodeError

import httpx as httpx

from ..Config import APIConfig
from ..Constants import BASE_URL
from ..exceptions import BadRequestError, ResourcePermissionError, ResourceNotFoundError, MissingOrIncorrectResourcePasswordError, IDriveException, RateLimitError, UnauthorizedError, \
    ServiceUnavailableError, InternalServerError, BadMethodError, ServerTimeoutError, NetworkError

logger = logging.getLogger("iDrive")

httpxClient = httpx.Client(timeout=20.0)
DEFAULT_RETRY_AFTER = 5


def _mask_preserving_spaces(value: str) -> str:
    return "".join("*" if ch != " " else " " for ch in value)

def _get_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if APIConfig.token:
        headers['Authorization'] = f"Token {APIConfig.token}"
    return headers


def make_request(method: str, endpoint: str, data: dict = None, headers: dict = None, params: dict = None, files: dict = None, retry=True) -> dict:
    headers = {k: v for k, v in (headers or {}).items() if v is not None}
    headers.update(_get_headers())

    SENSITIVE_HEADERS = {"authorization"}
    safe_headers = {
        key: (_mask_preserving_spaces(value) if key.lower() in SENSITIVE_HEADERS else value)
        for key, value in headers.items()
    }
    url = f"{BASE_URL}/{endpoint}"
    logger.debug(f"Calling... Endpoint={endpoint}, Method={method}, Headers={safe_headers}")

    try:
        response = httpxClient.request(method, url, headers=headers, json=data, params=params, files=files, timeout=5)
    except httpx.TimeoutException as e:
        logger.warning(f"Request timeout: {method} {endpoint}")
        if retry:
            time.sleep(DEFAULT_RETRY_AFTER)
            return make_request(method, endpoint, data, headers, params, files, retry=False)
        raise ServerTimeoutError("Request timed out") from e

    except httpx.RequestError as e:
        logger.error(f"Server not responding: {method} {endpoint} ({e})")
        if retry:
            time.sleep(DEFAULT_RETRY_AFTER)
            return make_request(method, endpoint, data, headers, params, files, retry=False)
        raise NetworkError("Server not responding") from e

    if response.status_code == 429 and retry:
        retry_after = response.headers.get("Retry-After")
        wait_time = int(retry_after) if retry_after and retry_after.isdigit() else DEFAULT_RETRY_AFTER
        logger.warning(f"Rate limited (429). Retrying after {wait_time} seconds...")
        time.sleep(wait_time)
        return make_request(method, url, headers, data, params, files, retry=False)

    if not response.is_success:
        _raise_for_status(response)

    return response.json()

def _raise_for_status(response):
    status = response.status_code

    if status == 400:
        raise BadRequestError(response)
    elif status == 401:
        raise UnauthorizedError(response)
    elif status == 403:
        raise ResourcePermissionError(response)
    elif status == 404:
        raise ResourceNotFoundError(response)
    elif status == 405:
        raise BadMethodError(response)
    elif status == 500:
        raise InternalServerError(response)
    elif status == 503:
        raise ServiceUnavailableError(response)
    elif status == 469:
        raise MissingOrIncorrectResourcePasswordError(response)
    elif status == 429:
        raise RateLimitError(response)

    # fallback
    raise IDriveException(response)
