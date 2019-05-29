import io

import pytest

from app import env, app
from app.storage import clients


@pytest.mark.skipif(env.AZURE_STORAGE_CREDENTIALS is None,
                    reason='GCP credentials needed')
def test_azure_store():
    client = clients.AzureStore()
    url = 'az://blueno/test_azure_store.txt'

    test_bytes = b'test stringfdfdfdf'
    upload_stream = io.BytesIO(test_bytes)
    client.put(url, upload_stream)
    assert client.exists(url)

    download_stream = client.get(url)
    assert download_stream.read() == test_bytes

    client.delete(url)
    assert not client.exists(url)


@pytest.mark.skipif(env.AZURE_STORAGE_CREDENTIALS is None,
                    reason='Azure credentials needed')
def test_azure_get_signed_url():
    az_client = clients.AzureStore()

    url = 'az://blueno/test/test_azure_get_signed_url.txt'
    stream = io.BytesIO(b'test: test_azure_get_signed_url')
    az_client.put(url, stream)
    assert az_client.get_signed_url(url).startswith('https://')


@pytest.mark.skipif(env.GOOGLE_APPLICATION_CREDENTIALS is None,
                    reason='GCP credentials needed')
def test_gcs_store():
    client = clients.GCSStore()
    # TODO: This test only works if the user has write access to elvo-platform
    url = 'gs://elvo-platform/test_gcs_store.txt'

    test_bytes = b'test stringfdfdfdf'
    upload_stream = io.BytesIO(test_bytes)
    client.put(url, upload_stream)
    assert client.exists(url)

    download_stream = client.get(url)
    assert download_stream.read() == test_bytes

    client.delete(url)
    assert not client.exists(url)


# Duplicated once in image_test.py
@pytest.mark.skipif(env.GOOGLE_APPLICATION_CREDENTIALS is None,
                    reason='GCP credentials needed')
def test_gcs_get_signed_url():
    gcs_client = clients.GCSStore()
    # TODO: This test only works if the user has write access to elvo-platform
    url = 'gs://elvo-platform/test/test_gcs_get_signed_url.md'
    stream = io.BytesIO(b'test: test_gcs_get_signed_url')
    gcs_client.put(url, stream)
    assert gcs_client.get_signed_url(url).startswith('https://')


@pytest.mark.skipif(env.FILESYSTEM_STORE_ROOT is None,
                    reason='Filesystem configuration needed')
def test_filesystem_store():
    client = clients.FilesystemStore()
    url = 'file://test_filesystem_store.txt'

    test_bytes = b'test stringfdfdfdf'
    upload_stream = io.BytesIO(test_bytes)
    client.put(url, upload_stream)
    assert client.exists(url)

    download_stream = client.get(url)
    assert download_stream.read() == test_bytes

    client.delete(url)
    assert not client.exists(url)


@pytest.mark.skipif(env.FILESYSTEM_STORE_ROOT is None,
                    reason='Filesystem configuration needed')
def test_fileystem_signed_url():
    client = clients.FilesystemStore()
    url = 'file://test_fileystem_signed_url.txt'
    stream = io.BytesIO(b'test: test_gcs_get_signed_url')
    client.put(url, stream)
    with app.test_request_context('http://www.example.com/rest/of/the/route'):
        assert client.get_signed_url(url) == \
               f'http://www.example.com/data/download?url={url}'
