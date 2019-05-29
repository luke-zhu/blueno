import pathlib
from blueno import PlatformClient

API_SERVER = ''
EMAIL = ''
PASSWORD = ''
DATASET = ''

if __name__ == '__main__':
    client = PlatformClient(API_SERVER, EMAIL, PASSWORD)
    print(f'Creating dataset: {DATASET}')
    client.create_dataset(DATASET,
                          description='First version of the multiphase'
                                      ' segmentation data')

    root_dir = pathlib.Path(
        '/research/rih-cs/datasets/elvo-multiphase/segmentation_data')
    for dirpath in root_dir.iterdir():
        for filepath in dirpath.iterdir():
            if filepath.name.endswith('.jpg'):
                sample_name = filepath.name[:-len('.jpg')]
                label = sample_name[0]  # either 'P' or 'N'
                url = f'gs://elvo-platform/multiphase/processed' \
                    f'/{DATASET}/{filepath.name}'
                print(
                    f'Uploading sample {sample_name} with label {label} to'
                    f' {url} from {str(filepath)}')
                with open(filepath, 'rb') as f:
                    client.create_sample(sample_name,
                                         DATASET,
                                         data_url=url,
                                         data_content=f,
                                         label=label)
