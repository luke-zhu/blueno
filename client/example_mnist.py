import os
import time
from typing import List

from blueno import PlatformClient

API_SERVER = ''
EMAIL = ''
PASSWORD = ''


def register_mnist_az():
    client = PlatformClient(API_SERVER, EMAIL, PASSWORD)
    dataset_name = f'mnist-az'

    client.create_dataset(dataset_name,
                          description="MNIST on Azure in PNG form.")

    dir: str
    files: List[str]
    for dir, _, files in os.walk('mnist_png'):
        for file in files:
            if file.endswith('.png'):
                label = dir.split('/')[-1]
                split = dir.split('/')[1]
                start = time.time()
                sample_name = f"{file.split('.')[0]}-{split}"
                new_dir = dir.replace('mnist_png', 'data')
                data_url = f'az://ml-platform/{new_dir}/{file}'
                print(
                    f"Registering {sample_name} with label {label},"
                    f" split {split}, and data_url {data_url}",
                    flush=True)
                ret = client.register_sample(
                    sample_name,
                    dataset_name,
                    data_url=data_url,
                    validate=False,
                    label=label,
                    split=split,
                )
                end = time.time()
                if ret:
                    print(f"REGISTERED: processed {file}"
                          f" in {end - start} seconds")
                else:
                    print(f"ALREADY EXISTS: processed {file}"
                          f" in {end - start} seconds")


if __name__ == '__main__':
    register_mnist_az()
