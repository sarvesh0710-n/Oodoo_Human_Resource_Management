import React, { useEffect, useState } from 'react';
import type { LeaveRequest } from '../lib/types';
import api from '../lib/api';
import { StatusBadge } from '../components/StatusBadge';

export const LeaveApprovals: React.FC = () => {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRequests = async () => {
    try {
      const res = await api.get<LeaveRequest[]>('/leave/requests');
      setRequests(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleAction = async (id: number, action: 'approve' | 'reject') => {
    try {
      await api.patch(`/leave/requests/${id}/review`, {
        status: action === 'approve' ? 'Approved' : 'Rejected',
        review_comment: `Reviewed by HR`
      });
      fetchRequests();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to review request');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading leave requests...</div>;

  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl mb-1">Leave Approvals</h1>
        <p className="text-slate-500">Review and manage employee time-off requests.</p>
      </div>

      <div className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-bold">
                <th className="p-4 pl-6">Employee ID</th>
                <th className="p-4">Duration</th>
                <th className="p-4">Remarks</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right pr-6">Action</th>
              </tr>
            </thead>
            <tbody>
              {requests.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-400">No pending leave requests.</td>
                </tr>
              ) : (
                requests.map((req) => (
                  <tr key={req.id} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                    <td className="p-4 pl-6 font-medium text-slate-700">Emp #{req.employee_id}</td>
                    <td className="p-4 text-slate-600">
                      {new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()}
                    </td>
                    <td className="p-4 text-slate-600 truncate max-w-xs">{req.remarks || '—'}</td>
                    <td className="p-4"><StatusBadge status={req.status} /></td>
                    <td className="p-4 text-right pr-6">
                      {req.status.toLowerCase() === 'pending' && (
                        <div className="flex gap-2 justify-end">
                          <button 
                            onClick={() => handleAction(req.id, 'approve')}
                            className="text-xs bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-semibold py-1.5 px-3 rounded transition-colors"
                          >
                            Approve
                          </button>
                          <button 
                            onClick={() => handleAction(req.id, 'reject')}
                            className="text-xs bg-red-100 hover:bg-red-200 text-red-700 font-semibold py-1.5 px-3 rounded transition-colors"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </td>
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
