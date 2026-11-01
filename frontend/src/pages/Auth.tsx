import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowUpRight,ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { api,setToken } from './../api/client';

import AccountAction from '../features/auth/AccountAction';
import { ErrorBox,Field } from './../components/ui';

const loginSchema=z.object({email:z.string().email(),password:z.string().min(1)});
export default function Auth({done}:{done:()=>void}) {
  const [accountAction,setAccountAction]=useState(new URLSearchParams(window.location.search).get('action')||'');
  const [register,setRegister]=useState(false),[error,setError]=useState<unknown>(),[busy,setBusy]=useState(false);
  const form=useForm<z.infer<typeof loginSchema>>({resolver:zodResolver(loginSchema)});
  if(accountAction)return <div className="auth"><aside><div className="wordmark"><span className="logo">G</span>GST Billing Pro</div><h1>Your business.<br/>Protected.</h1></aside><main><AccountAction initial={accountAction} back={()=>setAccountAction('')}/></main></div>;
  async function submit(data:z.infer<typeof loginSchema>){setBusy(true);setError(undefined);try{const extras=Object.fromEntries(new FormData(document.querySelector('form')!).entries());const r=await api.post(`/auth/${register?'register':'login'}`,{...extras,...data});if(r.data.verification_required){setRegister(false);setAccountAction('verification');}else{setToken(r.data.access_token);done();}}catch(e){setError(e);}finally{setBusy(false);}}
  return <div className="auth"><aside><div className="wordmark"><span className="logo">G</span>GST Billing <b>Pro</b></div><div><span className="eyebrow">A CLEARER PICTURE OF YOUR BUSINESS</span><h1>Less paperwork.<br/>More possibility.</h1><p>Your customers, invoices, and payments.<br/>One thoughtful workspace.</p></div><small>Built for Indian businesses. Designed for everyday clarity.</small></aside><main><div className="auth-form"><span className="eyebrow">YOUR BUSINESS, IN BALANCE</span><h1>{register?'Start your workspace':'Welcome back'}</h1><p>{register?'Create your company and administrator account.':'Sign in to keep your business moving.'}</p><form onSubmit={form.handleSubmit(submit)}>{register&&<><Field label="Your name"><input name="name" minLength={2} maxLength={120} required/></Field><Field label="Company name"><input name="company_name" minLength={2} maxLength={160} required/></Field><Field label="GST state code"><input name="state_code" placeholder="27" pattern="[0-9]{2}" required/></Field></>}<Field label="Email address"><input type="email" autoComplete="email" {...form.register('email')}/></Field><Field label="Password"><input type="password" autoComplete={register?'new-password':'current-password'} minLength={register?12:1} {...form.register('password')}/></Field>{Object.values(form.formState.errors).map((e,i)=><p className="error" key={i}>{e.message}</p>)}{error!=null&&<ErrorBox error={error}/>}<button className="primary wide" disabled={busy}>{busy?'Please wait…':register?'Create workspace':'Sign in'}<ArrowUpRight size={18}/></button></form><button className="text-button" onClick={()=>setRegister(!register)}>{register?'Already have an account? Sign in':'Registration enabled? Create a workspace'}</button><button className="text-button" onClick={()=>setAccountAction('forgot')}>Forgot password or verify email</button><div className="secure-note"><ShieldCheck size={16}/> Secure access. Company data stays separate.</div></div></main></div>;
}
