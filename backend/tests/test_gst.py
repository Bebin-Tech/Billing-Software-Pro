from decimal import Decimal
import pytest
from app.services.gst import calculate


@pytest.mark.parametrize('rate,total', [('0','1000.00'),('5','1050.00'),('12','1120.00'),('18','1180.00'),('28','1280.00')])
def test_rates(rate,total):
    result=calculate([{'price':'1000','quantity':'1','gst_rate':rate}], '27','27')
    assert result['total']==total
    assert Decimal(result['items'][0]['cgst'])+Decimal(result['items'][0]['sgst'])==Decimal(result['tax'])


def test_interstate():
    row=calculate([{'price':'1000','quantity':'1','gst_rate':'18'}],'27','29')['items'][0]
    assert row['igst']=='180.00' and row['cgst']=='0'


def test_inclusive_discount_and_mixed():
    result=calculate([{'price':'1180','quantity':'1','gst_rate':'18','inclusive':True,'discount_percent':'10'}, {'price':'200','quantity':'2','gst_rate':'5'}],'27','27')
    assert result['taxable']=='1300.00'
    assert result['total']=='1482.00'


def test_rounding_and_rcm():
    result=calculate([{'price':'0.05','quantity':'1','gst_rate':'18'}],'27','27')
    assert result['tax']=='0.01'
    assert result['items'][0]['cgst']=='0.01' and result['items'][0]['sgst']=='0.00'
    rcm=calculate([{'price':'1000','quantity':'1','gst_rate':'18'}],'27','29',reverse_charge=True)
    assert rcm['total']=='1000.00' and rcm['tax']=='180.00'


def test_sez_is_interstate_even_same_state():
    assert calculate([{'price':'1000','quantity':'1','gst_rate':'18'}],'27','27',rule='sez')['interstate']


def test_storage_overflow_rejected_before_posting():
    with pytest.raises(ValueError,match='storage capacity'):
        calculate([{'price':'9999999999999999.99','quantity':'2','gst_rate':'18'}],'27','27')
