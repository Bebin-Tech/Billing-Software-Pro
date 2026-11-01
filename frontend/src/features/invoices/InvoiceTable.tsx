import { ChevronRight } from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { RecordData,money } from './../../app/runtime';
import { Empty } from './../../components/ui';

export default function InvoiceTable({rows}:{rows:RecordData[]}) {return rows.length?<div className="table-scroll"><table><thead><tr><th>Invoice</th><th>Invoice date</th><th>Status</th><th>Payment</th><th className="right">Amount</th><th/></tr></thead><tbody>{rows.map(r=><tr key={r.id}><td><NavLink to={`/invoices/${r.id}`}>{r.number||`Draft #${r.id}`}</NavLink></td><td>{r.invoice_date}</td><td><span className={`badge ${r.status}`}>{r.status}</span></td><td>{Number(r.paid)>=Number(r.total)&&r.status==='issued'?'Paid':Number(r.paid)>0?'Part paid':'Unpaid'}</td><td className="right"><b>{money(r.total)}</b></td><td><NavLink aria-label="View invoice" to={`/invoices/${r.id}`}><ChevronRight size={17}/></NavLink></td></tr>)}</tbody></table></div>:<Empty label="No invoices yet" detail="Create a draft to start your first billing workflow."/>;}
