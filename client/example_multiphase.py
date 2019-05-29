import os
import time
from typing import List

from blueno import PlatformClient

API_SERVER = ''
EMAIL = ''
PASSWORD = ''

DATASET_NAME = f'multiphase'
SOURCE_PREFIX = '/research/rih-cs/datasets/elvo-multiphase/v1.0'
DATA_PREFIX = f'az://ml-platform/{DATASET_NAME}'


def load():
    client = PlatformClient(API_SERVER, EMAIL, PASSWORD)

    client.create_dataset(DATASET_NAME,
                          description="Raw multiphase ELVO scans in NPZ form.")

    dir: str
    files: List[str]
    for dir, _, files in os.walk(
            '/research/rih-cs/datasets/elvo-multiphase/v1.0'):
        for file in files:
            if file.endswith('.npz'):
                sample_name = file.split('.')[0]
                label = 'positive' if file.startswith('P') else 'negative'
                data_url = f'{DATA_PREFIX}/{file}'
                print(f"Registering sample={sample_name} with"
                      f" label={label} and url={data_url}", flush=True)
                start = time.time()
                success = client.register_sample(
                    sample_name,
                    DATASET_NAME,
                    data_url=data_url,
                    image_type='3D',
                    label=label,
                )
                end = time.time()
                if success:
                    print(f"Registered {file} in {end - start} seconds")
                else:
                    print(f"Found {file} exists in {end - start} seconds")


if __name__ == '__main__':
    load()
