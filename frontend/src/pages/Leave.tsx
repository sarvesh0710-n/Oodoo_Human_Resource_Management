import React, { useEffect, useState } from 'react';
import { LeaveRequest, LeaveType } from '../lib/types';
import api from '../lib/api';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

export const Leave: React.FC = () => {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    leave_type_id: '',
    start_date: '',
    end_date: '',
    remarks: ''
  });

  const fetchData = async () => {
    try {
      const [reqRes, typesRes] = await Promise.all([
        api.get<LeaveRequest[]>('/leave/requests'),
        api.get<LeaveType[]>('/leave/types')
      ]);
      setRequests(reqRes.data || []);
      setLeaveTypes(typesRes.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/leave/requests', {
        ...formData,
        leave_type_id: parseInt(formData.leave_type_id)
      });
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit leave request');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading leave data...</div>;

  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl mb-1">Time-Off Requests</h1>
          <p className="text-slate-500">Apply for leaves and track approval status.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium transition-colors shadow-sm"
        >
          + Request Leave
        </button>
      </div>

      <div className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-bold">
                <th className="p-4 pl-6">Duration</th>
                <th className="p-4">Type ID</th>
                <th className="p-4">Remarks</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {requests.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-8 text-center text-slate-400">No leave requests found.</td>
                </tr>
              ) : (
                requests.map((req) => (
                  <tr key={req.id} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                    <td className="p-4 pl-6 font-medium text-slate-700">
                      {new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()}
                    </td>
                    <td className="p-4 text-slate-600">{req.leave_type_id}</td>
                    <td className="p-4 text-slate-600 truncate max-w-xs">{req.remarks || '—'}</td>
                    <td className="p-4"><StatusBadge status={req.status} /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Request Time-Off">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Leave Type</label>
            <select 
              required
              className="w-full p-2.5 rounded-lg border border-slate-300 focus:border-emerald-500 outline-none"
              value={formData.leave_type_id}
              onChange={e => setFormData({...formData, leave_type_id: e.target.value})}
            >
              <option value="">Select a type...</option>
              {leaveTypes.map(type => (
                <option key={type.id} value={type.id}>{type.name}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Start Date</label>
              <input 
                type="date" 
                required
                className="w-full p-2.5 rounded-lg border border-slate-300 focus:border-emerald-500 outline-none"
                value={formData.start_date}
                onChange={e => setFormData({...formData, start_date: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">End Date</label>
              <input 
                type="date" 
                required
                className="w-full p-2.5 rounded-lg border border-slate-300 focus:border-emerald-500 outline-none"
                value={formData.end_date}
                onChange={e => setFormData({...formData, end_date: e.target.value})}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Remarks</label>
            <textarea 
              rows={3}
              className="w-full p-2.5 rounded-lg border border-slate-300 focus:border-emerald-500 outline-none"
              value={formData.remarks}
              onChange={e => setFormData({...formData, remarks: e.target.value})}
            ></textarea>
          </div>
          <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 rounded-lg mt-4">
            Submit Request
          </button>
        </form>
      </Modal>
    </div>
  );
};
