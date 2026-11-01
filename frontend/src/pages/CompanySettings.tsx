import { useQueryClient } from '@tanstack/react-query';
import { CheckCircle2 } from 'lucide-react';
import { useState } from 'react';
import { api } from './../api/client';

import { RecordData } from './../app/runtime';
import { ErrorBox,Field } from './../components/ui';

export default function CompanySettings({companies}:{companies:RecordData[]}){
  const current=companies.find(c=>String(c.id)===sessionStorage.getItem('company_id'))||companies[0];const [error,setError]=useState<unknown>(),[saved,setSaved]=useState(false),[busy,setBusy]=useState(false);const client=useQueryClient();
  return <><div className="page-heading"><div><span className="eyebrow">WORKSPACE</span><h1>Company settings</h1><p>The details that make your business yours.</p></div></div><section className="panel padded"><form key={current.id} onSubmit={async e=>{e.preventDefault();setBusy(true);setSaved(false);try{await api.put(`/companies/${current.id}`,Object.fromEntries(new FormData(e.currentTarget)));await client.invalidateQueries();setSaved(true);}catch(e){setError(e);}finally{setBusy(false);}}}><div className="form-grid">{[['name','Legal business name'],['state_code','GST state code'],['gstin','GSTIN'],['address','Business address'],['invoice_prefix','Invoice prefix']].map(([name,label])=><Field key={name} label={label}><input name={name} defaultValue={current[name]||''} required={name!=='gstin'&&name!=='address'}/></Field>)}</div>{error!=null&&<ErrorBox error={error}/>} {saved&&<p className="success"><CheckCircle2 size={16}/>Company details saved.</p>}<button className="primary" disabled={busy}>Save changes</button></form></section></>;
}
