from conftest import account


def test_session_revocation_and_isolation(client):
    first=account(client)
    sessions=client.get('/api/v1/auth/sessions',headers=first).json()
    assert sessions and 'token_hash' not in sessions[0]
    second=account(client,'other@example.com')
    path=f"/api/v1/auth/sessions/{sessions[0]['id']}/revoke"
    assert client.post(path,headers=second).status_code==404
    assert client.post(path,headers=first).status_code==204
    assert client.get('/api/v1/companies',headers=first).status_code==401
