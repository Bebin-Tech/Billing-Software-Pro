import { FileText,X } from 'lucide-react';
import React,{ useEffect,useRef } from 'react';
import { errorMessage } from './../api/client';


export function Field({label, children}: {label:string;children:React.ReactNode}) { return <label className="field"><span>{label}</span>{children}</label>; }
export function ErrorBox({error}: {error:unknown}) { return <div role="alert" className="error">{errorMessage(error)}</div>; }
export function Empty({label='No records yet', detail='Your business activity will appear here as you get started.'}) {return <div className="empty"><FileText size={30}/><h3>{label}</h3><p>{detail}</p></div>;}
export function Modal({title, children, close}: {title:string;children:React.ReactNode;close:()=>void}) {
  const dialog=useRef<HTMLElement>(null);
  const onClose=useRef(close); onClose.current=close;
  useEffect(()=>{
    const previous=document.activeElement as HTMLElement|null;
    const focusables=()=>Array.from(dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input, select, textarea, a[href], [tabindex="0"]')||[]);
    focusables()[0]?.focus();
    const trap=(event:KeyboardEvent)=>{
      if(event.key==='Escape'){event.stopPropagation();onClose.current();}
      if(event.key==='Tab'){
        const items=focusables(),first=items[0],last=items[items.length-1];
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
      }
    };
    const oldOverflow=document.body.style.overflow;document.body.style.overflow='hidden';
    document.addEventListener('keydown',trap);
    return()=>{document.removeEventListener('keydown',trap);document.body.style.overflow=oldOverflow;previous?.focus();};
  },[]);
  return <div className="overlay" onClick={close}><section ref={dialog} className="modal" role="dialog" aria-modal="true" aria-label={title} onClick={e=>e.stopPropagation()}><header><h2>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={close}><X/></button></header>{children}</section></div>;
}
