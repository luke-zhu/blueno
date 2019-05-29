from app import app


def test_login(test_user):
    client = app.test_client()
    res = client.post('/login', json={
        'email': test_user[0],
        'password': test_user[1],
    })
    assert res.status_code == 200, f'response: {res.json}'
