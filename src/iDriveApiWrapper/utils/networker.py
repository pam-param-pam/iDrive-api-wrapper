import json
import logging
import time
from json import JSONDecodeError

import httpx as httpx

from ..Config import APIConfig
from ..Constants import BASE_URL
from ..exceptions import BadRequestError, ResourcePermissionError, ResourceNotFoundError, MissingOrIncorrectResourcePasswordError, IDriveException, RateLimitException, UnauthorizedError, \
    ServiceUnavailable, InternalServerError

logger = logging.getLogger("iDrive")

httpxClient = httpx.Client(timeout=20.0)
DEFAULT_RETRY_AFTER = 5


def _get_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if APIConfig.token:
        headers['Authorization'] = f"Token {APIConfig.token}"
    return headers


def make_request(method: str, endpoint: str, data: dict = None, headers: dict = None, params: dict = None, files: dict = None) -> dict:
    if headers is None:
        headers = {}

    logger.debug(f"Calling... Endpoint={endpoint}, Method={method}, Headers={headers}")
    url = f"{BASE_URL}/{endpoint}"
    headers.update(_get_headers())

    response = httpxClient.request(method, url, headers=headers,  json=data, params=params, files=files)
    if not response.is_success:
        try:
            error = json.loads(response.content)
        except JSONDecodeError:
            error = response.content
        if response.status_code == 400:
            raise BadRequestError(error)
        elif response.status_code == 401:
            raise UnauthorizedError(error)
        elif response.status_code == 403:
            raise ResourcePermissionError(error)
        elif response.status_code == 404:
            raise ResourceNotFoundError(error)
        elif response.status_code == 500:
            raise InternalServerError(error)
        elif response.status_code == 503:
            raise ServiceUnavailable(error)

        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait_time = int(retry_after) if retry_after and retry_after.isdigit() else DEFAULT_RETRY_AFTER
            logger.warning(f"Rate limited (429). Retrying after {wait_time} seconds...")
            time.sleep(wait_time)

            # Retry once
            response = httpxClient.request(method, url, headers=headers, json=data, params=params, files=files)

            if not response.is_success:
                try:
                    error = json.loads(response.content)
                except JSONDecodeError:
                    error = response.content
                raise RateLimitException(error)
        elif response.status_code == 469:
            raise MissingOrIncorrectResourcePasswordError(error)
        else:
            raise IDriveException(error)

    if response.status_code == 200:
        return response.json()
