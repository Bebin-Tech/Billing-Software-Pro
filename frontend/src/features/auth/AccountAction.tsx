import { useState } from 'react';
import { api,errorMessage } from '../../api/client';
import { Field } from '../../components/ui';

export default function AccountAction({initial,back}:{initial:string;back:()=>void}) {
  const [mode,setMode]=useState(initial),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('');
  const token=new URLSearchParams(window.location.hash.slice(1)).get('token')||'';
  const title=mode==='reset'?'Set a new password':mode==='verify'?'Verify your email':mode==='verification'?'Request verification':'Reset your password';
  async function submit(e:React.FormEvent<HTMLFormElement>){
    e.preventDefault();setError('');setBusy(true);
    const values=Object.fromEntries(new FormData(e.currentTarget));
    try{
      const path=mode==='reset'?'reset-password':mode==='verify'?'verify-email':mode==='verification'?'request-verification':'forgot-password';
      const body=mode==='reset'?{token,password:values.password}:mode==='verify'?{token}:{email:values.email};
      const response=await api.post(`/auth/${path}`,body);
      setMessage(response.data.detail);
    }catch(e){setError(errorMessage(e));}finally{setBusy(false);}
  }
  return <div className="auth-form"><span className="eyebrow">ACCOUNT SECURITY</span><h1>{title}</h1><p>Secure, single-use email links expire after 30 minutes.</p><form onSubmit={submit}>{mode==='reset'?<Field label="New password"><input name="password" type="password" autoComplete="new-password" minLength={12} maxLength={72} required/></Field>:mode!=='verify'?<Field label="Email address"><input name="email" type="email" autoComplete="email" required/></Field>:<p>Confirm the verification link from your email.</p>}{error&&<p className="error" role="alert">{error}</p>}{message&&<p className="success" role="status">{message}</p>}<button className="primary wide" disabled={busy||Boolean(message)||(['reset','verify'].includes(mode)&&!token)}>{busy?'Please wait…':mode==='verify'?'Verify email':mode==='reset'?'Save new password':'Send email link'}</button></form>{!['reset','verify'].includes(mode)&&<button className="text-button" onClick={()=>{setMode(mode==='verification'?'forgot':'verification');setError('');setMessage('');}}>{mode==='verification'?'Need to reset your password?':'Need an email verification link?'}</button>}<br/><button className="text-button" onClick={()=>{window.history.replaceState(null,'','/');back();}}>Back to sign in</button></div>;
}
