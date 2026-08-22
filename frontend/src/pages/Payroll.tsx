import React, { useEffect, useState } from 'react';
import { Payslip } from '../lib/types';
import api from '../lib/api';
import { FileText, Download } from 'lucide-react';

export const Payroll: React.FC = () => {
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPayslips = async () => {
      try {
        const res = await api.get<Payslip[]>('/payroll/payslips');
        setPayslips(res.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPayslips();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading your payslips...</div>;

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl mb-1">My Payslips</h1>
        <p className="text-slate-500">View and download your monthly salary slips.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {payslips.length === 0 ? (
          <div className="col-span-full p-8 text-center bg-slate-50 border border-slate-200 border-dashed rounded-xl text-slate-500">
            No payslips available yet.
          </div>
        ) : (
          payslips.map(ps => (
            <div key={ps.id} className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col h-full hover:border-emerald-200 transition-colors">
              <div className="flex justify-between items-start mb-6 pb-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <FileText size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">{monthNames[ps.month - 1]} {ps.year}</h3>
                    <p className="text-xs text-slate-500">Generated {new Date(ps.generated_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>

              <div className="flex-1 space-y-3 mb-6">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Basic Salary</span>
                  <span className="font-medium text-slate-700">${ps.basic_salary.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Allowances</span>
                  <span className="font-medium text-emerald-600">+${ps.allowances.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Deductions</span>
                  <span className="font-medium text-red-600">-${ps.deductions.toFixed(2)}</span>
                </div>
                <div className="pt-3 mt-3 border-t border-slate-100 flex justify-between">
                  <span className="font-bold text-slate-800">Net Pay</span>
                  <span className="font-bold text-emerald-700">${ps.net_salary.toFixed(2)}</span>
                </div>
              </div>

              <button className="w-full mt-auto flex items-center justify-center gap-2 py-2 bg-slate-50 hover:bg-emerald-50 text-slate-600 hover:text-emerald-700 border border-slate-200 hover:border-emerald-200 rounded-lg transition-colors text-sm font-medium">
                <Download size={16} />
                Download PDF
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
