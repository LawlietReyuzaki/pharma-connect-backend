
import React from 'react';
import { PHARMACY_G_COSTS } from '../constants';
import { Globe, Database, Smartphone, CheckCircle, ExternalLink, Activity } from 'lucide-react';
import Button from './ui/Button';

const PharmacyDeployments: React.FC = () => {
  return (
    <section id="deployments" className="py-24 bg-[#0F0F0F]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Deployed Pharmacy Landing Pages</h2>
            <p className="text-gray-400 max-w-2xl">
                Each registered pharmacy receives a dedicated, auto-generated landing page and secure web application.
                Below is the live infrastructure status and cost analysis for our active deployments.
            </p>
        </div>

        <div className="space-y-12">
            {PHARMACY_G_COSTS.map((pharmacy) => (
                <div key={pharmacy.id} className="bg-[#1A1A1A] rounded-2xl border border-[#333] overflow-hidden soft-shadow">
                    
                    {/* Card Header */}
                    <div className="bg-[#202020] px-6 py-4 border-b border-[#333] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-[#0D0D0D] rounded-lg flex items-center justify-center border border-[#333]">
                                <Activity className="text-[#00DFA2] w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">{pharmacy.name}</h3>
                                <div className="flex items-center space-x-2 text-xs">
                                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                    <span className="text-green-500 font-medium">System Operational</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex space-x-3">
                            <Button variant="outline" className="text-xs h-9 px-4">Manage DB</Button>
                            <Button className="text-xs h-9 px-4">Visit App <ExternalLink className="w-3 h-3 ml-2" /></Button>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
                        
                        {/* Left Col: Landing Page Info */}
                        <div className="lg:col-span-5 p-8 border-b lg:border-b-0 lg:border-r border-[#333]">
                            <h4 className="text-sm uppercase tracking-wider text-gray-500 mb-6 font-semibold">Deployment Configuration</h4>
                            
                            <div className="space-y-6">
                                <div>
                                    <div className="flex items-center text-white mb-2 font-medium">
                                        <Globe className="w-4 h-4 text-[#00DFA2] mr-2" /> Custom Domain
                                    </div>
                                    <a href="#" className="text-sm text-blue-400 hover:text-blue-300 block pl-6">{pharmacy.domain}</a>
                                </div>

                                <div>
                                    <div className="flex items-center text-white mb-2 font-medium">
                                        <Smartphone className="w-4 h-4 text-[#00DFA2] mr-2" /> Web Application
                                    </div>
                                    <a href="#" className="text-sm text-blue-400 hover:text-blue-300 block pl-6">{pharmacy.webAppUrl}</a>
                                </div>

                                <div>
                                    <div className="flex items-center text-white mb-2 font-medium">
                                        <Database className="w-4 h-4 text-[#00DFA2] mr-2" /> Database Info
                                    </div>
                                    <p className="text-sm text-gray-400 pl-6">{pharmacy.databaseInfo}</p>
                                </div>

                                <div>
                                    <div className="text-white mb-3 font-medium flex items-center">
                                        <CheckCircle className="w-4 h-4 text-[#00DFA2] mr-2" /> Active Services
                                    </div>
                                    <div className="flex flex-wrap gap-2 pl-6">
                                        <span className="px-2 py-1 bg-[#0D0D0D] border border-[#333] rounded text-xs text-gray-300">AI Chatbot</span>
                                        <span className="px-2 py-1 bg-[#0D0D0D] border border-[#333] rounded text-xs text-gray-300">Inventory Sync</span>
                                        <span className="px-2 py-1 bg-[#0D0D0D] border border-[#333] rounded text-xs text-gray-300">Appointments</span>
                                        <span className="px-2 py-1 bg-[#0D0D0D] border border-[#333] rounded text-xs text-gray-300">Analytics</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Right Col: Cost Table */}
                        <div className="lg:col-span-7 bg-[#141414] p-8">
                            <div className="flex justify-between items-center mb-6">
                                <h4 className="text-sm uppercase tracking-wider text-gray-500 font-semibold">Infrastructure & Usage Costs (Monthly)</h4>
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border
                                    ${pharmacy.status === 'High Usage' ? 'bg-red-900/20 text-red-400 border-red-500/30' : 
                                      pharmacy.status === 'Low Usage' ? 'bg-green-900/20 text-green-400 border-green-500/30' : 
                                      'bg-gray-800 text-gray-400 border-gray-700'}`}>
                                    {pharmacy.status}
                                </span>
                            </div>

                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse text-sm">
                                    <thead>
                                        <tr className="text-gray-500 border-b border-[#333]">
                                            <th className="pb-3 font-medium">Metric</th>
                                            <th className="pb-3 font-medium text-right">Usage / Details</th>
                                            <th className="pb-3 font-medium text-right">Cost</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[#252525]">
                                        <tr>
                                            <td className="py-3 text-gray-300">Total API Calls</td>
                                            <td className="py-3 text-right text-gray-400 font-mono">{pharmacy.totalApiCalls.toLocaleString()}</td>
                                            <td className="py-3 text-right text-gray-300 font-mono">-</td>
                                        </tr>
                                        <tr>
                                            <td className="py-3 text-gray-300">Token Usage</td>
                                            <td className="py-3 text-right text-gray-400 font-mono">{pharmacy.tokenUsage}</td>
                                            <td className="py-3 text-right text-gray-300 font-mono">-</td>
                                        </tr>
                                        <tr>
                                            <td className="py-3 text-gray-300">Cloud Hosting</td>
                                            <td className="py-3 text-right text-gray-400">Standard Instance</td>
                                            <td className="py-3 text-right text-gray-300 font-mono">${pharmacy.hostingCost.toFixed(2)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-3 text-gray-300">AI Model Serving</td>
                                            <td className="py-3 text-right text-gray-400">Gemini 1.5 Flash</td>
                                            <td className="py-3 text-right text-gray-300 font-mono">${pharmacy.servingCost.toFixed(2)}</td>
                                        </tr>
                                        <tr>
                                            <td className="py-3 text-gray-300">Vector Storage</td>
                                            <td className="py-3 text-right text-gray-400">Log Retention (30 days)</td>
                                            <td className="py-3 text-right text-gray-300 font-mono">${pharmacy.storageCost.toFixed(2)}</td>
                                        </tr>
                                    </tbody>
                                    <tfoot>
                                        <tr className="border-t border-[#333]">
                                            <td className="pt-4 font-bold text-white">Total Monthly Cost</td>
                                            <td className="pt-4 text-right"></td>
                                            <td className="pt-4 text-right font-bold text-[#00DFA2] text-lg font-mono">${pharmacy.totalCost.toFixed(2)}</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
      </div>
    </section>
  );
};

export default PharmacyDeployments;
