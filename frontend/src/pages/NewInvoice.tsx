import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight,Plus,X } from 'lucide-react';
import React,{ useState, useEffect } from 'react';
import { NavLink,useNavigate,useParams } from 'react-router-dom';
import { api } from './../api/client';

import { RecordData,money,queryClient,today } from './../app/runtime';
import { ErrorBox,Field } from './../components/ui';

export default function NewInvoice(){
  const {id}=useParams();
  const existing=useQuery({queryKey:['invoice-edit',id],queryFn:()=>api.get(`/invoices/${id}`).then(r=>r.data),enabled:Boolean(id)});
  const customers=useQuery({queryKey:['customers-options'],queryFn:()=>api.get('/customers',{params:{page_size:100}}).then(r=>r.data.items)});
  const products=useQuery({queryKey:['products-options'],queryFn:()=>api.get('/products',{params:{page_size:100}}).then(r=>r.data.items)});
  const [lines,setLines]=useState([{product_id:'',quantity:'1',discount_percent:'0',inclusive:false}]),[error,setError]=useState<unknown>(),[busy,setBusy]=useState(false);const navigate=useNavigate();
  useEffect(()=>{if(existing.data)setLines(existing.data.items.map((r:RecordData)=>({product_id:String(r.product_id),quantity:r.quantity,discount_percent:r.discount_percent||'0',inclusive:r.inclusive})));},[existing.data]);
  async function save(e:React.FormEvent<HTMLFormElement>){
    e.preventDefault();setBusy(true);setError(undefined);
    const values=Object.fromEntries(new FormData(e.currentTarget));
    try{
      const r=await api.request({method:id?'PUT':'POST',url:id?`/invoices/${id}/draft`:'/invoices/drafts',
        data:{...values,customer_id:Number(values.customer_id),reverse_charge:values.reverse_charge==='on',
          items:lines.map(l=>({...l,product_id:Number(l.product_id)}))}});
      queryClient.invalidateQueries();navigate(`/invoices/${r.data.id}`);
    }catch(e){setError(e);}finally{setBusy(false);}
  }
  if(id&&existing.isPending)return <p className="loading">Loading draft…</p>;
  if(existing.error)return <ErrorBox error={existing.error}/>;
  if(existing.data&&existing.data.status!=='draft')return <p className="error">Only draft invoices can be edited.</p>;
  return <><div className="page-heading"><div><span className="eyebrow">SALES / NEW INVOICE</span><h1>Make good work official.</h1><p>Save a draft, review the server-calculated totals, then issue.</p></div></div><form key={existing.data?.id||'new'} onSubmit={save}><section className="panel padded"><h2>Invoice details</h2><div className="form-grid"><Field label="Customer"><select name="customer_id" required defaultValue={existing.data?.customer_id||''}><option value="">Select customer</option>{customers.data?.map((r:RecordData)=><option key={r.id} value={r.id}>{r.name}</option>)}</select></Field><Field label="Invoice date"><input type="date" name="invoice_date" defaultValue={existing.data?.invoice_date||today()} required/></Field><Field label="Due date"><input type="date" name="due_date" defaultValue={existing.data?.due_date||today()} required/></Field><Field label="Confirmed place of supply — GST state code"><input name="supply_state" defaultValue={existing.data?.supply_state||''} pattern="[0-9]{2}" required placeholder="27"/></Field><Field label="Supply rule"><select name="supply_rule" defaultValue={existing.data?.supply_rule||'domestic_standard'}><option value="domestic_standard">Standard domestic supply</option><option value="sez">SEZ supply (interstate, taxable)</option></select></Field></div><label className="checkbox"><input name="reverse_charge" type="checkbox" defaultChecked={existing.data?.reverse_charge||false}/>Reverse charge applies</label><p className="muted">Confirm place-of-supply and tax applicability with your accountant. Exports, zero-rated SEZ and special rules are not supported in this version.</p></section><section className="panel padded"><h2>Line items</h2>{lines.map((line,i)=><div className="invoice-line" key={i}><Field label="Service"><select value={line.product_id} required onChange={e=>setLines(lines.map((l,n)=>n===i?{...l,product_id:e.target.value}:l))}><option value="">Select service</option>{products.data?.filter((r:RecordData)=>r.is_service&&r.active).map((r:RecordData)=><option key={r.id} value={r.id}>{r.name} · {money(r.price)} · {r.gst_rate}%</option>)}</select></Field>{(['quantity','discount_percent'] as const).map(key=><Field label={key==='quantity'?'Quantity':'Discount %'} key={key}><input type="number" min={key==='quantity'?0.0001:0} max={key==='discount_percent'?100:1000000} step="0.0001" required value={line[key]} onChange={e=>setLines(lines.map((l,n)=>n===i?{...l,[key]:e.target.value}:l))}/></Field>)}<label className="checkbox"><input type="checkbox" checked={line.inclusive} onChange={e=>setLines(lines.map((l,n)=>n===i?{...l,inclusive:e.target.checked}:l))}/>Inclusive</label><button type="button" aria-label="Remove line" disabled={lines.length===1} onClick={()=>setLines(lines.filter((_,n)=>n!==i))}><X size={16}/></button></div>)}<button type="button" onClick={()=>setLines([...lines,{product_id:'',quantity:'1',discount_percent:'0',inclusive:false}])}><Plus size={16}/>Add line</button></section>{(customers.error||products.error)&&<ErrorBox error={customers.error||products.error}/>} {error!=null&&<ErrorBox error={error}/>}<div className="form-actions"><NavLink to="/invoices">Cancel</NavLink><button className="primary" disabled={busy}>{busy?'Calculating & saving…':'Save draft & review'}<ArrowUpRight size={17}/></button></div></form></>;
}
