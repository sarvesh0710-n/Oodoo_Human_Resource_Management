import React, { useEffect, useState } from 'react';
import { Employee, Department } from '../lib/types';
import api from '../lib/api';
import { Modal } from '../components/Modal';
import { UserPlus } from 'lucide-react';

export const Employees: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState<any>({
    password: 'password123', // default password for new employees
    role: 'employee'
  });

  const fetchData = async () => {
    try {
      const [empRes, deptRes] = await Promise.all([
        api.get<Employee[]>('/employees'),
        api.get<Department[]>('/departments')
      ]);
      setEmployees(empRes.data || []);
      setDepartments(deptRes.data || []);
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
      await api.post('/employees', {
        ...formData,
        department_id: formData.department_id ? parseInt(formData.department_id) : null
      });
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add employee');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading employee directory...</div>;

  return (
    <div className="animate-fade-in max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl mb-1">Employee Directory</h1>
          <p className="text-slate-500">Manage all staff members in the organization.</p>
        </div>
        <button 
          onClick={() => { setFormData({password: 'password123', role: 'employee'}); setIsModalOpen(true); }}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium transition-colors shadow-sm flex items-center gap-2"
        >
          <UserPlus size={18} /> Add Employee
        </button>
      </div>

      <div className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-bold">
                <th className="p-4 pl-6">Code</th>
                <th className="p-4">Name</th>
                <th className="p-4">Job Title</th>
                <th className="p-4">Department</th>
                <th className="p-4">Joined</th>
              </tr>
            </thead>
            <tbody>
              {employees.map(emp => {
                const dept = departments.find(d => d.id === emp.department_id);
                return (
                  <tr key={emp.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                    <td className="p-4 pl-6 font-medium text-slate-700">#{emp.id}</td>
                    <td className="p-4 font-bold text-slate-800">{emp.first_name} {emp.last_name}</td>
                    <td className="p-4 text-slate-600">{emp.job_title || '—'}</td>
                    <td className="p-4 text-slate-600">
                      <span className="px-2 py-1 bg-slate-100 rounded text-xs">{dept ? dept.name : 'Unassigned'}</span>
                    </td>
                    <td className="p-4 text-slate-600 text-sm">{new Date(emp.joining_date).toLocaleDateString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add New Employee">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-1">First Name</label>
              <input type="text" required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, first_name: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">Last Name</label>
              <input type="text" required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, last_name: e.target.value})} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Email</label>
            <input type="email" required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, email: e.target.value})} />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Temporary Password</label>
            <input type="text" required defaultValue="password123" className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, password: e.target.value})} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-1">Department</label>
              <select className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, department_id: e.target.value})}>
                <option value="">None</option>
                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">Role</label>
              <select required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, role: e.target.value})}>
                <option value="employee">Employee</option>
                <option value="admin_hr">HR Admin</option>
              </select>
            </div>
          </div>
          <button type="submit" className="w-full bg-emerald-600 text-white p-2.5 rounded-lg mt-4 font-medium hover:bg-emerald-700">Add Employee</button>
        </form>
      </Modal>
    </div>
  );
};
