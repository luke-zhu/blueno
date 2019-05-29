import flask

from app import app


def test_all_simple(test_user):
    dataset = 'datasets_test::test_all_simple-dataset'

    with app.app_context():
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

        res = client.get('/datasets/', headers=headers)
        assert res.status_code == 200
        assert res.json['datasets'] == []

        # 1st create request should work
        res = client.put(f'/datasets/{dataset}', headers=headers)
        assert res.status_code == 200

        res = client.get('/datasets/', headers=headers)
        assert res.status_code == 200
        assert len(res.json['datasets']) == 1

        # 2nd create request should fail
        res = client.put(f'/datasets/{dataset}', headers=headers)
        assert res.status_code == 409

        res = client.get('/datasets/', headers=headers)
        assert res.status_code == 200
        assert len(res.json['datasets']) == 1

        # 1st delete request should work
        res = client.delete(f'/datasets/{dataset}', headers=headers)
        assert res.status_code == 200

        res = client.get('/datasets/', headers=headers)
        assert res.status_code == 200
        assert len(res.json['datasets']) == 0

        # 2nd delete request should fail
        res = client.delete(f'/datasets/{dataset}', headers=headers)
        assert res.status_code == 404

        res = client.get('/datasets/', headers=headers)
        assert res.status_code == 200
        assert len(res.json['datasets']) == 0
