import { useQuery } from '@tanstack/react-query';
import { Building2,ChevronRight,LogOut,Menu,ShieldCheck } from 'lucide-react';
import { useEffect,useState } from 'react';
import { NavLink,Route,Routes } from 'react-router-dom';
import { api,setCompany,setToken } from './../api/client';

import Auth from '../pages/Auth';
import CompanySettings from '../pages/CompanySettings';
import Dashboard from '../pages/Dashboard';
import InvoiceDetail from '../pages/InvoiceDetail';
import NewInvoice from '../pages/NewInvoice';
import Records from '../pages/Records';
import Team from '../pages/Team';
import Sessions from '../pages/Sessions';
import Reports from '../pages/Reports';
import { Empty,ErrorBox } from './../components/ui';
import { RecordData,nav,queryClient } from './runtime';
let bootstrap: Promise<boolean> | undefined;

export default function App(){
  const [auth,setAuth]=useState(false),[checking,setChecking]=useState(true),[collapsed,setCollapsed]=useState(false),[version,setVersion]=useState(0),[logoutError,setLogoutError]=useState<unknown>();
  const companies=useQuery({queryKey:['companies',auth],queryFn:()=>api.get('/companies').then(r=>r.data),enabled:auth});
  useEffect(()=>{bootstrap ??= api.post('/auth/refresh').then(r=>{setToken(r.data.access_token);return true;}).catch(()=>false);bootstrap.then(ok=>{setAuth(ok);setChecking(false);});},[]);
  useEffect(()=>{if(companies.data?.length){const selected=companies.data.find((c:RecordData)=>String(c.id)===sessionStorage.getItem('company_id'))||companies.data[0];setCompany(selected.id);setVersion(v=>v+1);}},[companies.data]);
  if(checking)return <div className="loading">Opening your workspace…</div>;
  if(!auth)return <Auth done={()=>setAuth(true)}/>;
  if(companies.isPending)return <div className="loading">Loading companies…</div>;
  if(companies.error)return <ErrorBox error={companies.error}/>;
  if(!companies.data?.length)return <Empty label="No company access" detail="Ask your administrator to add you to a company."/>;
  const company=companies.data.find((c:RecordData)=>String(c.id)===sessionStorage.getItem('company_id'))||companies.data[0];
  const allowedNav=nav.filter(n=>!['/users','/settings','/audit-logs'].includes(n.to)||company.role==='company_admin');
  return <div className={`app ${collapsed?'collapsed':''}`}><aside className="sidebar"><NavLink className="wordmark" to="/"><span className="logo">G</span><span>GST Billing <b>Pro</b></span></NavLink><div className="workspace-label">BUSINESS WORKSPACE</div><nav>{allowedNav.map(n=><NavLink to={n.to} key={n.to} end={n.to==='/'}><n.icon size={19}/><span>{n.label}</span></NavLink>)}</nav><div className="sidebar-bottom"><div className="secure-card"><ShieldCheck size={20}/><span><b>Your business. Protected.</b><small>Company-scoped access</small></span></div><div className="company-avatar">{company.name[0]}</div><div className="company-caption"><b>{company.name}</b><small>{company.role.replaceAll('_',' ')}</small></div></div></aside><div className="workspace"><header className="topbar"><div className="topbar-left"><button className="icon-button" aria-label="Toggle sidebar" onClick={()=>setCollapsed(!collapsed)}><Menu size={20}/></button><span className="breadcrumb">Workspace <ChevronRight size={13}/> {company.name}</span></div><div className="topbar-right"><Building2 size={17}/><select aria-label="Select company" value={company.id} onChange={e=>{setCompany(Number(e.target.value));queryClient.removeQueries({predicate:q=>q.queryKey[0]!=='companies'});setVersion(v=>v+1);}}>{companies.data.map((c:RecordData)=><option key={c.id} value={c.id}>{c.name}</option>)}</select><button className="icon-button" aria-label="Sign out" onClick={async()=>{try{await api.post('/auth/logout');setToken('');setAuth(false);queryClient.clear();}catch(e){setLogoutError(e);}}}><LogOut size={18}/></button></div></header><main className="content" key={version}>{logoutError!=null&&<ErrorBox error={logoutError}/>}<Routes><Route path="/" element={<Dashboard/>}/>{['customers','products','invoices','payments','audit-logs'].map(k=><Route path={`/${k}`} key={k} element={<Records kind={k}/>}/>)}<Route path="/invoices/new" element={<NewInvoice/>}/><Route path="/invoices/:id/edit" element={<NewInvoice/>}/><Route path="/invoices/:id" element={<InvoiceDetail/>}/><Route path="/settings" element={<CompanySettings companies={companies.data}/>}/><Route path="/users" element={<Team/>}/><Route path="/sessions" element={<Sessions/>}/><Route path="/reports" element={<Reports/>}/><Route path="*" element={<Empty label="Page not found"/>}/></Routes><footer>GST Billing Pro <span>Thoughtful tools for growing businesses.</span></footer></main></div></div>;
}
