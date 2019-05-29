import io
import pathlib

import flask
import pytest

from app import env, app


@pytest.mark.skipif(env.FILESYSTEM_STORE_ROOT is None,
                    reason='Local filesystem store must be enabled')
def test_upload_download_object(test_user):
    client = app.test_client()
    res = client.post('/login', json={
        'email': test_user[0],
        'password': test_user[1],
    })
    assert res.status_code == 200
    access_token = res.json['access_token']
    headers = {
        'Authorization': 'Bearer {}'.format(access_token)
    }

    file_url = 'file://blueno/test_upload_object.txt'
    file_content = b'some text'
    stream = io.BytesIO(file_content)

    res = client.post(f'/data/upload?url={file_url}',
                      headers=headers,
                      data={
                          'file': (stream, file_url),
                      })
    assert res.status_code == 200
    path = pathlib.Path(
        env.FILESYSTEM_STORE_ROOT).resolve() / 'blueno/test_upload_object.txt'
    assert path.exists()
    with path.open('rb') as f:
        assert f.read() == file_content

    res: flask.Response = client.get(f'/data/download?url={file_url}',
                                     headers=headers)
    assert res.status_code == 200
    assert res.data == file_content
