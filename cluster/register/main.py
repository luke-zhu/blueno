"""
This script registers a tensorflow dataset in the blueno database and
creates JPG images of each sample.

Environment variables:
BLUENO_SERVER: the host_url of the server
    (ex. http://blueno-server OR http://35.35.35.35)
FILESYSTEM_STORE_ROOT: the path where the FILESYSTEM_STORE_ROOT is mounted
    - the URL file://data will be translated to <FILESYSTEM_STORE_ROOT>/data
"""
import argparse
import asyncio
import json
import logging
import os
import pathlib
import shutil
import time
from typing import Dict

import numpy
import tensorflow
import tensorflow_datasets

import blueno

SERVER_HOST = os.environ['BLUENO_SERVER']
FILESYSTEM_STORE_ROOT = os.environ['FILESYSTEM_STORE_ROOT']


async def prepare_dataset(builder_name: str, email: str, password: str):
    """
    Downloads an registers a dataset in the platform.

    Data is saved to 'file://data/' and images to 'file://images/'. Samples
    are registered in the blueno db with this info.

    :param builder_name: the name of a tensorflow dataset (ex. imagenet2012)
    :param email: the email of a registered user
    :param password: the password of a registered user
    """
    builder: tensorflow_datasets.core.DatasetBuilder
    builder = tensorflow_datasets.builder(builder_name)
    download_dir = pathlib.Path(FILESYSTEM_STORE_ROOT) / 'tensorflow_datasets'

    # TODO: Check whether there is enough disk space to download the dataset
    #  beforehand.
    logging.info(f'downloading dataset {builder_name} to {download_dir}')
    builder.download_and_prepare(download_dir=download_dir)
    d = tensorflow_datasets.as_numpy(builder.as_dataset(shuffle_files=False))

    client = blueno.PlatformClient(SERVER_HOST, email, password)

    info = json.loads(builder.info.as_json)
    client.create_dataset(builder_name, info=info)

    tasks = []
    for split_name, dataset in d.items():
        for i, sample in enumerate(dataset):
            t = loop.create_task(
                register_sample(client, builder_name, sample, split_name, i))
            tasks.append(t)
            # Limit concurrency
            two_gb = 2 * 10 ** 6
            max_conns = 1000
            est_max_arrays_in_mem = two_gb / sample['image'].nbytes
            if len(tasks) >= min(max_conns, 0.75 * est_max_arrays_in_mem):
                for t in tasks:
                    await t
                    t.result()
                tasks = []

    shutil.rmtree(download_dir / builder_name, ignore_errors=True)


def decode(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, bytes):
        return value.decode()
    elif numpy.isscalar(value):
        return value.item()
    elif isinstance(value, numpy.ndarray):
        return value.tolist()
    elif isinstance(value, dict):
        return {k: decode(v) for k, v in value.items()}
    raise TypeError(f"Cannot decode value of type {type(value)}")


async def register_sample(client: blueno.PlatformClient,
                          dataset_name: str,
                          sample: Dict,
                          split_name: str,
                          sample_no: int):
    """
    Register the sample under file://data/{dataset_name}. The name
    of the sample is derived from the sample info if possible.
    """
    start = time.time()

    for key in sample:
        if key in ('filename', 'file_name',
                   'image/filename', 'image/file_name'):
            sample_name = decode(sample[key]).replace('/', '-')
            break
    else:
        sample_name = f'{split_name}-{sample_no}'

    logging.info(f'registering sample {sample_name}')

    arr = sample['image']
    if 'label' in sample:
        label = decode(sample['label'])
    else:
        label = None

    feature_info = {}
    for key in sample:
        if key != 'image':
            try:
                feature_info[key] = decode(sample[key])
            except TypeError as e:
                logging.info(f"Failed to decode feature '{key}': {e}")

    rel_sample_path = f'data/{dataset_name}/{sample_name}.npy'
    abs_sample_path = pathlib.Path(FILESYSTEM_STORE_ROOT) / rel_sample_path
    abs_sample_path.parent.mkdir(parents=True, exist_ok=True)
    numpy.save(abs_sample_path, arr)

    client.register_sample(
        sample_name,
        dataset_name,
        data_url=f'file://{rel_sample_path}',
        image_type='2D',
        label=label,
        split=split_name,
        other_info={
            'feature': feature_info,
        },
    )

    end = time.time()
    logging.info(f'registered sample {sample_name} in {end - start} seconds')


if __name__ == '__main__':
    # This ends up printing logs because tensorflow is doing something to
    # the root logger.
    logging.getLogger().setLevel(logging.INFO)

    tensorflow.enable_eager_execution()

    parser = argparse.ArgumentParser()
    parser.add_argument('builder')
    # TODO: email and password are shown by `kubectl describe`. Properly
    #  change this so the password is never shown.
    parser.add_argument('email')
    parser.add_argument('password')
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        prepare_dataset(args.builder, args.email, args.password))
