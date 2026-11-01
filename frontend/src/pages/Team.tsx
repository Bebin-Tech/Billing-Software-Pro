import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from './../api/client';

import { RecordData } from './../app/runtime';
import { ErrorBox,Field } from './../components/ui';

export default function Team(){const q=useQuery({queryKey:['users'],queryFn:()=>api.get('/users').then(r=>r.data)});const [error,setError]=useState<unknown>(),[busy,setBusy]=useState(false);return <><div className="page-heading"><div><span className="eyebrow">WORKSPACE</span><h1>Your team</h1><p>Give the right people the right access.</p></div></div><section className="panel padded"><h2>Add an existing account</h2><form onSubmit={async e=>{e.preventDefault();setBusy(true);try{await api.post('/users',Object.fromEntries(new FormData(e.currentTarget)));await q.refetch();}catch(e){setError(e);}finally{setBusy(false);}}}><div className="form-grid"><Field label="Email address"><input name="email" type="email" required/></Field><Field label="Role"><select name="role">{['viewer','billing_staff','inventory_manager','accountant','company_admin'].map(r=><option key={r}>{r}</option>)}</select></Field></div><button className="primary" disabled={busy}>Add member</button></form>{error!=null&&<ErrorBox error={error}/>}</section><section className="panel padded">{q.error?<ErrorBox error={q.error}/>:q.data?.map((r:RecordData)=><div className="team-member" key={r.id}><b>{r.name}</b><span>{r.email}</span><span className="badge">{r.role}</span></div>)}</section></>;}
