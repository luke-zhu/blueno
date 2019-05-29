import io

import numpy
import pytest

from app import app, env, image, storage


def test_create_images_2d_npy_3_channels():
    arr = numpy.zeros((5, 5, 3))
    stream = io.BytesIO()
    numpy.save(stream, arr)
    stream.seek(0)

    image_type = '2D'
    image_url = 'temp://2d-array'
    data_url = 'temp://2d-array.npy'

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    image._create_images(image_type, image_url, data_url)
    assert client.exists(image_url + '.jpg')


def test_create_images_2d_npy_1_channel():
    arr = numpy.zeros((5, 5, 1))
    stream = io.BytesIO()
    numpy.save(stream, arr)
    stream.seek(0)

    image_type = '2D'
    image_url = 'temp://2d-array.jpg'
    data_url = 'temp://2d-array.npy'

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    image._create_images(image_type, image_url, data_url)
    assert client.exists(image_url + '.jpg')


def test_create_images_2d_npy_flattened():
    arr = numpy.zeros((5, 5))
    stream = io.BytesIO()
    numpy.save(stream, arr)
    stream.seek(0)

    image_type = '2D'
    image_url = 'temp://2d-array.jpg'
    data_url = 'temp://2d-array.npy'

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    image._create_images(image_type, image_url, data_url)
    assert client.exists(image_url + '.jpg')


def test_create_images_2d_npz():
    # This used to be supported now it should throw an exception
    arr0 = numpy.zeros((5, 5))
    arr1 = numpy.ones((5, 4, 1))
    arr2 = numpy.ones((6, 2, 3))
    stream = io.BytesIO()
    numpy.savez(stream, arr0, arr1, arr2)
    stream.seek(0)

    image_type = '2D'
    image_url = 'temp://2d-array.jpg'
    data_url = 'temp://2d-array.npz'

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    with pytest.raises(IOError):
        image._create_images(image_type, image_url, data_url)


def test_create_images_3d_npy():
    arr = numpy.zeros((5, 5, 10))
    stream = io.BytesIO()
    numpy.save(stream, arr)
    stream.seek(0)

    image_type = '3D'
    image_url = 'temp://3d-array'
    data_url = 'temp://3d-array.npy'

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    image._create_images(image_type, image_url, data_url)
    assert client.exists(f'{image_url}-{0}.jpg')
    assert client.exists(f'{image_url}-{4}.jpg')
    assert not client.exists(f'{image_url}-{5}.jpg')


def test_create_images_3d_npz():
    # npz files are no longer supported
    arr_0 = numpy.zeros((5, 5, 9))
    arr_1 = numpy.ones((111, 4, 5))
    arr_2 = numpy.ones((6, 2, 17))
    stream = io.BytesIO()
    numpy.savez(stream, arr_0, arr_1, arr_2)
    stream.seek(0)

    image_type = '3D'
    image_url = 'temp://3d-array'
    data_url = 'temp://3d-array.npz'

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    with pytest.raises(ValueError):
        image._create_images(image_type, image_url, data_url)


def test_get_images_jpg():
    stream = io.BytesIO(b'some bytes that should represent a JPG file')
    stream.seek(0)

    data_url1 = 'temp://blueno/some-image.jpg'
    data_url2 = 'temp://blueno/some-image.JPEG'

    client = storage.get_storage_client(data_url1)
    client.put(data_url1, stream)
    client.put(data_url2, stream)

    urls1 = image.get_images({'data': {'url': data_url1}}, 1, 0)
    urls2 = image.get_images({'data': {'url': data_url2}}, 1, 0)
    assert len(urls1) == 1
    assert len(urls2) == 1


@pytest.mark.skipif(env.GOOGLE_APPLICATION_CREDENTIALS is None,
                    reason='GCP credentials needed')
def test_get_images_gcs1():
    image_type = '2D'
    image_url = 'gs://a-bucket/2d-array'
    info = {
        'image': {
            'url': image_url,
            'type': image_type,
        }
    }

    urls = image.get_images(info, 1, 0)
    assert len(urls) == 1
    assert urls[0].startswith(
        'https://storage.googleapis.com/a-bucket/2d-array.jpg')


@pytest.mark.skipif(env.GOOGLE_APPLICATION_CREDENTIALS is None,
                    reason='GCP credentials needed')
def test_get_images_gcs2():
    image_type = '3D'
    image_url = 'gs://a-bucket/3d-array'
    info = {
        'image': {
            'url': image_url,
            'type': image_type,
            'count': 16,
        }
    }

    urls = image.get_images(info, 16, 12)
    assert len(urls) == 4  # we get images 12,13,14,15
    assert urls[0].startswith(
        'https://storage.googleapis.com/a-bucket/3d-array-12.jpg')


@pytest.mark.skipif(env.AZURE_STORAGE_CREDENTIALS is None,
                    reason='Azure blob storage credentials needed')
def test_get_images_azure1():
    arr = numpy.zeros((120, 5, 3))
    stream = io.BytesIO()
    numpy.save(stream, arr)
    stream.seek(0)

    image_type = '2D'
    image_url = 'az://blueno2/2d-array'
    data_url = 'az://blueno2/2d-array.npy'
    info = {
        'image': {
            'url': image_url,
            'type': image_type,
            'count': arr.shape[0],
        }
    }

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    image._create_images(image_type, image_url, data_url)

    urls = image.get_images(info, 1, 0)
    assert len(urls) == 1
    assert urls[0].startswith(
        'https://blueno.blob.core.windows.net/blueno2/2d-array.jpg')


@pytest.mark.skipif(env.AZURE_STORAGE_CREDENTIALS is None,
                    reason='Azure blob storage credentials needed')
def test_get_images_azure2():
    arr = numpy.zeros((12, 5, 3))
    stream = io.BytesIO()
    numpy.save(stream, arr)
    stream.seek(0)

    image_type = '3D'
    image_url = 'az://blueno/3d-array'
    data_url = 'az://blueno/3d-array.npy'
    info = {
        'image': {
            'url': image_url,
            'type': image_type,
            'count': arr.shape[0],
        }
    }

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    image._create_images(image_type, image_url, data_url)

    urls = image.get_images(info, 10, 2)
    assert len(urls) == 10


@pytest.mark.skipif(env.FILESYSTEM_STORE_ROOT is None,
                    reason='Local filesystem store must be enabled')
def test_get_images_filesystem():
    arr = numpy.zeros((12, 5, 3))
    stream = io.BytesIO()
    numpy.save(stream, arr)
    stream.seek(0)

    image_type = '3D'
    image_url = 'file://blueno/3d-array'
    data_url = 'file://blueno/3d-array.npy'
    info = {
        'image': {
            'url': image_url,
            'type': image_type,
            'count': arr.shape[0],
        }
    }

    client = storage.get_storage_client(data_url)
    client.put(data_url, stream)

    image._create_images(image_type, image_url, data_url)

    with app.test_request_context('http://www.example.com/rest/of/the/route'):
        urls = image.get_images(info, 10, 2)

    assert len(urls) == 10
    assert urls[0].startswith(
        'http://www.example.com/data/download?url=file://blueno/3d-array')
