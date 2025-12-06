
import React from 'react';
import { PHARMACY_G_COSTS } from '../constants';
import { Server, Database, CloudLightning, Activity } from 'lucide-react';

const GCostTable: React.FC = () => {
  // Calculate totals
  const totalApiCalls = PHARMACY_G_COSTS.reduce((acc, curr) => acc + curr.totalApiCalls, 0);
  const totalHosting = PHARMACY_G_COSTS.reduce((acc, curr) => acc + curr.hostingCost, 0);
  const totalServing = PHARMACY_G_COSTS.reduce((acc, curr) => acc + curr.servingCost, 0);
  const totalStorage = PHARMACY_G_COSTS.reduce((acc, curr) => acc + curr.storageCost, 0);
  const totalFinal = PHARMACY_G_COSTS.reduce((acc, curr) => acc + curr.totalCost, 0);

  return (
    <section id="g-costs" className="py-24 bg-[#0F0F0F]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
            <h2 className="text-3xl font-bold text-white mb-2">Infrastructure Cost Breakdown (G-Cost)</h2>
            <p className="text-gray-400">Detailed monthly analysis of Serving, Hosting, and Token consumption per pharmacy.</p>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-[#1A1A1A] p-4 rounded-lg border border-[#333]">
                <div className="flex items-center space-x-2 text-gray-400 mb-1">
                    <CloudLightning className="w-4 h-4 text-[#00DFA2]" />
                    <span className="text-xs uppercase tracking-wider">Total Serving</span>
                </div>
                <div className="text-2xl font-bold text-white">${totalServing.toFixed(2)}</div>
            </div>
             <div className="bg-[#1A1A1A] p-4 rounded-lg border border-[#333]">
                <div className="flex items-center space-x-2 text-gray-400 mb-1">
                    <Server className="w-4 h-4 text-blue-400" />
                    <span className="text-xs uppercase tracking-wider">Total Hosting</span>
                </div>
                <div className="text-2xl font-bold text-white">${totalHosting.toFixed(2)}</div>
            </div>
             <div className="bg-[#1A1A1A] p-4 rounded-lg border border-[#333]">
                <div className="flex items-center space-x-2 text-gray-400 mb-1">
                    <Database className="w-4 h-4 text-purple-400" />
                    <span className="text-xs uppercase tracking-wider">Total Storage</span>
                </div>
                <div className="text-2xl font-bold text-white">${totalStorage.toFixed(2)}</div>
            </div>
            <div className="bg-[#1A1A1A] p-4 rounded-lg border border-[#333]">
                <div className="flex items-center space-x-2 text-gray-400 mb-1">
                    <Activity className="w-4 h-4 text-yellow-400" />
                    <span className="text-xs uppercase tracking-wider">Total API Calls</span>
                </div>
                <div className="text-2xl font-bold text-white">{(totalApiCalls / 1000).toFixed(1)}k</div>
            </div>
        </div>

        {/* Table Container */}
        <div className="bg-[#1A1A1A] rounded-xl border border-[#333] overflow-hidden soft-shadow">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#0A0A0A] text-gray-400 text-xs uppercase tracking-wider border-b border-[#333]">
                  <th className="p-4 font-semibold">Pharmacy Name</th>
                  <th className="p-4 font-semibold">API Calls (Mo)</th>
                  <th className="p-4 font-semibold">Token Usage</th>
                  <th className="p-4 font-semibold text-right">Hosting</th>
                  <th className="p-4 font-semibold text-right">Serving</th>
                  <th className="p-4 font-semibold text-right">Storage</th>
                  <th className="p-4 font-semibold text-right text-white">Total Cost</th>
                  <th className="p-4 font-semibold text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#333]">
                {PHARMACY_G_COSTS.map((pharmacy) => (
                  <tr key={pharmacy.id} className="hover:bg-[#252525] transition-colors group">
                    <td className="p-4">
                        <div className="font-medium text-white group-hover:text-[#00DFA2] transition-colors">{pharmacy.name}</div>
                        <div className="text-xs text-gray-500">{pharmacy.mau} MAU • {pharmacy.dailyApiCalls} calls/day</div>
                    </td>
                    <td className="p-4 text-gray-300 font-mono">{pharmacy.totalApiCalls.toLocaleString()}</td>
                    <td className="p-4 text-gray-300 font-mono">{pharmacy.tokenUsage}</td>
                    <td className="p-4 text-right text-gray-400 font-mono">${pharmacy.hostingCost.toFixed(2)}</td>
                    <td className="p-4 text-right text-gray-400 font-mono">${pharmacy.servingCost.toFixed(2)}</td>
                    <td className="p-4 text-right text-gray-400 font-mono">${pharmacy.storageCost.toFixed(2)}</td>
                    <td className="p-4 text-right font-bold text-[#00DFA2] font-mono">${pharmacy.totalCost.toFixed(2)}</td>
                    <td className="p-4 text-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border
                            ${pharmacy.status === 'High Usage' ? 'bg-red-900/20 text-red-400 border-red-500/30' : 
                              pharmacy.status === 'Low Usage' ? 'bg-green-900/20 text-green-400 border-green-500/30' : 
                              'bg-gray-800 text-gray-400 border-gray-700'}`}>
                            {pharmacy.status}
                        </span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-[#202020] border-t-2 border-[#333]">
                <tr>
                    <td className="p-4 font-bold text-white uppercase text-sm">Total Sum</td>
                    <td className="p-4 font-bold text-white font-mono">{totalApiCalls.toLocaleString()}</td>
                    <td className="p-4 text-gray-500 italic">--</td>
                    <td className="p-4 text-right font-bold text-white font-mono">${totalHosting.toFixed(2)}</td>
                    <td className="p-4 text-right font-bold text-white font-mono">${totalServing.toFixed(2)}</td>
                    <td className="p-4 text-right font-bold text-white font-mono">${totalStorage.toFixed(2)}</td>
                    <td className="p-4 text-right font-bold text-[#00DFA2] text-lg font-mono">${totalFinal.toFixed(2)}</td>
                    <td className="p-4"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
        
        <div className="mt-4 text-xs text-gray-500 text-right">
            * Costs calculated based on Google Cloud & AI Studio pricing models. Data updated every 24 hours.
        </div>
      </div>
    </section>
  );
};

export default GCostTable;
