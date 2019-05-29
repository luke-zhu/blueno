"""
Image processing code.

"""
import io
import json
from typing import Dict

import numpy
import psycopg2
import redis
import rq
from PIL import Image

from app import storage, env

queue = rq.Queue(connection=redis.Redis(host=env.REDIS_HOST))


def _create_rgb_image(arr) -> Image.Image:
    normalized = ((arr - arr.min()) / (arr.max() - arr.min()))
    as_rgb = (255 * normalized).astype(numpy.uint8)
    return Image.fromarray(as_rgb)


def _upload_to_uri(img: Image.Image, uri: str):
    """
    Uploads the image to the storage URI.

    :param img: a PIL.Image.Image object
    :param uri: the URI to save the image to (should start with gs://,
        az://, etc.)
    """
    stream = io.BytesIO()
    img.save(stream, format='jpeg')
    stream.seek(0)

    storage_client = storage.get_storage_client(uri)
    storage_client.put(uri, stream)


def _create_image_from_npy(arr, full_url):
    if arr.ndim == 2:
        img = _create_rgb_image(arr)
        _upload_to_uri(img, full_url)
    elif arr.ndim == 3:
        if arr.shape[2] == 1:
            arr_squeezed = arr.squeeze(axis=2)
            img = _create_rgb_image(arr_squeezed)
            _upload_to_uri(img, full_url)
        elif arr.shape[2] == 3:
            img = _create_rgb_image(arr)
            _upload_to_uri(img, full_url)
        else:
            raise ValueError(
                f"3D array must have 1 or 3 channels, found {arr.shape}")
    else:
        raise ValueError(
            f"Array is not 2D or 3D: dimension={arr.ndim}")


def _create_images(image_type: str,
                   image_url_prefix: str,
                   data_url: str) -> int:
    """
    Creates images from the given info.

    :param image_type: either '2D' or '3D'
    :param image_url_prefix: the internal url prefix of the image.
        This should not end with '/' or a file extension.
    :param data_url: the internal URL of the data
    :return: the
    """
    # _create_images and get_images should have mirrored structures
    storage_client = storage.get_storage_client(data_url)
    data_stream = storage_client.get(data_url)

    if image_type == '2D':
        if data_url.lower().endswith('.npy'):
            arr = numpy.load(data_stream)
            _create_image_from_npy(arr, f'{image_url_prefix}.jpg')
            return 1
        elif data_url.lower().endswith('.tfrecord'):
            raise NotImplementedError()
        else:
            # This will fail if the format is unsupported
            img = Image.open(data_stream)
            _upload_to_uri(img, f'{image_url_prefix}.jpg')
        return 1
    elif image_type == '3D':
        if data_url.lower().endswith('.npy'):
            # Create an image per each slice
            # TODO: This assumes the data is column first not column last.
            #  Document this somewhere
            arr = numpy.load(data_stream)
            for i in range(arr.shape[0]):
                img = _create_rgb_image(arr[i])
                _upload_to_uri(img, f'{image_url_prefix}-{i}.jpg')
            return arr.shape[0]
        else:
            raise ValueError(f'Cannot create images for'
                             f' image_type={image_type} data_url={data_url}')
    elif image_type == 'CT':
        raise NotImplementedError(f'Image type {image_type} not supported yet')
    else:
        raise ValueError(f'Image type {image_type} not supported')


def create_images(sample_id: int):
    with psycopg2.connect(**env.POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT info
                FROM samples
                WHERE id = %s;
                """,
                (sample_id,)
            )
            result = cur.fetchone()
            assert result is not None

        info = result[0]
        image_type = info['image']['type']
        image_url_prefix = info['image']['url']
        data_url = info['data']['url']
        try:
            count = _create_images(image_type, image_url_prefix, data_url)
        except Exception as e:
            info['image']['status'] = 'FAILED'
            info['image']['reason'] = str(e)
        else:
            info['image']['status'] = 'CREATED'
            info['image']['count'] = count
        finally:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE samples
                    SET info = %s
                    WHERE id = %s;
                    """,
                    (json.dumps(info), sample_id,)
                )
            conn.commit()


def enqueue_create_images(sample_id: int) -> rq.job.Job:
    """
    Creates images for the data in data_url on a Redis Queue worker.
    :param sample_id: the database ID of the sample
    :return: a redis queue Job
    """
    return queue.enqueue(create_images, sample_id)


def get_images(info, limit, offset):
    if 'image' in info:
        image_info: Dict = info['image']
        image_url_prefix = image_info['url']
        image_type = image_info['type']
        storage_client = storage.get_storage_client(image_url_prefix)
        if image_type == '2D':
            images = [
                storage_client.get_signed_url(f'{image_url_prefix}.jpg')
            ]
        elif image_type == '3D':
            if limit is None:
                upper_bound = image_info['count']
            else:
                upper_bound = min(image_info['count'], offset + limit)
            images = [
                storage_client.get_signed_url(f'{image_url_prefix}-{i}.jpg')
                for i in range(offset, upper_bound)
            ]
        else:
            raise ValueError(f"Unsupported image_type '{image_type}'")
    elif any([info['data']['url'].lower().endswith(ext)
              for ext in ('.png', '.jpg', '.jpeg')]):
        storage_client = storage.get_storage_client(info['data']['url'])
        public_image_url = storage_client.get_signed_url(info['data']['url'])
        images = [public_image_url]
    else:
        images = []
    return images
