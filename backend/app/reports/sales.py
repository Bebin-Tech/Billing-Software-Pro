from datetime import date
from decimal import Decimal
from io import BytesIO
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from app.core.database import get_db
from app.core.security import tenant
from app.models import Invoice,InvoiceLine

router=APIRouter(prefix='/api/v1/reports',tags=['Preparation reports'])


def sales_rows(db,company_id,start,end):
    if end<start: raise HTTPException(422,'End date must not precede start date')
    return list(db.scalars(select(Invoice).where(Invoice.company_id==company_id,Invoice.status=='issued',
                           Invoice.invoice_date>=start,Invoice.invoice_date<=end).order_by(Invoice.invoice_date,Invoice.id)))


@router.get('/sales')
def sales(start:date,end:date,member=Depends(tenant),db=Depends(get_db,scope='function')):
    rows=sales_rows(db,member.company_id,start,end)
    return {'label':'Sales register','start':start,'end':end,'items':[
        {'id':r.id,'number':r.number,'date':r.invoice_date,'customer':r.snapshot['customer']['name'],
         'taxable':str(r.taxable),'gst':str(r.tax),'total':str(r.total),'paid':str(r.paid),'balance':str(r.total-r.paid)} for r in rows],
        'taxable':str(sum((r.taxable for r in rows),Decimal(0))),'total':str(sum((r.total for r in rows),Decimal(0)))}


@router.get('/gst-preparation')
def gst_preparation(start:date,end:date,member=Depends(tenant),db=Depends(get_db,scope='function')):
    rows=sales_rows(db,member.company_id,start,end)
    totals={key:Decimal(0) for key in ('taxable','cgst','sgst','igst','reverse_charge_tax')}
    hsn={}
    for invoice in rows:
        for line in invoice.snapshot['items']:
            totals['taxable']+=Decimal(line['taxable'])
            if invoice.reverse_charge:
                totals['reverse_charge_tax']+=Decimal(line['tax'])
            else:
                for key in ('cgst','sgst','igst'): totals[key]+=Decimal(line[key])
            key=(line['hsn'],line['gst_rate'])
            bucket=hsn.setdefault(key,{'quantity':Decimal(0),'taxable':Decimal(0),'tax':Decimal(0)})
            bucket['quantity']+=Decimal(line['quantity']);bucket['taxable']+=Decimal(line['taxable']);bucket['tax']+=Decimal(line['tax'])
    return {'label':'OUTWARD SUPPLY PREPARATION — NOT FILED','start':start,'end':end,
            'limitations':'Service sales only. No purchases, ITC, credit/debit notes, exports, or GST portal reconciliation. Not a complete GSTR-1 or GSTR-3B.',
            'totals':{k:str(v) for k,v in totals.items()},'hsn':[{'hsn':key[0],'rate':key[1],**{k:str(v) for k,v in value.items()}} for key,value in hsn.items()]}


@router.get('/sales.xlsx')
def export_sales(start:date,end:date,member=Depends(tenant),db=Depends(get_db,scope='function')):
    rows=sales_rows(db,member.company_id,start,end)
    book=Workbook();sheet=book.active;sheet.title='Sales register'
    sheet.append(['Invoice','Date','Customer','Taxable INR','GST INR','Total INR','Paid INR','Balance INR'])
    for row in rows:
        # Force untrusted party/number text to Excel strings; never formulas.
        sheet.append([row.number,str(row.invoice_date),row.snapshot['customer']['name'],row.taxable,row.tax,row.total,row.paid,row.total-row.paid])
        for column in (1,2,3): sheet.cell(sheet.max_row,column).data_type='s'
    for cell in sheet[1]: cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='18365C')
    for row in sheet.iter_rows(min_row=2,min_col=4):
        for cell in row: cell.number_format='#,##0.00';cell.alignment=Alignment(horizontal='right')
    for col in 'ABCDEFGH': sheet.column_dimensions[col].width=24
    sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    output=BytesIO();book.save(output);output.seek(0)
    return StreamingResponse(output,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename="sales-register.xlsx"'})
