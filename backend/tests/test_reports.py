from io import BytesIO
from openpyxl import load_workbook
from conftest import account
from test_workflow import draft


def test_reports_exclude_cancelled_and_export_actual_totals(client):
    headers=account(client)
    invoice,_=draft(client,headers)
    client.post(f"/api/v1/invoices/{invoice['id']}/issue",headers=headers)
    params={'start':'2026-11-01','end':'2026-11-30'}
    report=client.get('/api/v1/reports/sales',headers=headers,params=params)
    assert report.status_code==200 and report.json()['total']=='1180.00'
    gst=client.get('/api/v1/reports/gst-preparation',headers=headers,params=params).json()
    assert 'NOT FILED' in gst['label'] and gst['totals']['cgst']=='90.00'
    xlsx=client.get('/api/v1/reports/sales.xlsx',headers=headers,params=params)
    assert xlsx.status_code==200
    book=load_workbook(BytesIO(xlsx.content));assert book.active['F2'].value==1180
    client.post(f"/api/v1/invoices/{invoice['id']}/cancel",headers=headers,json={'reason':'QA cancellation requested'})
    assert client.get('/api/v1/reports/sales',headers=headers,params=params).json()['total']=='0'
