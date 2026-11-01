import { QueryClient } from '@tanstack/react-query';
import { FileText,LayoutDashboard,Package,Settings,ShieldCheck,Users,Wallet } from 'lucide-react';
export type RecordData = Record<string, any>;
export const money = (value: string | number = 0) => new Intl.NumberFormat('en-IN', {style: 'currency', currency: 'INR'}).format(Number(value));
export const today = () => new Date().toLocaleDateString('en-CA');
export const queryClient = new QueryClient({defaultOptions:{queries:{retry:1, refetchOnWindowFocus:false}}});
export const nav = [{to:'/', label:'Overview',icon:LayoutDashboard},{to:'/invoices',label:'Invoices',icon:FileText},{to:'/products',label:'Products & services',icon:Package},{to:'/customers',label:'Customers',icon:Users},{to:'/payments',label:'Payments',icon:Wallet},{to:'/reports',label:'Sales & GST reports',icon:FileText},{to:'/sessions',label:'Active sessions',icon:ShieldCheck},{to:'/users',label:'Team & permissions',icon:ShieldCheck},{to:'/settings',label:'Company settings',icon:Settings},{to:'/audit-logs',label:'Audit trail',icon:FileText}];

