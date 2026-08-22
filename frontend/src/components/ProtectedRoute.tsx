import React, { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { getMe, isAuthenticated } from '../lib/auth';
import { User } from '../lib/types';

interface ProtectedRouteProps {
  allowedRoles?: string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const isAuth = isAuthenticated();

  useEffect(() => {
    if (!isAuth) {
      setLoading(false);
      return;
    }
    
    getMe()
      .then(userData => {
        setUser(userData);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [isAuth]);

  if (!isAuth) {
    return <Navigate to="/login" replace />;
  }

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // Redirect to default dashboard if role doesn't match
    return <Navigate to={user.role === 'admin_hr' ? '/admin-dashboard' : '/dashboard'} replace />;
  }

  return <Outlet context={{ user }} />;
};
