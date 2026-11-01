import { render,screen,waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe,expect,it,vi } from 'vitest';
import { api } from '../api/client';
import { Modal } from '../components/ui';
import InvoiceTable from '../features/invoices/InvoiceTable';
import Auth from '../pages/Auth';

describe('business workflow interface',()=>{
  it('validates required login fields before calling the backend',async()=>{
    const post=vi.spyOn(api,'post');const done=vi.fn();const user=userEvent.setup();
    render(<Auth done={done}/>);
    await user.click(screen.getByRole('button',{name:/^Sign in$/}));
    expect(post).not.toHaveBeenCalled();expect(done).not.toHaveBeenCalled();
  });

  it('submits credentials and enters the workspace only after API success',async()=>{
    const post=vi.spyOn(api,'post').mockResolvedValue({data:{access_token:'test-access-token'}});const done=vi.fn();const user=userEvent.setup();
    render(<Auth done={done}/>);
    await user.type(screen.getByLabelText('Email address'),'owner@example.com');
    await user.type(screen.getByLabelText('Password'),'valid-test-password');
    await user.click(screen.getByRole('button',{name:/^Sign in$/}));
    await waitFor(()=>expect(done).toHaveBeenCalledOnce());
    expect(post).toHaveBeenCalledWith('/auth/login',expect.objectContaining({email:'owner@example.com',password:'valid-test-password'}));
  });

  it('shows backend authentication failures without entering the workspace',async()=>{
    vi.spyOn(api,'post').mockRejectedValue(new Error('network'));const done=vi.fn();const user=userEvent.setup();
    render(<Auth done={done}/>);
    await user.type(screen.getByLabelText('Email address'),'owner@example.com');await user.type(screen.getByLabelText('Password'),'incorrect');
    await user.click(screen.getByRole('button',{name:/^Sign in$/}));
    expect(await screen.findByRole('alert')).toBeVisible();expect(done).not.toHaveBeenCalled();
  });

  it('keeps issued document status separate from payment status and links to details',()=>{
    render(<MemoryRouter><InvoiceTable rows={[{id:42,number:'INV/2026-27/00042',invoice_date:'2026-11-01',status:'issued',paid:'100.00',total:'1180.00'}]}/></MemoryRouter>);
    expect(screen.getByText('issued')).toBeVisible();expect(screen.getByText('Part paid')).toBeVisible();
    expect(screen.getByRole('link',{name:'INV/2026-27/00042'})).toHaveAttribute('href','/invoices/42');
  });

  it('supports escape dismissal and traps keyboard focus in a confirmation dialog',async()=>{
    const close=vi.fn();const user=userEvent.setup();
    render(<Modal title="Approve invoice" close={close}><button>Approve & issue</button></Modal>);
    const dismiss=screen.getByRole('button',{name:'Close dialog'}),approve=screen.getByRole('button',{name:'Approve & issue'});
    expect(dismiss).toHaveFocus();await user.tab({shift:true});expect(approve).toHaveFocus();
    await user.tab();expect(dismiss).toHaveFocus();await user.keyboard('{Escape}');expect(close).toHaveBeenCalled();
  });
});
