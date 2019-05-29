"""
An example of how to register data on GCS.
"""
import time

from blueno import PlatformClient

from google.cloud import storage

API_SERVER = ''
EMAIL = ''
PASSWORD = ''

DATASET_NAME = f'elvo-gcs'


def register():
    platform_client = PlatformClient(API_SERVER, EMAIL, PASSWORD)
    platform_client.create_dataset(
        DATASET_NAME, description="Raw singlephase ELVO scans in NPY form.")

    gcs_client = storage.Client()
    bucket = gcs_client.get_bucket('elvo-platform')
    blob: storage.Blob
    for blob in bucket.list_blobs(prefix='elvo/raw/numpy/'):
        if not blob.name.endswith('.npy'):
            continue

        filename = blob.name.split('/')[-1]
        sample_name = filename[:-len('.npy')]
        gcs_url = f'gs://{bucket.name}/{blob.name}'
        print(f"Registering sample={sample_name} with url={gcs_url}",
              flush=True)

        start = time.time()
        success = platform_client.register_sample(sample_name,
                                                  DATASET_NAME,
                                                  gcs_url,
                                                  image_type='3D')
        end = time.time()
        if success:
            print(f"Registered {sample_name} in {end - start} seconds")
        else:
            print(f"Found {sample_name} exists in {end - start} seconds")


if __name__ == '__main__':
    register()
