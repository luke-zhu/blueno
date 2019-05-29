"""
Simple clients to different storage options.

To use these, you should set the corresponding environment variables,
call get_storage_client() to get the correct storage client,
and then use the desired DataStoreInterface method.
"""
import datetime
import io
import pathlib
import time
import urllib.parse
from abc import ABCMeta, abstractmethod
from typing import Optional, Tuple, BinaryIO

import flask
from azure.storage.blob import BlockBlobService, BlobPermissions
from google.cloud.storage import Client as GCSClient

from app import env

GCS_PREFIX = 'gs://'
AZURE_PREFIX = 'az://'
TEMP_PREFIX = 'temp://'
FILESYSTEM_PREFIX = 'file://'


class DataStoreInterface(object):
    """
    An generic storage interface.

    sample_urls are 'fake' URLs prefixed with 'gs://', 'az://' or 's3://'
    instead of 'http://'.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, sample_url: str) -> BinaryIO:
        """
        Retrieves the contents at the given URL.

        The behavior for when the object does not exist is undefined.
        """
        raise NotImplementedError()

    @abstractmethod
    def put(self, sample_url: str, stream: BinaryIO):
        """
        Saves contents of the stream at the given URL.

        An exception will likely be thrown if you do not have
        write access to the location of sample_url.
        """
        raise NotImplementedError()

    @abstractmethod
    def exists(self, sample_url) -> bool:
        """Checks whether the object with the given url exists."""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, sample_url):
        """Deletes the object at the given url.

        The behavior for when the object does not exist is undefined.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_signed_url(self, sample_url) -> str:
        """
        Returns a public signed HTTPS URL for the given object that
        lasts for 15 minutes.

        The behavior for when the object does not exist is undefined.
        """
        raise NotImplementedError()


class _ClientCache(object):
    # Not thread-safe but it seems to work.

    def __init__(self):
        self._data = {}

    def get(self, username) -> Optional:
        value = self._data.get(username, None)
        if value is None:
            return None
        client, last_used = value
        if time.time() - last_used > 60:
            del self._data[username]
            return None

        return client

    def put(self, username: str, client):
        self._data[username] = client, time.time()


class GCSStore(DataStoreInterface):
    client_cache = _ClientCache()

    def __init__(self):
        client = self.client_cache.get('gcs')
        if client is None:
            self.client = GCSClient.from_service_account_json(
                env.GOOGLE_APPLICATION_CREDENTIALS
            )
        else:
            self.client: GCSClient = client
            self.client_cache.get('gcs')
        self.client_cache.put('gcs', self.client)

    def get(self, sample_url: str) -> BinaryIO:
        bucket_name, blob_name = self._parse_url(sample_url)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.get_blob(blob_name)
        stream = io.BytesIO()
        blob.download_to_file(stream)
        stream.seek(0)
        return stream

    def put(self, sample_url: str, stream: BinaryIO):
        bucket_name, blob_name = self._parse_url(sample_url)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_file(stream)

    def exists(self, sample_url) -> bool:
        bucket_name, blob_name = self._parse_url(sample_url)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()

    def delete(self, sample_url):
        bucket_name, blob_name = self._parse_url(sample_url)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()

    def get_signed_url(self, sample_url) -> str:
        bucket_name, blob_name = self._parse_url(sample_url)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.generate_signed_url(
            expiration=datetime.timedelta(minutes=15)
        )

    @staticmethod
    def _parse_url(url: str):
        if not url.startswith(GCS_PREFIX):
            raise ValueError(f"URL should start with {GCS_PREFIX}")
        bucket_name, blob_name = url[len(GCS_PREFIX):].split('/', maxsplit=1)
        return bucket_name, blob_name


class AzureStore(DataStoreInterface):
    service_cache = _ClientCache()

    def __init__(self):
        service = self.service_cache.get('azure')
        if service is None:
            self.service = BlockBlobService(**env.AZURE_STORAGE_CREDENTIALS)
        else:
            self.service: BlockBlobService = service
            self.service_cache.get('azure')
        self.service_cache.put('azure', self.service)

    def get(self, sample_url: str) -> BinaryIO:
        container_name, blob_name = self._parser_url(sample_url)
        stream = io.BytesIO()
        self.service.get_blob_to_stream(container_name, blob_name, stream)
        stream.seek(0)
        return stream

    def put(self, sample_url: str, stream: BinaryIO):
        container_name, blob_name = self._parser_url(sample_url)
        self.service.create_container(container_name)
        self.service.create_blob_from_stream(container_name, blob_name, stream)

    def exists(self, sample_url) -> bool:
        container_name, blob_name = self._parser_url(sample_url)
        return self.service.exists(container_name, blob_name)

    def delete(self, sample_url):
        container_name, blob_name = self._parser_url(sample_url)
        self.service.delete_blob(container_name, blob_name)

    def get_signed_url(self, sample_url) -> str:
        container_name, blob_name = self._parser_url(sample_url)
        signature = self.service.generate_blob_shared_access_signature(
            container_name,
            blob_name,
            permission=BlobPermissions(read=True),
            expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
        )
        url = self.service.make_blob_url(container_name,
                                         blob_name,
                                         protocol='https',
                                         sas_token=signature)
        return url

    @staticmethod
    def _parser_url(url) -> Tuple[str, str]:
        if not url.startswith(AZURE_PREFIX):
            raise ValueError(f"URL should start with {AZURE_PREFIX}")
        container_name, blob_name = url[len(AZURE_PREFIX):].split(
            '/', maxsplit=1)
        return container_name, blob_name


class TempStore(DataStoreInterface):
    """
    An in-memory data store. Useful for testing.
    """

    data = {}

    def get(self, sample_url: str) -> BinaryIO:
        return self.data[sample_url]

    def put(self, sample_url: str, stream: BinaryIO):
        self.data[sample_url] = stream

    def exists(self, sample_url) -> bool:
        return sample_url in self.data

    def delete(self, sample_url):
        del self.data[sample_url]

    def get_signed_url(self, sample_url) -> str:
        # This doesn't actually return a public URL, it's only here for
        # testing purposes
        return sample_url


class FilesystemStore(DataStoreInterface):
    def __init__(self):
        self.root_path = pathlib.Path(env.FILESYSTEM_STORE_ROOT).resolve()

    # TODO: Make the blueno-server pod restart itself if it fails to
    #  a stale file handle error
    def get(self, sample_url: str) -> BinaryIO:
        path = self._parse_url(sample_url)
        return path.open('rb')

    def put(self, sample_url: str, stream: BinaryIO):
        path = self._parse_url(sample_url)
        parent: pathlib.Path = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        with path.open('wb') as f:
            f.write(stream.read())

    def exists(self, sample_url) -> bool:
        path = self._parse_url(sample_url)
        return path.exists()

    def delete(self, sample_url):
        path = self._parse_url(sample_url)
        path.unlink()  # Note that this doesn't delete empty parent directories

    def get_signed_url(self, sample_url) -> str:
        return urllib.parse.urljoin(flask.request.host_url,
                                    f'/data/download?url={sample_url}')

    def _parse_url(self, url) -> pathlib.Path:
        if not url.startswith(FILESYSTEM_PREFIX):
            raise ValueError(f"URL should start with {FILESYSTEM_PREFIX}")
        relative_path = url[len(FILESYSTEM_PREFIX):]
        if relative_path.startswith('/'):
            raise ValueError(
                f"Expected relative path, got absolute path {relative_path}")
        return self.root_path / relative_path
