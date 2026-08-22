import React, { useEffect, useState } from 'react';
import type { Employee, SalaryStructure, Payslip } from '../lib/types';
import api from '../lib/api';
import { Modal } from '../components/Modal';

export const AdminPayroll: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [structures, setStructures] = useState<SalaryStructure[]>([]);
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isStructOpen, setIsStructOpen] = useState(false);
  const [isPayslipOpen, setIsPayslipOpen] = useState(false);
  const [formData, setFormData] = useState<any>({});

  const fetchData = async () => {
    try {
      const [empRes, strRes, slipRes] = await Promise.all([
        api.get<Employee[]>('/employees'),
        api.get<SalaryStructure[]>('/payroll/structures'),
        api.get<Payslip[]>('/payroll/payslips')
      ]);
      setEmployees(empRes.data || []);
      setStructures(strRes.data || []);
      setPayslips(slipRes.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleStructureSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/payroll/structures', {
        employee_id: parseInt(formData.employee_id),
        basic_salary: parseFloat(formData.basic_salary),
        allowances: parseFloat(formData.allowances || 0),
        deductions: parseFloat(formData.deductions || 0),
        effective_from: formData.effective_from || new Date().toISOString().split('T')[0]
      });
      setIsStructOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save salary structure');
    }
  };

  const handlePayslipSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/payroll/payslips', {
        employee_id: parseInt(formData.employee_id),
        month: parseInt(formData.month),
        year: parseInt(formData.year)
      });
      setIsPayslipOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate payslip');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading payroll management...</div>;

  return (
    <div className="animate-fade-in max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl mb-1">Payroll Management</h1>
          <p className="text-slate-500">Manage salary structures and generate payslips.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => { setFormData({}); setIsStructOpen(true); }} className="px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg font-medium transition-colors">
            + Set Salary Structure
          </button>
          <button onClick={() => { setFormData({}); setIsPayslipOpen(true); }} className="px-4 py-2 bg-emerald-600 text-white hover:bg-emerald-700 rounded-lg font-medium transition-colors">
            Generate Payslip
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden p-0">
          <div className="p-6 border-b border-slate-100 bg-slate-50">
            <h3 className="text-lg font-bold text-slate-800">Salary Structures</h3>
          </div>
          <div className="overflow-x-auto p-4">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-slate-500 uppercase">
                  <th className="pb-2">Emp ID</th>
                  <th className="pb-2">Basic</th>
                  <th className="pb-2">Allowances</th>
                  <th className="pb-2">Deductions</th>
                </tr>
              </thead>
              <tbody>
                {structures.map(s => (
                  <tr key={s.id} className="border-b last:border-0 hover:bg-slate-50">
                    <td className="py-2">#{s.employee_id}</td>
                    <td className="py-2">${s.basic_salary}</td>
                    <td className="py-2 text-emerald-600">${s.allowances}</td>
                    <td className="py-2 text-red-600">${s.deductions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden p-0">
          <div className="p-6 border-b border-slate-100 bg-slate-50">
            <h3 className="text-lg font-bold text-slate-800">Generated Payslips</h3>
          </div>
          <div className="overflow-x-auto p-4">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-slate-500 uppercase">
                  <th className="pb-2">Emp ID</th>
                  <th className="pb-2">Period</th>
                  <th className="pb-2">Net Pay</th>
                </tr>
              </thead>
              <tbody>
                {payslips.map(p => (
                  <tr key={p.id} className="border-b last:border-0 hover:bg-slate-50">
                    <td className="py-2">#{p.employee_id}</td>
                    <td className="py-2">{p.month}/{p.year}</td>
                    <td className="py-2 font-bold text-emerald-700">${p.net_salary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <Modal isOpen={isStructOpen} onClose={() => setIsStructOpen(false)} title="Set Salary Structure">
        <form onSubmit={handleStructureSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1">Employee</label>
            <select required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, employee_id: e.target.value})}>
              <option value="">Select Employee</option>
              {employees.map(e => <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Basic Salary</label>
            <input type="number" required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, basic_salary: e.target.value})} />
          </div>
          <div className="grid-2">
            <div>
              <label className="block text-sm font-semibold mb-1">Allowances</label>
              <input type="number" defaultValue="0" className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, allowances: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">Deductions</label>
              <input type="number" defaultValue="0" className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, deductions: e.target.value})} />
            </div>
          </div>
          <button type="submit" className="w-full bg-emerald-600 text-white p-2 rounded-lg mt-4">Save Structure</button>
        </form>
      </Modal>

      <Modal isOpen={isPayslipOpen} onClose={() => setIsPayslipOpen(false)} title="Generate Payslip">
        <form onSubmit={handlePayslipSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1">Employee</label>
            <select required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, employee_id: e.target.value})}>
              <option value="">Select Employee</option>
              {employees.map(e => <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>)}
            </select>
          </div>
          <div className="grid-2">
            <div>
              <label className="block text-sm font-semibold mb-1">Month (1-12)</label>
              <input type="number" min="1" max="12" required className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, month: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">Year</label>
              <input type="number" required defaultValue="2026" className="w-full p-2 border rounded-lg" onChange={e => setFormData({...formData, year: e.target.value})} />
            </div>
          </div>
          <button type="submit" className="w-full bg-emerald-600 text-white p-2 rounded-lg mt-4">Generate</button>
        </form>
      </Modal>
    </div>
  );
};
