from conftest import account


def draft(client,headers):
    customer=client.post('/api/v1/customers',headers=headers,json={'name':'Client A','state_code':'27'}).json()
    product=client.post('/api/v1/products',headers=headers,json={'name':'Consulting','sku':'CON-01','hsn':'9983','price':'1000','gst_rate':'18','is_service':True}).json()
    data={'customer_id':customer['id'],'invoice_date':'2026-11-01','due_date':'2026-11-30','supply_state':'27','items':[{'product_id':product['id'],'quantity':'1'}]}
    r=client.post('/api/v1/invoices/drafts',headers=headers,json=data)
    assert r.status_code==201,r.text
    return r.json(),data


def test_full_service_billing_workflow(client):
    headers=account(client)
    invoice,data=draft(client,headers)
    assert float(invoice['total'])==1180
    r=client.post(f"/api/v1/invoices/{invoice['id']}/issue",headers=headers)
    assert r.status_code==200 and r.json()['number']=='INV/2026-27/00001'
    assert client.put(f"/api/v1/invoices/{invoice['id']}/draft",headers=headers,json=data).status_code==409
    assert client.post(f"/api/v1/invoices/{invoice['id']}/issue",headers=headers).status_code==409
    pdf=client.get(f"/api/v1/invoices/{invoice['id']}/pdf",headers=headers)
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    payment={'invoice_id':invoice['id'],'amount':'500','method':'UPI','payment_date':'2026-11-01','idempotency_key':'unique-payment-key-12345'}
    assert client.post('/api/v1/payments',headers=headers,json=payment).status_code==201
    assert client.post('/api/v1/payments',headers=headers,json=payment).status_code==201
    summary=client.get('/api/v1/dashboard/summary',headers=headers).json()
    assert float(summary['cash_received'])==500 and float(summary['receivables'])==680
    assert float(summary['taxable_turnover'])==1000 and float(summary['output_gst'])==180
    assert client.post('/api/v1/payments',headers=headers,json={**payment,'amount':'800','idempotency_key':'another-payment-key-123'}).status_code==422
    assert client.post(f"/api/v1/invoices/{invoice['id']}/cancel",headers=headers,json={'reason':'Customer requested cancellation'}).status_code==409


def test_tenant_isolation(client):
    first=account(client)
    invoice,data=draft(client,first)
    second=account(client,'second@example.com')
    assert client.get(f"/api/v1/invoices/{invoice['id']}",headers=second).status_code==404
    assert client.post('/api/v1/invoices/drafts',headers=second,json=data).status_code==404
    forged={**first,'X-Company-ID':second['X-Company-ID']}
    assert client.get('/api/v1/customers',headers=forged).status_code==403
    assert client.get('/api/v1/invoices',headers=second).json()['total']==0


def test_refresh_rotation_reuse_and_logout(client):
    headers=account(client)
    old=client.cookies.get('refresh_token')
    r=client.post('/api/v1/auth/refresh',headers={'Origin':'http://localhost:5173'})
    assert r.status_code==200
    new=r.json()['access_token']
    client.cookies.set('refresh_token',old)
    assert client.post('/api/v1/auth/refresh',headers={'Origin':'http://localhost:5173'}).status_code==401
    assert client.get('/api/v1/companies',headers={'Authorization':f'Bearer {new}'}).status_code==401


def test_viewer_permissions(client):
    admin=account(client)
    viewer=account(client,'viewer@example.com')
    assert client.post('/api/v1/users',headers=admin,json={'email':'viewer@example.com','role':'viewer'}).status_code==201
    headers={**viewer,'X-Company-ID':admin['X-Company-ID']}
    assert client.get('/api/v1/customers',headers=headers).status_code==200
    assert client.post('/api/v1/customers',headers=headers,json={'name':'Forbidden','state_code':'27'}).status_code==403
    assert client.get('/api/v1/users',headers=headers).status_code==403


def test_unpaid_cancellation_excluded_from_dashboard(client):
    headers=account(client)
    invoice,_=draft(client,headers)
    path=f"/api/v1/invoices/{invoice['id']}"
    client.post(path+'/issue',headers=headers)
    assert client.post(path+'/cancel',headers=headers,json={'reason':'Incorrect customer selected'}).status_code==200
    assert client.get('/api/v1/dashboard/summary',headers=headers).json()['invoice_count']==0
