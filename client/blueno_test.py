import pytest

from blueno import PlatformClient, PlatformError

# TODO: YOUR SERVER HERE (ex. 'https://example.com' or 'http://35.35.35.35')
API_SERVER = ''
# TODO: YOUR USER EMAIL AND PASSWORD HERE
EMAIL = ''
PASSWORD = ''


@pytest.fixture(scope="module")
def client():
    PlatformClient.retry_limit = 0
    return PlatformClient(API_SERVER, EMAIL, PASSWORD)


def test_crud_datasets(client):
    dataset = 'blueno::test_crud_datasets'

    assert dataset not in {d['name'] for d in client.list_datasets()}

    assert client.create_dataset(dataset)
    assert dataset in {d['name'] for d in client.list_datasets()}
    assert not client.create_dataset(dataset)
    assert len([d['name']
                for d in client.list_datasets()
                if d['name'] == dataset]) == 1

    assert client.delete_dataset(dataset)
    assert dataset not in {d['name'] for d in client.list_datasets()}

    assert not client.delete_dataset(dataset)
    assert dataset not in {d['name'] for d in client.list_datasets()}


def test_crud_datasets_metadata(client: PlatformClient):
    dataset = 'blueno::test_crud_datasets_metadata'

    assert dataset not in {d['name'] for d in client.list_datasets()}
    client.create_dataset(dataset, description='This data is bad')

    matches = [d for d in client.list_datasets() if d['name'] == dataset]
    assert len(matches) == 1
    assert matches[0]['name'] == dataset
    assert matches[0]['info']['description'] == 'This data is bad'

    client.delete_dataset(dataset)
    matches = [d for d in client.list_datasets() if d['name'] == dataset]
    assert len(matches) == 0


def test_crud_samples(client: PlatformClient):
    dataset = 'blueno::test_crud_samples'
    samples = [
        'smaple1', 'snapple2', 'water3',
    ]

    client.create_dataset(dataset)

    # Attempt to create sample w/o data should pass
    assert client.register_sample(
        samples[0], dataset,
        data_url='file://test/crud_samples/no-data.xzx',
        validate=False,
        split='training')
    assert len(client.list_samples(dataset)) == 1
    # 2nd attempt to create w/ sample name should fail
    assert not client.register_sample(
        samples[0],
        dataset,
        data_url='file://test/crud_samples/no-data.xzx',
        validate=False,
        split='test')
    listed_samples = client.list_samples(dataset)
    assert len(listed_samples) == 1
    # 2nd attempt to create w/ sample name should not change 'info'
    assert listed_samples[0]['info']['split'] == 'training'

    # Attempt to create sample w/ data should pass
    assert client.register_sample(
        name=samples[1],
        dataset=dataset,
        data_url='file://test/crud_samples/with-data.txt',
        validate=False,
        split='training')
    listed_samples = client.list_samples(dataset)
    assert len(listed_samples) == 2

    # # Basic cleanup should work
    client.delete_sample(samples[0], dataset)
    client.delete_sample(samples[1], dataset)
    assert len(client.list_samples(dataset)) == 0

    client.delete_dataset(dataset)


def test_register_sample_validate(client: PlatformClient):
    dataset = 'blueno::test_register_sample_validate'

    client.create_dataset(dataset)
    with pytest.raises(PlatformError):
        client.register_sample(
            'test-sample',
            dataset,
            data_url='gs://elvo-platform/test/register_validate/no-data.xzx',
            validate=True,
            split='training')
    assert len(client.list_samples(dataset)) == 0
