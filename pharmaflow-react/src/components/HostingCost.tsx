import React from 'react';
import Button from './ui/Button';
import { HardDrive, Cloud, ShieldCheck } from 'lucide-react';

const HostingCost: React.FC = () => {
  return (
    <section id="hosting" className="py-24 bg-[#0D0D0D] border-t border-[#1A1A1A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">Hosting & Server Costs</h2>
          <p className="text-gray-400">Transparent pricing for your digital infrastructure.</p>
        </div>

        <div className="bg-[#1A1A1A] rounded-2xl border border-[#333] overflow-hidden soft-shadow">
             <div className="grid grid-cols-1 md:grid-cols-4">
                 {/* Current Plan Info */}
                 <div className="md:col-span-1 p-8 bg-[#202020] border-b md:border-b-0 md:border-r border-[#333]">
                     <div className="text-sm text-gray-400 mb-1 uppercase tracking-wide">Current Plan</div>
                     <div className="text-2xl font-bold text-white mb-4">Standard</div>
                     <div className="text-4xl font-bold text-[#00DFA2] mb-2">$99<span className="text-lg text-gray-500 font-normal">/mo</span></div>
                     <p className="text-xs text-gray-400 mb-6">Next billing date: Oct 24, 2024</p>
                     <Button fullWidth>Upgrade Plan</Button>
                 </div>

                 {/* Stats */}
                 <div className="md:col-span-3 p-8 grid grid-cols-1 sm:grid-cols-3 gap-8 items-center">
                     <div className="text-center sm:text-left">
                         <div className="flex items-center justify-center sm:justify-start mb-3">
                            <HardDrive className="text-blue-400 mr-2 h-5 w-5" />
                            <span className="font-semibold text-white">Storage</span>
                         </div>
                         <div className="text-2xl font-bold text-white mb-1">45%</div>
                         <div className="text-xs text-gray-500">225GB / 500GB Used</div>
                         <div className="w-full bg-[#333] h-1.5 mt-3 rounded-full overflow-hidden">
                             <div className="bg-blue-500 w-[45%] h-full"></div>
                         </div>
                     </div>

                     <div className="text-center sm:text-left">
                         <div className="flex items-center justify-center sm:justify-start mb-3">
                            <Cloud className="text-[#00DFA2] mr-2 h-5 w-5" />
                            <span className="font-semibold text-white">Bandwidth</span>
                         </div>
                         <div className="text-2xl font-bold text-white mb-1">12%</div>
                         <div className="text-xs text-gray-500">1.2TB / 10TB Used</div>
                         <div className="w-full bg-[#333] h-1.5 mt-3 rounded-full overflow-hidden">
                             <div className="bg-[#00DFA2] w-[12%] h-full"></div>
                         </div>
                     </div>

                      <div className="text-center sm:text-left">
                         <div className="flex items-center justify-center sm:justify-start mb-3">
                            <ShieldCheck className="text-purple-400 mr-2 h-5 w-5" />
                            <span className="font-semibold text-white">Security</span>
                         </div>
                         <div className="text-2xl font-bold text-white mb-1">Active</div>
                         <div className="text-xs text-gray-500">SSL + DDoS Protection</div>
                         <div className="flex items-center space-x-1 mt-3">
                             <div className="w-2 h-2 rounded-full bg-green-500"></div>
                             <span className="text-xs text-gray-400">Monitoring 24/7</span>
                         </div>
                     </div>
                 </div>
             </div>
        </div>
      </div>
    </section>
  );
};

export default HostingCost;