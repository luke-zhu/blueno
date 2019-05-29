"""
This module contains code for managing the samples in the dataset.
These are usually images stored on NFS, GCS, or similar alternatives.

To use this module. You should use get_storage_client() to get the correct
storage client. Then call on relevant methods defined in DataStoreInterface
to access the data.
"""
from . import clients


def _parse_prefix(url):
    low_idx = url.find('://')
    if low_idx == -1:
        raise ValueError("Could not find '://' in URL.")
    return url[0:url.find('://') + len('://')]


def get_storage_client(url) -> clients.DataStoreInterface:
    """
    Returns a new storage client for the given URL.

    :param url: a URL starting with gs:// or another registered scheme
    :return: a storage client
    :raise ValueError: if the URL is incorrectly formatted or if the client
        type does not exist
    """
    prefix = _parse_prefix(url)
    if prefix == clients.GCS_PREFIX:
        return clients.GCSStore()
    elif prefix == clients.AZURE_PREFIX:
        return clients.AzureStore()
    elif prefix == clients.TEMP_PREFIX:
        return clients.TempStore()
    elif prefix == clients.FILESYSTEM_PREFIX:
        return clients.FilesystemStore()
    else:
        raise ValueError(f"Store for prefix '{prefix}' not supported")
