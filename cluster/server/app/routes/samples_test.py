import io
import pathlib

import flask
import pytest

from app import app, env


def test_all_simple(test_user):
    dataset = 'samples_test::test_all_simple-dataset'
    sample = 'samples_test::test_all_simple-sample'

    client = app.test_client()

    res: flask.Response
    # Log in and get a token
    res = client.post('/login', json={
        'email': test_user[0],
        'password': test_user[1],
    })
    assert res.status_code == 200
    access_token = res.json['access_token']
    headers = {
        'Authorization': 'Bearer {}'.format(access_token)
    }

    # Create a dataset
    res = client.put(f'/datasets/{dataset}',
                     headers=headers)
    assert res.status_code == 200

    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers)
    assert res.status_code == 200
    assert res.json['samples'] == []

    payload = {
        'info': {
            'data': {
                'url': 'gs://abcdefg/hijklmnop'
            },
        },
        'validate': False,
    }
    # First insert should work
    res = client.put(f'/datasets/{dataset}/samples/{sample}',
                     headers=headers,
                     json=payload)
    assert res.status_code == 200

    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers)
    assert res.status_code == 200
    assert len(res.json['samples']) == 1

    # 2nd insert should conflict
    res = client.put(f'/datasets/{dataset}/samples/{sample}',
                     headers=headers,
                     json=payload)
    assert res.status_code == 409

    # but the number of samples shouldn't change
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers)
    assert res.status_code == 200
    assert len(res.json['samples']) == 1

    # inserts with bad payloads should fail
    bad_payloads = [None, {}, {'abc': []}]
    for bad_payload in bad_payloads:
        res = client.put(f'/datasets/{dataset}/samples/{sample}',
                         headers=headers,
                         json=bad_payload)
        assert res.status_code == 400
        res = client.get(f'/datasets/{dataset}/samples/',
                         headers=headers)
        assert len(res.json['samples']) == 1

    # 1st delete should work
    res = client.delete(f'/datasets/{dataset}/samples/{sample}',
                        headers=headers)
    assert res.status_code == 200

    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers)
    assert res.status_code == 200
    assert len(res.json['samples']) == 0

    # 2nd delete should fail
    res = client.delete(f'/datasets/{dataset}/samples/{sample}',
                        headers=headers)
    assert res.status_code == 404

    # but the number of samples shouldn't change
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers)
    assert res.status_code == 200
    assert len(res.json['samples']) == 0

    res = client.delete(f'/datasets/{dataset}',
                        headers=headers)
    assert res.status_code == 200


def test_list_count_samples(test_user):
    dataset = 'samples_test::test_list_samples-dataset'
    sample1 = 'samples_test::test_list_samples-sample1'
    sample2 = 'samples_test::test_list_samples-sample2'

    client = app.test_client()

    res: flask.Response
    # Log in and get a token
    res = client.post('/login', json={
        'email': test_user[0],
        'password': test_user[1],
    })
    assert res.status_code == 200
    access_token = res.json['access_token']
    headers = {
        'Authorization': 'Bearer {}'.format(access_token)
    }

    # Create a dataset
    res = client.put(f'/datasets/{dataset}',
                     headers=headers)
    assert res.status_code == 200

    # Test list and count initially
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers)
    assert res.status_code == 200
    assert len(res.json['samples']) == 0
    res = client.get(f'/datasets/{dataset}/samples/count',
                     headers=headers)
    assert res.status_code == 200
    assert res.json['count'] == 0

    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers)
    assert res.status_code == 200
    assert res.json['samples'] == []
    # Insert a sample
    res = client.put(f'/datasets/{dataset}/samples/{sample1}',
                     headers=headers,
                     json={
                         'info': {
                             'data': {
                                 'url': 'gs://abcdefg/hijklmnop'
                             },
                             'label': '[0, 0, 1]',
                             'split': 'training',
                         },
                         'validate': False,
                     })
    assert res.status_code == 200
    # Insert another sample
    res = client.put(f'/datasets/{dataset}/samples/{sample2}',
                     headers=headers,
                     json={
                         'info': {
                             'data': {
                                 'url': 'gs://abcdefg/efgs'
                             },
                             'label': '[1, 0, 0]',
                             'split': 'test',
                         },
                         'validate': False,
                     })
    assert res.status_code == 200

    # Test count again
    res = client.get(f'/datasets/{dataset}/samples/count',
                     headers=headers)
    assert res.status_code == 200
    assert res.json['count'] == 2

    # Test no options
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers)
    assert res.status_code == 200
    assert len(res.json['samples']) == 2

    # Test limit
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers,
                     query_string={
                         'limit': 1,
                     })
    assert res.status_code == 200
    assert len(res.json['samples']) == 1
    assert res.json['samples'][0]['name'] == sample1

    # Test offset
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers,
                     query_string={
                         'offset': 1,
                     })
    assert res.status_code == 200
    assert len(res.json['samples']) == 1
    assert res.json['samples'][0]['name'] == sample2

    # Test prefix
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers,
                     query_string={
                         'prefix': 'samples_test::test_list_samples'
                     })
    assert res.status_code == 200
    assert len(res.json['samples']) == 2

    # Test label
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers,
                     query_string={
                         'label': '[1, 0, 0]',
                     })
    assert res.status_code == 200
    assert len(res.json['samples']) == 1
    assert res.json['samples'][0]['name'] == sample2

    # Test split
    res = client.get(f'/datasets/{dataset}/samples/',
                     headers=headers,
                     query_string={
                         'split': 'training'
                     })
    assert res.status_code == 200
    assert len(res.json['samples']) == 1
    assert res.json['samples'][0]['name'] == sample1

    # Cleanup all resources
    res = client.delete(f'/datasets/{dataset}/samples/{sample1}',
                        headers=headers)
    assert res.status_code == 200
    res = client.delete(f'/datasets/{dataset}/samples/{sample2}',
                        headers=headers)
    assert res.status_code == 200
    res = client.delete(f'/datasets/{dataset}',
                        headers=headers)
    assert res.status_code == 200

@pytest.mark.skipif(env.FILESYSTEM_STORE_ROOT is None,
                    reason='Local filesystem store must be enabled')
def test_delete_sample(test_user):
    dataset = 'samples_test::test_all_simple-dataset'
    sample = 'samples_test::test_all_simple-sample'

    client = app.test_client()

    res: flask.Response
    # Log in and get a token
    res = client.post('/login', json={
        'email': test_user[0],
        'password': test_user[1],
    })
    assert res.status_code == 200
    access_token = res.json['access_token']
    headers = {
        'Authorization': 'Bearer {}'.format(access_token)
    }
    # Create a dataset
    res = client.put(f'/datasets/{dataset}',
                     headers=headers)
    assert res.status_code == 200

    #  Insert the data
    data_url = f'file://blueno/{sample}.jpg'
    stream = io.BytesIO(b'supposedly a JPG file')
    res = client.post(f'/data/upload?url={data_url}',
                      headers=headers,
                      data={
                          'file': (stream, data_url)
                      })
    # Create the sample
    res = client.put(f'/datasets/{dataset}/samples/{sample}',
                     headers=headers,
                     json={
                         'info': {
                             'data': {
                                 'url': data_url,
                             },
                         },
                     })
    assert res.status_code == 200

    data_path = pathlib.Path(
        env.FILESYSTEM_STORE_ROOT) / f'blueno/{sample}.jpg'
    assert data_path.exists()

    # Delete the sample and dataset
    res = client.delete(f'/datasets/{dataset}/samples/{sample}',
                        headers=headers,
                        json={
                            'purge': True,
                        })
    assert res.status_code == 200
    assert not data_path.exists()

    res = client.delete(f'/datasets/{dataset}',
                        headers=headers)
    assert res.status_code == 200
