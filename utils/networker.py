import json
import logging
from json import JSONDecodeError

import requests

from Config import APIConfig
from Constants import BASE_URL
from exceptions import IDriveException, UnauthorizedError, ResourceNotFoundError, ResourcePermissionError, MissingOrIncorrectResourcePasswordError, BadRequestError, RateLimitException

logger = logging.getLogger("iDrive")


def _get_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if APIConfig.token:
        headers['Authorization'] = f"Token {APIConfig.token}"
    return headers

def make_request(method: str, endpoint: str, data: dict = None, headers: dict = None, params: dict = None):
    if headers is None:
        headers = {}

    logger.debug(f"Calling... Endpoint={endpoint}, Method={method}, Headers={headers}")
    url = f"{BASE_URL}/{endpoint}"
    headers.update(_get_headers())
    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers, json=data)
    elif method.upper() == "PATCH":
        response = requests.patch(url, headers=headers, json=data)
    else:
        raise ValueError("Unsupported HTTP method")

    if not response.ok:
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
        elif response.status_code == 429:
            raise RateLimitException(error)
        elif response.status_code == 469:
            raise MissingOrIncorrectResourcePasswordError(error)
        else:
            raise IDriveException(error)

    if response.status_code == 200:
        return response.json()
