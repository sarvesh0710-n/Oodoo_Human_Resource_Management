import React from 'react';

type StatusType = 'Present' | 'Absent' | 'Leave' | 'Half Day' | 'Pending' | 'Approved' | 'Rejected' | 'present' | 'absent' | 'leave' | 'half_day' | 'pending' | 'approved' | 'rejected';

interface StatusBadgeProps {
  status: StatusType;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const s = status.toLowerCase();
  
  let bg = 'bg-slate-100';
  let text = 'text-slate-700';
  let border = 'border-slate-200';
  
  if (s === 'present' || s === 'approved') {
    bg = 'bg-emerald-100'; text = 'text-emerald-800'; border = 'border-emerald-200';
  } else if (s === 'absent' || s === 'rejected') {
    bg = 'bg-red-100'; text = 'text-red-800'; border = 'border-red-200';
  } else if (s === 'leave' || s === 'on leave') {
    bg = 'bg-sky-100'; text = 'text-sky-800'; border = 'border-sky-200';
  } else if (s === 'pending') {
    bg = 'bg-amber-100'; text = 'text-amber-800'; border = 'border-amber-200';
  } else if (s === 'half_day' || s === 'half day') {
    bg = 'bg-purple-100'; text = 'text-purple-800'; border = 'border-purple-200';
  }

  // Capitalize first letter
  const displayStatus = status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ');

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold border ${bg} ${text} ${border}`}>
      <span className={`w-1.5 h-1.5 rounded-full`} style={{ backgroundColor: 'currentColor' }}></span>
      {displayStatus}
    </span>
  );
};
