import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { Attendance } from './pages/Attendance';
import { Leave } from './pages/Leave';
import { LeaveApprovals } from './pages/LeaveApprovals';
import { Payroll } from './pages/Payroll';
import { AdminPayroll } from './pages/AdminPayroll';
import { Profile } from './pages/Profile';
import { Employees } from './pages/Employees';
import { Departments } from './pages/Departments';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* Protected Routes Wrapper */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/attendance" element={<Attendance />} />
            <Route path="/leave" element={<Leave />} />
            <Route path="/payroll" element={<Payroll />} />
            <Route path="/profile" element={<Profile />} />
            
            {/* HR Admin Only Routes */}
            <Route element={<ProtectedRoute allowedRoles={['admin_hr']} />}>
              <Route path="/admin-dashboard" element={<AdminDashboard />} />
              <Route path="/employees" element={<Employees />} />
              <Route path="/departments" element={<Departments />} />
              <Route path="/leave-approvals" element={<LeaveApprovals />} />
              <Route path="/admin-payroll" element={<AdminPayroll />} />
            </Route>
            
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Route>
        
        {/* Default fallback */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
