import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import type { User } from '../lib/types';
import { LayoutDashboard, Calendar, Clock, FileText, User as UserIcon, Users, Building, FileCheck, CircleDollarSign, ShieldCheck } from 'lucide-react';

interface SidebarProps {
  user: User;
}

export const Sidebar: React.FC<SidebarProps> = ({ user }) => {
  const location = useLocation();
  const isAdmin = user.role === 'admin_hr';

  const NavItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => {
    const isActive = location.pathname === to;
    return (
      <Link 
        to={to} 
        className={`nav-item flex items-center gap-2 p-2 rounded-md mb-1 transition-colors ${
          isActive 
            ? 'bg-emerald-700 text-white font-medium' 
            : 'text-slate-600 hover:bg-emerald-50 hover:text-emerald-800'
        }`}
        style={isActive ? { background: 'var(--color-primary)', color: 'white' } : {}}
      >
        <Icon size={18} />
        <span>{label}</span>
      </Link>
    );
  };

  return (
    <aside className="w-64 border-r bg-white flex flex-col h-full shadow-sm" style={{ borderRight: '1px solid var(--border-main)' }}>
      <div className="p-4 border-b flex items-center gap-2" style={{ borderBottom: '1px solid var(--border-main)' }}>
        <div className="w-8 h-8 rounded bg-emerald-700 flex items-center justify-center text-white font-bold" style={{ background: 'var(--color-primary)' }}>
          D
        </div>
        <div>
          <h2 className="font-bold text-lg leading-tight m-0" style={{ color: 'var(--color-primary-dark)' }}>Dayflow</h2>
          <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded">HRMS</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-2 mt-2">Main Navigation</div>
        <NavItem to="/dashboard" icon={LayoutDashboard} label="Dashboard" />
        <NavItem to="/attendance" icon={Clock} label="Attendance Log" />
        <NavItem to="/leave" icon={Calendar} label="Leave & Time-Off" />
        <NavItem to="/payroll" icon={FileText} label="My Payslips" />
        <NavItem to="/profile" icon={UserIcon} label="My Profile" />

        {isAdmin && (
          <>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-2 mt-6">Admin & HR</div>
            <NavItem to="/admin-dashboard" icon={ShieldCheck} label="HR Overview" />
            <NavItem to="/employees" icon={Users} label="Employee Directory" />
            <NavItem to="/leave-approvals" icon={FileCheck} label="Leave Approvals" />
            <NavItem to="/departments" icon={Building} label="Departments" />
            <NavItem to="/admin-payroll" icon={CircleDollarSign} label="Payroll Management" />
          </>
        )}
      </div>
    </aside>
  );
};
