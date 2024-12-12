import urllib
from typing import List
from urllib.parse import unquote

import requests
from tqdm import tqdm

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

def parse_filename(content_disposition):
    if 'filename*=' in content_disposition:
        # Extract the UTF-8 filename
        filename_encoded = content_disposition.split("filename*=")[1].split(';')[0].strip()
        encoding, _, filename_encoded = filename_encoded.split("'", 2)
        filename = urllib.parse.unquote(filename_encoded)
    elif 'filename=' in content_disposition:
        # Fallback to plain filename
        filename = content_disposition.split("filename=")[1].split(';')[0].strip().strip('"')
    else:
        # Default filename if none provided
        filename = "default_filename"
    return filename

def download_from_url(download_url: str):
    # Perform the download
    response = requests.get(download_url, stream=True)
    response.raise_for_status()

    # Extract filename from headers, or fall back to a default name
    content_disposition = response.headers.get('Content-Disposition')

    filename = parse_filename(content_disposition)

    # Get the total file size from the Content-Length header (if available)
    total_size = int(response.headers.get('content-length', 0))

    # Open the file in binary write mode
    with open(filename, 'wb') as file:
        # Use tqdm for a progress bar (optional)
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as progress_bar:
            for chunk in response.iter_content(chunk_size=8192):
                # Write the chunk to the file
                file.write(chunk)

                # Update the progress bar
                progress_bar.update(len(chunk))
