import app.main as application


def test_unconfigured_mysql_reports_liveness_but_blocks_business_routes(client,monkeypatch):
    monkeypatch.setattr(application,'engine',None)
    health=client.get('/health')
    assert health.status_code==200 and health.json()['runtime']=='fastapi'
    assert client.get('/health/ready').status_code==503
    response=client.get('/api/v1/invoices')
    assert response.status_code==503 and 'MySQL' in response.json()['detail']
    assert response.headers['cache-control']=='no-store'
