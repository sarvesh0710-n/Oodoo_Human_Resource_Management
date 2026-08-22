import React from 'react';
import { User } from '../lib/types';
import { logout } from '../lib/auth';
import { LogOut } from 'lucide-react';

interface NavbarProps {
  user: User;
}

export const Navbar: React.FC<NavbarProps> = ({ user }) => {
  return (
    <header className="h-16 bg-white border-b flex items-center justify-between px-6 shadow-sm sticky top-0 z-10" style={{ borderBottom: '1px solid var(--border-main)' }}>
      <div className="flex items-center">
        <h1 className="text-xl font-bold m-0" style={{ color: 'var(--color-primary-dark)', fontFamily: 'Outfit, sans-serif' }}>
          Dayflow HRMS
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <div 
          className="text-xs font-medium px-2 py-1 rounded border flex items-center gap-1"
          style={
            user.role === 'admin_hr' 
              ? { background: 'var(--color-primary)', color: 'white', borderColor: 'var(--color-primary-dark)' }
              : { background: 'var(--color-bg)', color: 'var(--color-primary)', borderColor: 'var(--color-primary)' }
          }
        >
          {user.role === 'admin_hr' ? 'HR Admin' : 'Employee'}
        </div>
        
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center font-semibold text-sm" style={{ background: 'var(--color-primary-light)' }}>
            {user.email.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm font-medium text-slate-700 hidden sm:block">{user.email}</span>
        </div>

        <button 
          onClick={logout}
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-red-600 transition-colors border px-3 py-1.5 rounded bg-white hover:bg-slate-50"
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">Sign Out</span>
        </button>
      </div>
    </header>
  );
};
