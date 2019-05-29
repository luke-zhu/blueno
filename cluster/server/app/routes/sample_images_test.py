import io

import flask
import numpy
import pytest

from app import app, env


@pytest.mark.skipif(env.FILESYSTEM_STORE_ROOT is None,
                    reason='Local filesystem store must be enabled')
def test_list_sample_images(test_user):
    dataset = 'sample_images_test::test_list_sample_images-dataset'
    sample = 'sample_images_test::test_list_sample_images-sample'
    sample2 = 'sample_images_test::test_list_sample_images-sample2'
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
    data_url = f'file://blueno/{sample}.npy'
    arr = numpy.zeros((12, 5, 3))
    stream = io.BytesIO()
    numpy.save(stream, arr)
    stream.seek(0)
    res = client.post(f'/data/upload?url={data_url}',
                      headers=headers,
                      data={
                          'file': (stream, data_url)
                      })
    assert res.status_code == 200
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

    # Check list_sample_images
    res = client.get(f'/datasets/{dataset}/samples/images',
                     headers=headers)
    assert res.status_code == 200
    assert len(res.json['images']) == 1
    # We receive None since we didn't specify to make an image
    assert res.json['images'][0] is None

    # With a JPG sample
    data_url2 = f'file://blueno/{sample2}.jpg'
    stream2 = io.BytesIO(b'fake_jpg data')
    res = client.post(f'/data/upload?url={data_url2}',
                      headers=headers,
                      data={
                          'file': (stream2, data_url2)
                      })
    # Create the sample
    res = client.put(f'/datasets/{dataset}/samples/{sample2}',
                     headers=headers,
                     json={
                         'info': {
                             'data': {
                                 'url': data_url2,
                             },
                         },
                     })
    assert res.status_code == 200

    # Check list_sample_images
    res = client.get(f'/datasets/{dataset}/samples/images',
                     headers=headers)
    assert len(res.json['images']) == 2
    # We receive None since we didn't specify to make an image
    expected_url = f'http://localhost/data/download?url={data_url2}'
    assert res.json['images'][1] == expected_url

    # Delete the samples and dataset
    res = client.delete(f'/datasets/{dataset}/samples/{sample}',
                        headers=headers)
    assert res.status_code == 200
    res = client.delete(f'/datasets/{dataset}/samples/{sample2}',
                        headers=headers)
    assert res.status_code == 200
    res = client.delete(f'/datasets/{dataset}', headers=headers)
    assert res.status_code == 200


@pytest.mark.skipif(env.FILESYSTEM_STORE_ROOT is None,
                    reason='Local filesystem store must be enabled')
def test_get_sample_images(test_user):
    dataset = 'sample_images_test::test_get_sample_images-dataset'
    sample = 'sample_images_test::test_get_sample_images-sample'
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

    # Get the sample
    res = client.get(f'/datasets/{dataset}/samples/{sample}/images',
                     headers=headers)
    assert len(res.json['images']) == 1
    expected_url = f'http://localhost/data/download?url={data_url}'
    assert res.json['images'][0] == expected_url

    # Delete the sample and dataset
    res = client.delete(f'/datasets/{dataset}/samples/{sample}',
                        headers=headers)
    assert res.status_code == 200
    res = client.delete(f'/datasets/{dataset}',
                        headers=headers)
    assert res.status_code == 200
