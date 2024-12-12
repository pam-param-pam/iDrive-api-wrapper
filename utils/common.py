import cgi
import os
from typing import List
from urllib.parse import unquote

import requests

from models.Folder import Folder
from models.Item import Item
from utils.networker import make_request


def _extract_ids_and_passwords(items: List[Item]) -> dict:
    ids = []
    resourcePasswords = {}
    for item in items:
        if item._is_locked and item._password:
            resourcePasswords[item.id] = item._password
        ids.append(item.id)

    return {'ids': ids, 'resourcePasswords': resourcePasswords}


def move_to_trash(items: List[Item]) -> None:
    data = _extract_ids_and_passwords(items)
    make_request("PATCH", f"item/moveToTrash", data)


def delete(items: List[Item]) -> None:
    data = _extract_ids_and_passwords(items)
    make_request("PATCH", f"item/delete", data)


def restore_from_trash(items: List[Item]) -> None:
    data = _extract_ids_and_passwords(items)
    make_request("PATCH", f"item/restoreFromTrash", data)


def move(items: List[Item], new_parent: Folder) -> None:
    data = _extract_ids_and_passwords(items)
    data['new_parent_id'] = new_parent.id
    make_request("PATCH", f"item/move", data)


def get_zip_download_url(items: List[Item]) -> str:
    data = _extract_ids_and_passwords(items)
    data = make_request("POST", f"zip", data)
    return data['download_url']


def download_from_url(download_url: str):
    # Perform the download
    response = requests.get(download_url, stream=True)
    response.raise_for_status()

    # Extract filename from headers, or fall back to a default name
    content_disposition = response.headers.get('Content-Disposition')

    print(content_disposition)

    # attachment; filename="Seven%20Nation%20Army%20can%27t%20stop%20the%20United%20States%20%28ww2%20edit%29.mp4"; filename*=UTF-8''Seven%20Nation%20Army%20can%27t%20stop%20the%20United%20States%20%28ww2%20edit%29.mp4
    # todo fix filename, support both filename and filename*utf-8
    filename = "aaaa"
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
            f.write(chunk)
