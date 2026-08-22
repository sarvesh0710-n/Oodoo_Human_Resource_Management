import React, { useEffect, useState } from 'react';
import { Attendance as AttendanceType } from '../lib/types';
import api from '../lib/api';
import { StatusBadge } from '../components/StatusBadge';

export const Attendance: React.FC = () => {
  const [attendance, setAttendance] = useState<AttendanceType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAttendance = async () => {
      try {
        const res = await api.get<AttendanceType[]>('/attendance');
        setAttendance(res.data || []);
      } catch (err) {
        console.error("Failed to load attendance", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAttendance();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading attendance data...</div>;

  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl mb-1">Attendance Log</h1>
        <p className="text-slate-500">Your daily check-in and check-out records.</p>
      </div>

      <div className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <div>
            <h3 className="text-lg font-bold text-slate-800">Detailed Logs</h3>
            <p className="text-sm text-slate-500">Complete attendance records for the current period</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-bold">
                <th className="p-4 pl-6">Date</th>
                <th className="p-4">Check In</th>
                <th className="p-4">Check Out</th>
                <th className="p-4">Total Hours</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {attendance.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-400">No attendance records found.</td>
                </tr>
              ) : (
                attendance.map((row) => (
                  <tr key={row.id} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                    <td className="p-4 pl-6 font-medium text-slate-700">{new Date(row.date).toLocaleDateString()}</td>
                    <td className="p-4 text-slate-600">{row.check_in || '—'}</td>
                    <td className="p-4 text-slate-600">{row.check_out || '—'}</td>
                    <td className="p-4 text-slate-600">{row.check_in && row.check_out ? '8.0 hrs' : '—'}</td>
                    <td className="p-4"><StatusBadge status={row.status} /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
