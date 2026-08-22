import React, { useEffect, useState } from 'react';
import { getMyProfile } from '../lib/auth';
import type { Employee } from '../lib/types';
import api from '../lib/api';
import { User, Phone, MapPin, Briefcase, Calendar } from 'lucide-react';

export const Profile: React.FC = () => {
  const [profile, setProfile] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<any>({});

  const fetchProfile = async () => {
    try {
      const data = await getMyProfile();
      setProfile(data);
      setFormData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.patch('/employees/me', {
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
        address: formData.address
      });
      setIsEditing(false);
      fetchProfile();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update profile');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading profile...</div>;
  if (!profile) return <div className="p-8 text-center text-red-500">Failed to load profile.</div>;

  return (
    <div className="animate-fade-in max-w-4xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl mb-1">My Profile</h1>
        <p className="text-slate-500">Manage your personal information.</p>
      </div>

      <div className="glass-card bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden p-0">
        <div className="h-32 bg-emerald-600 relative">
          <div className="absolute -bottom-12 left-8 w-24 h-24 rounded-full border-4 border-white bg-slate-100 flex items-center justify-center shadow-md">
            <User size={40} className="text-slate-400" />
          </div>
        </div>
        
        <div className="pt-16 p-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-800">{profile.first_name} {profile.last_name}</h2>
              <p className="text-slate-500 flex items-center gap-2 mt-1">
                <Briefcase size={16} /> {profile.job_title || 'Employee'}
              </p>
            </div>
            <button 
              onClick={() => setIsEditing(!isEditing)}
              className="px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg font-medium transition-colors"
            >
              {isEditing ? 'Cancel Edit' : 'Edit Profile'}
            </button>
          </div>

          {isEditing ? (
            <form onSubmit={handleUpdate} className="space-y-4 max-w-lg mt-8 border-t pt-8">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold mb-1">First Name</label>
                  <input type="text" required className="w-full p-2 border rounded-lg" value={formData.first_name || ''} onChange={e => setFormData({...formData, first_name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-semibold mb-1">Last Name</label>
                  <input type="text" required className="w-full p-2 border rounded-lg" value={formData.last_name || ''} onChange={e => setFormData({...formData, last_name: e.target.value})} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Phone</label>
                <input type="text" className="w-full p-2 border rounded-lg" value={formData.phone || ''} onChange={e => setFormData({...formData, phone: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Address</label>
                <textarea rows={3} className="w-full p-2 border rounded-lg" value={formData.address || ''} onChange={e => setFormData({...formData, address: e.target.value})}></textarea>
              </div>
              <button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-6 rounded-lg transition-colors">
                Save Changes
              </button>
            </form>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8 border-t pt-8">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded bg-slate-50 flex items-center justify-center text-slate-500 shrink-0"><Phone size={16} /></div>
                  <div>
                    <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Phone</div>
                    <div className="text-slate-700">{profile.phone || 'Not provided'}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded bg-slate-50 flex items-center justify-center text-slate-500 shrink-0"><MapPin size={16} /></div>
                  <div>
                    <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Address</div>
                    <div className="text-slate-700 max-w-xs">{profile.address || 'Not provided'}</div>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded bg-slate-50 flex items-center justify-center text-slate-500 shrink-0"><Calendar size={16} /></div>
                  <div>
                    <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Joining Date</div>
                    <div className="text-slate-700">{new Date(profile.joining_date).toLocaleDateString()}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
