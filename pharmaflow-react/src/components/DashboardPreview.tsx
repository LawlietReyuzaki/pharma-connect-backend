import React from 'react';
import { DollarSign, Users, Server, Box, Activity, Star, Calendar } from 'lucide-react';

const DashboardPreview: React.FC = () => {
  return (
    <section id="dashboard" className="py-24 bg-[#141414]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
            <h2 className="text-3xl font-bold text-white mb-2">Admin Dashboard</h2>
            <p className="text-gray-400">Real-time overview of your pharmacy performance.</p>
        </div>

        {/* Dashboard Container */}
        <div className="bg-[#0D0D0D] border border-[#333] rounded-xl p-6 shadow-2xl overflow-hidden">
            {/* Top Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <Card title="Revenue" value="$24,500" icon={<DollarSign className="text-[#00DFA2]" />} sub="Success" change="+12%" />
                <Card title="Appointments" value="142" icon={<Calendar className="text-blue-400" />} sub="Total" change="+5%" />
                <Card title="Traffic" value="8.4k" icon={<Activity className="text-purple-400" />} sub="Monthly" change="+18%" />
                <Card title="Rating" value="4.9" icon={<Star className="text-yellow-400" />} sub="Average" change="0%" />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Main Chart Area (Fake) */}
                <div className="lg:col-span-2 bg-[#1A1A1A] rounded-lg border border-[#333] p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-lg font-semibold text-white">Revenue Analytics</h3>
                        <div className="flex space-x-2">
                             <div className="w-3 h-3 rounded-full bg-[#00DFA2]"></div>
                             <span className="text-xs text-gray-400">Income</span>
                        </div>
                    </div>
                    {/* Fake Chart Visualization */}
                    <div className="h-64 flex items-end justify-between space-x-2 px-2">
                        {[40, 65, 45, 80, 55, 90, 70, 85, 60, 75, 50, 95].map((h, i) => (
                            <div key={i} className="w-full bg-[#00DFA2]/20 hover:bg-[#00DFA2]/40 transition-all rounded-t-sm relative group" style={{ height: `${h}%` }}>
                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-[#333] text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                                    ${h}00
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="flex justify-between mt-4 text-xs text-gray-500">
                        <span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span>
                        <span>Jul</span><span>Aug</span><span>Sep</span><span>Oct</span><span>Nov</span><span>Dec</span>
                    </div>
                </div>

                {/* Side Cards */}
                <div className="space-y-6">
                    {/* Hosting Status */}
                    <div className="bg-[#1A1A1A] rounded-lg border border-[#333] p-6">
                         <div className="flex items-center justify-between mb-4">
                            <h4 className="text-sm font-medium text-gray-300">Hosting Status</h4>
                            <Server className="h-4 w-4 text-gray-500" />
                         </div>
                         <div className="text-2xl font-bold text-white mb-1">$49.00</div>
                         <div className="text-xs text-gray-500 mb-4">Standard Plan / Monthly</div>
                         <div className="w-full bg-[#333] h-1.5 rounded-full overflow-hidden">
                             <div className="bg-[#00DFA2] h-full w-[45%]"></div>
                         </div>
                         <div className="mt-2 text-xs text-gray-400 flex justify-between">
                             <span>24GB Used</span>
                             <span>100GB Total</span>
                         </div>
                    </div>

                    {/* API Usage */}
                    <div className="bg-[#1A1A1A] rounded-lg border border-[#333] p-6">
                         <div className="flex items-center justify-between mb-4">
                            <h4 className="text-sm font-medium text-gray-300">API Usage</h4>
                            <Box className="h-4 w-4 text-gray-500" />
                         </div>
                         <div className="space-y-3">
                             <div>
                                 <div className="flex justify-between text-xs text-gray-400 mb-1">
                                     <span>Chatbot Requests</span>
                                     <span>85%</span>
                                 </div>
                                 <div className="w-full bg-[#333] h-1.5 rounded-full overflow-hidden">
                                     <div className="bg-blue-500 h-full w-[85%]"></div>
                                 </div>
                             </div>
                             <div>
                                 <div className="flex justify-between text-xs text-gray-400 mb-1">
                                     <span>Inventory Sync</span>
                                     <span>32%</span>
                                 </div>
                                 <div className="w-full bg-[#333] h-1.5 rounded-full overflow-hidden">
                                     <div className="bg-purple-500 h-full w-[32%]"></div>
                                 </div>
                             </div>
                         </div>
                    </div>

                    {/* Doctors Count */}
                    <div className="bg-[#1A1A1A] rounded-lg border border-[#333] p-6 flex items-center justify-between">
                        <div>
                            <div className="text-sm text-gray-400">Registered Doctors</div>
                            <div className="text-2xl font-bold text-white">12</div>
                        </div>
                        <div className="h-10 w-10 bg-[#333] rounded-full flex items-center justify-center">
                            <Users className="h-5 w-5 text-white" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </section>
  );
};

const Card = ({ title, value, icon, sub, change }: { title: string, value: string, icon: any, sub: string, change: string }) => (
    <div className="bg-[#1A1A1A] p-5 rounded-lg border border-[#333]">
        <div className="flex justify-between items-start mb-4">
            <div className="bg-[#0D0D0D] p-2 rounded-md">{icon}</div>
            <span className={`text-xs px-2 py-1 rounded ${change.includes('+') ? 'bg-green-900/30 text-[#00DFA2]' : 'bg-gray-800 text-gray-400'}`}>{change}</span>
        </div>
        <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">{title}</div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-xs text-gray-500 mt-1">{sub}</div>
    </div>
);

export default DashboardPreview;