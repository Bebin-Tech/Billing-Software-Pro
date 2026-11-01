import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { ErrorBox, Modal } from '../components/ui';

type Session={id:number;created_at:string;expires_at:string};
export default function Sessions(){
  const query=useQuery({queryKey:['sessions'],queryFn:()=>api.get<Session[]>('/auth/sessions').then(r=>r.data)});
  const [selected,setSelected]=useState<Session|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState<unknown>();
  return <><div className="page-heading"><div><span className="eyebrow">ACCOUNT SECURITY</span><h1>Active sessions</h1><p>Review and revoke sign-ins to your account. Times are shown in UTC.</p></div></div><section className="panel padded">{query.error&&<ErrorBox error={query.error}/>} {error!=null&&<ErrorBox error={error}/>} {query.isPending?<p>Loading sessions…</p>:query.data?.map(s=><div className="team-member" key={s.id}><b>Session #{s.id}</b><span>Created {s.created_at} UTC</span><span>Expires {s.expires_at} UTC</span><button onClick={()=>setSelected(s)}>Revoke</button></div>)}</section>{selected&&<Modal title="Revoke this session?" close={()=>setSelected(null)}><p>This ends the entire sign-in session, including rotated refresh tokens. Revoking your current session will require signing in again.</p><button className="primary" disabled={busy} onClick={async()=>{setBusy(true);try{await api.post(`/auth/sessions/${selected.id}/revoke`);setSelected(null);await query.refetch();}catch(e){setError(e);}finally{setBusy(false);}}}>Revoke session</button></Modal>}</>;
}
