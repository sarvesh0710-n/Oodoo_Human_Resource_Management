import React, { useEffect, useState } from 'react';
import type { Department } from '../lib/types';
import api from '../lib/api';
import { Modal } from '../components/Modal';
import { Building2 } from 'lucide-react';

export const Departments: React.FC = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState<any>({});

  const fetchDepartments = async () => {
    try {
      const res = await api.get<Department[]>('/departments');
      setDepartments(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/departments', formData);
      setIsModalOpen(false);
      fetchDepartments();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add department');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading departments...</div>;

  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl mb-1">Departments</h1>
          <p className="text-slate-500">Manage organizational structure and teams.</p>
        </div>
        <button 
          onClick={() => { setFormData({}); setIsModalOpen(true); }}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium transition-colors shadow-sm flex items-center gap-2"
        >
          <Building2 size={18} /> New Department
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {departments.length === 0 ? (
          <div className="col-span-full p-8 text-center bg-slate-50 border border-slate-200 border-dashed rounded-xl text-slate-500">
            No departments created yet.
          </div>
        ) : (
          departments.map(dept => (
            <div key={dept.id} className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col hover:border-emerald-200 hover:shadow-md transition-all">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                  <Building2 size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-slate-800">{dept.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">{dept.description || 'Core Department'}</p>
                </div>
              </div>
              
              <div className="mt-auto pt-4 border-t border-slate-100 flex justify-between items-center">
                <span className="text-sm font-medium text-slate-600 bg-slate-50 px-3 py-1 rounded-full border border-slate-200">
                  {dept.employee_count} Members
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create Department">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1">Department Name</label>
            <input type="text" required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, name: e.target.value})} />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Description</label>
            <textarea rows={3} className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, description: e.target.value})}></textarea>
          </div>
          <button type="submit" className="w-full bg-emerald-600 text-white p-2.5 rounded-lg mt-4 font-medium hover:bg-emerald-700">Create Department</button>
        </form>
      </Modal>
    </div>
  );
};
