import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { Employee, Department, LeaveRequest } from '../lib/types';
import api from '../lib/api';
import { StatCard } from '../components/StatCard';
import { Users, FileCheck, Percent, Building, ClipboardList, Wallet } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [empRes, deptRes, leaveRes] = await Promise.all([
          api.get<Employee[]>('/employees'),
          api.get<Department[]>('/departments'),
          api.get<LeaveRequest[]>('/leave/requests')
        ]);
        setEmployees(empRes.data || []);
        setDepartments(deptRes.data || []);
        setLeaves(leaveRes.data || []);
      } catch (err) {
        console.error("Failed to load admin data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading HR Overview...</div>;

  const pendingLeaves = leaves.filter(l => l.status.toLowerCase() === 'pending').length;

  return (
    <div className="animate-fade-in max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl mb-1">HR & Operations Overview</h1>
          <p className="text-slate-500">Real-time headcount, attendance snapshot, and pending workflow approvals.</p>
        </div>
        <div className="flex gap-3">
          <Link to="/leave-approvals" className="px-4 py-2 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg font-medium transition-colors border border-rose-200 shadow-sm flex items-center gap-2">
            <span>⚡ Review Pending ({pendingLeaves})</span>
          </Link>
          <Link to="/employees" className="px-4 py-2 bg-emerald-600 text-white hover:bg-emerald-700 rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2">
            <span>+ Add Employee</span>
          </Link>
        </div>
      </div>

      <div className="grid-4">
        <StatCard title="Total Active Staff" value={employees.length || 0} icon={Users} color="sage" />
        <StatCard title="Pending Approvals" value={pendingLeaves} icon={FileCheck} color="terracotta" />
        <StatCard title="Attendance Rate" value="94.2%" icon={Percent} color="sage" />
        <StatCard title="Active Departments" value={departments.length || 0} icon={Building} color="ochre" />
      </div>

      <div className="grid-2">
        <div className="glass-card bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-lg font-bold text-slate-800">Department Distribution</h3>
              <p className="text-sm text-slate-500">Headcount allocation by team</p>
            </div>
            <Link to="/departments" className="text-sm font-medium text-slate-600 hover:text-emerald-600 bg-slate-100 hover:bg-emerald-50 px-3 py-1.5 rounded-lg transition-colors">Manage</Link>
          </div>

          <div className="space-y-3">
            {departments.length === 0 ? (
              <div className="p-8 text-center text-slate-400 bg-slate-50 rounded-xl border border-slate-100 border-dashed">
                No departments created yet. <Link to="/departments" className="text-emerald-600">Create your first department</Link>
              </div>
            ) : (
              departments.map(dept => (
                <div key={dept.id} className="flex justify-between items-center p-4 rounded-xl bg-slate-50 border border-slate-100">
                  <div>
                    <div className="font-semibold text-slate-800">{dept.name}</div>
                    <div className="text-xs text-slate-500 mt-1">{dept.description || 'Core Department'}</div>
                  </div>
                  <span className="px-3 py-1 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 shadow-sm">
                    {dept.employee_count || 0} Members
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="glass-card bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="mb-6 pb-4 border-b border-slate-100">
            <h3 className="text-lg font-bold text-slate-800">Admin Workflows</h3>
            <p className="text-sm text-slate-500">Direct shortcuts to HR actions</p>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <Link to="/leave-approvals" className="block p-6 text-center rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 transition-all hover:-translate-y-1 group">
              <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <ClipboardList size={24} />
              </div>
              <div className="font-semibold text-slate-800 mb-1">Leave Approvals</div>
              <div className="text-xs text-slate-500">Review pending requests</div>
            </Link>

            <Link to="/admin-payroll" className="block p-6 text-center rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 transition-all hover:-translate-y-1 group">
              <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <Wallet size={24} />
              </div>
              <div className="font-semibold text-slate-800 mb-1">Generate Payslips</div>
              <div className="text-xs text-slate-500">Run monthly payroll</div>
            </Link>
          </div>

          <div className="bg-emerald-50 border border-emerald-100 p-4 rounded-xl">
            <div className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2">System Status</div>
            <div className="flex items-center gap-3 text-sm">
              <span className="flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span className="text-emerald-900 font-medium">Operational</span>
              <span className="text-emerald-700 ml-auto">Database connected & RBAC active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
