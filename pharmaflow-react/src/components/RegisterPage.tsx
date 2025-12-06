import React from 'react';
import Button from './ui/Button';
import { Activity, ArrowLeft } from 'lucide-react';
import { Page } from '../types';

interface RegisterPageProps {
    onNavigate: (page: Page) => void;
}

const RegisterPage: React.FC<RegisterPageProps> = ({ onNavigate }) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert("Registration Successful! Redirecting to your pharmacy dashboard...");
    // Redirect to the Flask app (Red Dot Pharmacy) admin dashboard after registration
    window.location.href = '/admin';
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Minimal Header */}
      <div className="bg-white border-b border-gray-200 py-4 px-6 flex justify-between items-center">
         <div className="flex items-center space-x-2 cursor-pointer" onClick={() => onNavigate('landing')}>
            <Activity className="h-6 w-6 text-[#1e3a5f]" />
            <span className="text-xl font-bold tracking-tight text-[#0f2744]">
              Pharma<span className="text-[#3B82F6]">Platform</span>
            </span>
          </div>
          <button onClick={() => onNavigate('landing')} className="text-sm text-gray-500 hover:text-[#0f2744] flex items-center transition-colors">
              <ArrowLeft className="w-4 h-4 mr-1" /> Back to Home
          </button>
      </div>

      <div className="flex-grow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl w-full space-y-8 bg-white p-10 rounded-2xl soft-shadow border border-gray-100">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-[#0f2744]">Register Your Pharmacy</h2>
            <p className="mt-2 text-sm text-gray-600">
              Create your account to start managing your pharmacy digitally.
            </p>
          </div>
          
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm space-y-4">
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Pharmacy Name</label>
                    <input name="pharmacyName" type="text" required className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-[#3B82F6] focus:border-[#3B82F6] sm:text-sm transition-all" placeholder="e.g. HealthFirst Pharmacy" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Owner Name</label>
                    <input name="ownerName" type="text" required className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-[#3B82F6] focus:border-[#3B82F6] sm:text-sm transition-all" placeholder="Full Name" />
                  </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
                <input name="email" type="email" required className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-[#3B82F6] focus:border-[#3B82F6] sm:text-sm transition-all" placeholder="admin@pharmacy.com" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                <input name="phone" type="tel" required className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-[#3B82F6] focus:border-[#3B82F6] sm:text-sm transition-all" placeholder="+1 (555) 000-0000" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <input name="address" type="text" required className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-[#3B82F6] focus:border-[#3B82F6] sm:text-sm transition-all" placeholder="Street Address, City, Zip" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input name="password" type="password" required className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-[#3B82F6] focus:border-[#3B82F6] sm:text-sm transition-all" placeholder="••••••••" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
                    <input name="confirmPassword" type="password" required className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-[#3B82F6] focus:border-[#3B82F6] sm:text-sm transition-all" placeholder="••••••••" />
                  </div>
              </div>

            </div>

            <div>
              <Button type="submit" fullWidth className="shadow-lg shadow-[#1e3a5f]/20">
                Register Pharmacy
              </Button>
            </div>
            
            <div className="text-center text-sm text-gray-500">
                By registering, you agree to our Terms of Service and Privacy Policy.
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;