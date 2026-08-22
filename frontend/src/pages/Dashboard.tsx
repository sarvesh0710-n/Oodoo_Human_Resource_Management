import React, { useEffect, useState } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import type { User, Attendance, LeaveRequest } from '../lib/types';
import api from '../lib/api';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { Clock, Calendar, Briefcase, FileCheck, LogIn, LogOut } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useOutletContext<{ user: User }>();
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchData = async () => {
    try {
      const [attRes, leaveRes] = await Promise.all([
        api.get<Attendance[]>('/attendance'),
        api.get<LeaveRequest[]>('/leave/requests')
      ]);
      setAttendance(attRes.data || []);
      setLeaves(leaveRes.data || []);
    } catch (err) {
      console.error("Failed to load dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCheckInOut = async (type: 'in' | 'out') => {
    try {
      if (type === 'in') {
        await api.post('/attendance/check-in');
      } else {
        await api.post('/attendance/check-out');
      }
      fetchData(); // Refresh data
    } catch (err) {
      alert(`Check ${type} failed. It might already be logged.`);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading your workspace...</div>;

  const todayStr = new Date().toISOString().split('T')[0];
  const todayRecord = attendance.find(a => a.date === todayStr);
  const isCheckedIn = todayRecord && !todayRecord.check_out;
  const isCompleted = todayRecord && todayRecord.check_out;

  const presentCount = attendance.filter(a => a.status === 'present').length;
  const leaveCount = leaves.filter(l => l.status === 'approved').length;

  return (
    <div className="animate-fade-in max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl mb-1">Hello, Team Member 👋</h1>
          <p className="text-slate-500">Here is your work summary for today.</p>
        </div>
        {user.role === 'admin_hr' && (
          <Link to="/admin-dashboard" className="px-4 py-2 bg-emerald-100 text-emerald-800 rounded-lg hover:bg-emerald-200 font-medium transition-colors border border-emerald-200">
            Switch to Admin View
          </Link>
        )}
      </div>

      <div className="grid-4">
        <StatCard title="Days Present" value={presentCount || 18} icon={Calendar} color="sage" />
        <StatCard title="Logged Hours" value={`${(presentCount || 18) * 8} hrs`} icon={Clock} color="ochre" />
        <StatCard title="Leaves Taken" value={`${leaveCount || 2} days`} icon={Briefcase} color="terracotta" />
        <StatCard title="Leave Balance" value="16 days" icon={FileCheck} color="sage" />
      </div>

      <div className="grid-2">
        <div className="glass-card bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-lg font-bold text-slate-800">Today's Check-In</h3>
              <p className="text-sm text-slate-500">Log your shift check-in and check-out</p>
            </div>
            <StatusBadge status={isCompleted ? 'Approved' : isCheckedIn ? 'Present' : 'Pending'} />
          </div>

          <div className="bg-slate-50 rounded-xl p-8 text-center mb-6 border border-slate-100 shadow-inner">
            <div className="text-4xl font-bold text-slate-800 font-mono tracking-wider">{currentTime}</div>
            <div className="text-sm text-slate-400 mt-2 font-medium uppercase tracking-widest">Local System Time</div>
          </div>

          <div className="flex gap-4">
            <button 
              onClick={() => handleCheckInOut('in')}
              disabled={!!todayRecord}
              className="flex-1 flex justify-center items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 px-4 rounded-xl transition-all disabled:opacity-50 disabled:hover:bg-emerald-600 shadow-sm hover:shadow-md"
            >
              <LogIn size={20} />
              Check In Now
            </button>
            <button 
              onClick={() => handleCheckInOut('out')}
              disabled={!isCheckedIn}
              className="flex-1 flex justify-center items-center gap-2 bg-rose-600 hover:bg-rose-700 text-white font-medium py-3 px-4 rounded-xl transition-all disabled:opacity-50 disabled:hover:bg-rose-600 shadow-sm hover:shadow-md"
            >
              <LogOut size={20} />
              Check Out
            </button>
          </div>
        </div>

        <div className="glass-card bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-lg font-bold text-slate-800">Recent Time-Off</h3>
              <p className="text-sm text-slate-500">Your latest leave requests</p>
            </div>
            <Link to="/leave" className="text-sm font-medium text-emerald-600 hover:text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg">Apply Leave</Link>
          </div>

          <div className="space-y-3">
            {leaves.length === 0 ? (
              <div className="p-8 text-center text-slate-400 bg-slate-50 rounded-xl border border-slate-100 border-dashed">
                No leave requests submitted yet.
              </div>
            ) : (
              leaves.slice(0, 4).map(leave => (
                <div key={leave.id} className="flex justify-between items-center p-4 rounded-xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-colors">
                  <div>
                    <div className="font-semibold text-slate-800">{new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}</div>
                    <div className="text-xs text-slate-500 mt-1">{leave.remarks || 'Time-off request'}</div>
                  </div>
                  <StatusBadge status={leave.status} />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
