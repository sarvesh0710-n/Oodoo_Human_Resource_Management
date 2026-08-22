import React from 'react';
import { Outlet, useOutletContext } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import type { User } from '../lib/types';

export const Layout: React.FC = () => {
  // We get the user from the ProtectedRoute context
  const { user } = useOutletContext<{ user: User }>();

  return (
    <div className="app-container">
      <Sidebar user={user} />
      <div className="main-content">
        <Navbar user={user} />
        <main className="page-content bg-slate-50">
          <Outlet context={{ user }} />
        </main>
      </div>
    </div>
  );
};
