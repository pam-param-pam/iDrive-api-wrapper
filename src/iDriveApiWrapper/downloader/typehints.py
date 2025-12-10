from typing import Union, List

from ..models.File import File
from ..models.Folder import Folder

Downloadable = Union[File, Folder]

DownloadInput = Union[List[Downloadable], Downloadable]
