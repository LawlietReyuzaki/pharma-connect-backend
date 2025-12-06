import React, { useState } from 'react';
import Button from './ui/Button';
import { CheckCircle } from 'lucide-react';

const RegistrationModule: React.FC = () => {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <section id="register" className="py-24 bg-[#0D0D0D]">
        <div className="max-w-md mx-auto px-4">
          <div className="bg-[#1A1A1A] border border-[#00DFA2] rounded-2xl p-8 text-center soft-shadow">
            <div className="mx-auto w-16 h-16 bg-[#00DFA2]/20 rounded-full flex items-center justify-center mb-6">
              <CheckCircle className="h-8 w-8 text-[#00DFA2]" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Registration Complete</h3>
            <p className="text-gray-400 mb-6">
              Your pharmacy has been registered successfully. Our team will contact you via WhatsApp shortly to finalize the setup.
            </p>
            <Button onClick={() => setSubmitted(false)} variant="outline">Register Another</Button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="register" className="py-24 bg-[#0D0D0D]">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">Register Your Pharmacy</h2>
          <p className="text-gray-400">Join thousands of healthcare providers using our platform.</p>
        </div>

        <div className="bg-[#1A1A1A] rounded-2xl border border-[#333] p-8 md:p-10 soft-shadow">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Pharmacy Name</label>
                <input required type="text" className="w-full bg-[#0D0D0D] border border-[#333] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#00DFA2] transition-colors" placeholder="e.g. City Care Pharmacy" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Owner Name</label>
                <input required type="text" className="w-full bg-[#0D0D0D] border border-[#333] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#00DFA2] transition-colors" placeholder="Full Name" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Address</label>
              <input required type="text" className="w-full bg-[#0D0D0D] border border-[#333] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#00DFA2] transition-colors" placeholder="Street Address, City, Zip" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">WhatsApp Number</label>
                <input required type="tel" className="w-full bg-[#0D0D0D] border border-[#333] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#00DFA2] transition-colors" placeholder="+1 (555) 000-0000" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Hosting Plan</label>
                <select className="w-full bg-[#0D0D0D] border border-[#333] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#00DFA2] transition-colors appearance-none">
                  <option>Basic ($49/mo)</option>
                  <option>Standard ($99/mo)</option>
                  <option>Pro ($199/mo)</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-6 pt-2">
               <label className="flex items-center space-x-3 cursor-pointer group">
                  <input type="checkbox" className="w-5 h-5 rounded border-gray-600 text-[#00DFA2] focus:ring-[#00DFA2] bg-[#0D0D0D]" />
                  <span className="text-gray-300 group-hover:text-white">Need Clinic Setup?</span>
               </label>
               <label className="flex items-center space-x-3 cursor-pointer group">
                  <input type="checkbox" className="w-5 h-5 rounded border-gray-600 text-[#00DFA2] focus:ring-[#00DFA2] bg-[#0D0D0D]" />
                  <span className="text-gray-300 group-hover:text-white">Add Doctors?</span>
               </label>
            </div>

            <div className="pt-4">
              <Button type="submit" fullWidth>Complete Registration</Button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
};

export default RegistrationModule;