import os
import time
import threading

import numpy

from blueno import PlatformClient

API_SERVER = ''
EMAIL = ''
PASSWORD = ''
DATASET_BATCHES = 'cifar-10-batches'
DATASET_INDIVIDUAL = 'cifar-10-npy'


def unpickle(file):
    import pickle
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict


def load_batches():
    client = PlatformClient(API_SERVER, EMAIL, PASSWORD)
    client.create_dataset(
        DATASET_BATCHES,
        description="CIFAR-10 batches from"
                    " http://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
    )

    training_files = ['data_batch_1', 'data_batch_2', 'data_batch_3',
                      'data_batch_4',
                      'data_batch_5']
    test_files = ['test_batch']

    for filename in training_files:
        filepath = os.path.join('cifar-10-batches-py/', filename)
        print('Loading training file', filepath)
        start = time.time()
        split_class = 'training'
        with open(filepath, 'rb') as f:
            client.create_sample(
                filename, DATASET_BATCHES,
                data_url=f'gs://elvo-platform/test/platform/data'
                f'/{DATASET_BATCHES}/{filename}.pkl',
                data_content=f,
                split=split_class
            )
        end = time.time()
        print(f'Took {end - start} seconds', flush=True)

    for filename in test_files:
        filepath = os.path.join('cifar-10-batches-py/', filename)
        print('Loading test file', filepath)
        start = time.time()
        split_class = 'test'
        with open(filepath, 'rb') as f:
            client.create_sample(
                filename, DATASET_BATCHES,
                data_url=f'gs://elvo-platform/test/platform/data'
                f'/{DATASET_BATCHES}/{filename}.pkl',
                data_content=f,
                split=split_class
            )
        end = time.time()
        print(f'Took {end - start} seconds', flush=True)


def _load_individual(client, filename, split_class):
    filepath = os.path.join('cifar-10-batches-py/', filename)

    data_dict = unpickle(filepath)
    data = data_dict[b'data']
    labels = data_dict[b'labels']

    for i in range(10000):
        sample_name = f'{filename}-{i}'

        print(f'Loading {split_class} sample {sample_name}')
        start = time.time()

        arr: numpy.ndarray = data[i]
        arr = arr.reshape((3, 32, 32)).transpose((1, 2, 0))
        label: int = labels[i]
        print('Array shape:', arr.shape)

        retry_count = 0
        while True:
            try:
                client.create_sample(
                    sample_name,
                    DATASET_INDIVIDUAL,
                    data_url=f'gs://elvo-platform/test/platform/data'
                    f'/{DATASET_INDIVIDUAL}/{sample_name}.npy',
                    data_content=arr.dumps(),
                    image_type='2D',
                    label=label,
                    split=split_class
                )
                break
            except Exception:
                time.sleep(2 ** retry_count)
                retry_count += 1
                print(f'Retry #{retry_count}')

        end = time.time()
        print(f'Took {end - start} seconds', flush=True)


def load_individual():
    client = PlatformClient(API_SERVER, EMAIL, PASSWORD)
    client.create_dataset(
        DATASET_INDIVIDUAL,
        description="Individual CIFAR-10 numpy arrays",
    )

    training_files = ['data_batch_1', 'data_batch_2', 'data_batch_3',
                      'data_batch_4',
                      'data_batch_5']
    test_files = ['test_batch']

    threads = []
    for filename in training_files:
        t = threading.Thread(
            target=_load_individual,
            args=(client, filename, 'training'))
        t.start()
        threads.append(t)

    for filename in test_files:
        t = threading.Thread(
            target=_load_individual,
            args=(client, filename, 'test'))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == '__main__':
    load_batches()
    load_individual()
