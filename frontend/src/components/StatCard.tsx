import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: any;
  color?: 'sage' | 'terracotta' | 'ochre';
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, color = 'sage' }) => {
  let iconBg = '';
  let iconColor = '';
  let valColor = '';

  if (color === 'sage') {
    iconBg = 'var(--color-bg)';
    iconColor = 'var(--color-primary-light)';
    valColor = 'var(--color-primary)';
  } else if (color === 'terracotta') {
    iconBg = 'var(--status-danger-bg)';
    iconColor = 'var(--status-danger)';
    valColor = 'var(--color-primary)';
  } else if (color === 'ochre') {
    iconBg = 'var(--status-warning-bg)';
    iconColor = 'var(--status-warning)';
    valColor = 'var(--color-primary)';
  }

  return (
    <div className="glass-card flex items-center gap-4 p-4 border bg-white shadow-sm hover:shadow-md transition-shadow rounded-xl">
      <div 
        className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
        style={{ backgroundColor: iconBg, color: iconColor }}
      >
        <Icon size={24} />
      </div>
      <div>
        <div className="text-2xl font-bold leading-none mb-1" style={{ color: valColor, fontFamily: 'Outfit' }}>{value}</div>
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{title}</div>
      </div>
    </div>
  );
};
