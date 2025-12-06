import React from 'react';
import { SAMPLE_PHARMACIES } from '../constants';
import Button from './ui/Button';
import { MapPin, User, ArrowUpRight } from 'lucide-react';

const PharmacyProfiles: React.FC = () => {
  return (
    <section className="py-24 bg-[#141414]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-end mb-12">
            <div>
                 <h2 className="text-3xl font-bold text-white mb-2">Registered Pharmacies</h2>
                 <p className="text-gray-400">View performance snapshots of your clinic network.</p>
            </div>
            <Button variant="outline" className="hidden sm:inline-flex">View All</Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {SAMPLE_PHARMACIES.map((pharmacy) => (
            <div key={pharmacy.id} className="bg-[#1A1A1A] border border-[#333] rounded-xl p-6 hover:shadow-lg hover:shadow-[#00DFA2]/10 transition-all group">
              <div className="flex justify-between items-start mb-6">
                <div>
                   <h3 className="text-lg font-bold text-white group-hover:text-[#00DFA2] transition-colors">{pharmacy.name}</h3>
                   <div className="flex items-center text-xs text-gray-500 mt-1">
                      <MapPin className="w-3 h-3 mr-1" /> {pharmacy.address}
                   </div>
                </div>
                <div className="bg-[#0D0D0D] p-2 rounded-lg border border-[#333]">
                    <User className="w-4 h-4 text-gray-400" />
                </div>
              </div>

              <div className="space-y-4 mb-6">
                 <div className="flex justify-between text-sm">
                     <span className="text-gray-400">Owner</span>
                     <span className="text-white">{pharmacy.owner}</span>
                 </div>
                 <div className="w-full h-px bg-[#333]"></div>
                 <div className="grid grid-cols-2 gap-4">
                     <div>
                         <div className="text-xs text-gray-500">Monthly Traffic</div>
                         <div className="font-semibold text-white">{pharmacy.traffic}</div>
                     </div>
                      <div>
                         <div className="text-xs text-gray-500">Revenue</div>
                         <div className="font-semibold text-[#00DFA2]">{pharmacy.revenue}</div>
                     </div>
                 </div>
                  <div className="grid grid-cols-2 gap-4">
                     <div>
                         <div className="text-xs text-gray-500">API Cost</div>
                         <div className="font-mono text-gray-300">{pharmacy.apiCost}</div>
                     </div>
                      <div>
                         <div className="text-xs text-gray-500">Hosting</div>
                         <div className="font-mono text-gray-300">{pharmacy.hostingCost}</div>
                     </div>
                 </div>
              </div>

              <Button fullWidth variant="secondary" className="text-sm">View Dashboard <ArrowUpRight className="ml-2 w-3 h-3" /></Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default PharmacyProfiles;