import os
from typing import List

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


async def move_to_trash(items: List[Item]) -> None:
    data = _extract_ids_and_passwords(items)
    await make_request("PATCH", f"item/moveToTrash", data)


async def delete(items: List[Item]) -> None:
    data = _extract_ids_and_passwords(items)
    await make_request("PATCH", f"item/delete", data)


async def restore_from_trash(items: List[Item]) -> None:
    data = _extract_ids_and_passwords(items)
    await make_request("PATCH", f"item/restoreFromTrash", data)


async def move(items: List[Item], new_parent: Folder) -> None:
    data = _extract_ids_and_passwords(items)
    data['new_parent_id'] = new_parent.id
    await make_request("PATCH", f"item/move", data)


async def get_zip_download_url(items: List[Item]) -> str:
    data = _extract_ids_and_passwords(items)
    data = await make_request("POST", f"zip", data)
    return data['download_url']


async def download_from_url(download_url: str):
    # Perform the download
    response = requests.get(download_url, stream=True)
    response.raise_for_status()

    # Extract filename from headers, or fall back to a default name
    content_disposition = response.headers.get('Content-Disposition')
    if content_disposition and 'filename=' in content_disposition:
        filename = content_disposition.split('filename=')[1].strip('"')
    else:
        filename = 'downloaded_file.zip'

    # Ensure safe filename in case of special characters
    filename = os.path.basename(filename)

    # Save the file
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
            f.write(chunk)
