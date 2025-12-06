import React, { useState } from 'react';
import Button from './ui/Button';
import { Lock, ArrowLeft } from 'lucide-react';
import { Page } from '../types';

interface SuperAdminLoginProps {
    onNavigate: (page: Page) => void;
}

const SuperAdminLogin: React.FC<SuperAdminLoginProps> = ({ onNavigate }) => {
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if(password) {
        onNavigate('admin-dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
       
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
        <div className="flex justify-start mb-6">
             <button onClick={() => onNavigate('landing')} className="text-sm text-gray-400 hover:text-gray-600 flex items-center">
                  <ArrowLeft className="w-4 h-4 mr-1" /> Back
             </button>
        </div>

        <div className="text-center mb-8">
            <div className="w-16 h-16 bg-[#1e3a5f]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lock className="w-8 h-8 text-[#1e3a5f]" />
            </div>
            <h2 className="text-2xl font-bold text-[#0f2744]">Super Admin Access</h2>
            <p className="text-gray-500 text-sm mt-1">Restricted area. Authorized personnel only.</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Admin Password</label>
                <input 
                    type="password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-[#1e3a5f] focus:border-[#1e3a5f] outline-none transition-all"
                    placeholder="Enter secure password"
                />
            </div>
            <Button type="submit" fullWidth className="bg-[#1e3a5f] text-white hover:bg-[#0f2744]">
                Enter Panel
            </Button>
        </form>
      </div>
    </div>
  );
};

export default SuperAdminLogin;