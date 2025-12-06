import React from 'react';
import { Globe, Smartphone, Monitor } from 'lucide-react';

const TrafficAnalytics: React.FC = () => {
  return (
    <section className="py-24 bg-[#141414]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
             <h2 className="text-3xl font-bold text-white mb-2">Traffic Analytics</h2>
             <p className="text-gray-400">Deep dive into your patient demographics.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Stats */}
            <div className="lg:col-span-2 grid grid-cols-2 gap-4">
                <StatBox label="Daily Traffic" value="1,240" sub="+5.4%" />
                <StatBox label="Monthly Traffic" value="38.5k" sub="+12.1%" />
                <StatBox label="Unique Visitors" value="24.2k" sub="+8.2%" />
                <StatBox label="Returning" value="14.3k" sub="+15.3%" />
                
                {/* Geo Map Placeholder */}
                <div className="col-span-2 bg-[#1A1A1A] border border-[#333] rounded-xl p-6 h-64 relative overflow-hidden flex items-center justify-center">
                    <Globe className="text-[#333] w-48 h-48 absolute opacity-20" />
                    <div className="z-10 text-center">
                        <div className="text-sm text-gray-400 mb-2">Top Region</div>
                        <div className="text-2xl font-bold text-white">North America</div>
                        <div className="text-xs text-[#00DFA2]">65% of traffic</div>
                    </div>
                    {/* Fake dots */}
                    <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-[#00DFA2] rounded-full animate-ping"></div>
                    <div className="absolute bottom-1/3 right-1/3 w-2 h-2 bg-[#00DFA2] rounded-full animate-ping delay-75"></div>
                    <div className="absolute top-1/2 right-1/4 w-2 h-2 bg-[#00DFA2] rounded-full animate-ping delay-150"></div>
                </div>
            </div>

            {/* Device Stats */}
            <div className="bg-[#1A1A1A] border border-[#333] rounded-xl p-8 flex flex-col justify-center">
                <h3 className="text-lg font-bold text-white mb-8">Device Usage</h3>
                
                <div className="space-y-8">
                    <div>
                        <div className="flex items-center justify-between mb-2 text-sm text-gray-300">
                             <div className="flex items-center"><Smartphone className="w-4 h-4 mr-2" /> Mobile</div>
                             <span>72%</span>
                        </div>
                        <div className="w-full h-2 bg-[#333] rounded-full overflow-hidden">
                            <div className="h-full bg-[#00DFA2] w-[72%]"></div>
                        </div>
                    </div>

                    <div>
                        <div className="flex items-center justify-between mb-2 text-sm text-gray-300">
                             <div className="flex items-center"><Monitor className="w-4 h-4 mr-2" /> Desktop</div>
                             <span>28%</span>
                        </div>
                        <div className="w-full h-2 bg-[#333] rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 w-[28%]"></div>
                        </div>
                    </div>
                </div>

                <div className="mt-12 p-4 bg-[#0D0D0D] rounded-lg border border-[#333]">
                    <div className="text-xs text-gray-500 mb-1">Analysis</div>
                    <p className="text-sm text-gray-300">Most patients book appointments via mobile devices. Optimize your profile for mobile views.</p>
                </div>
            </div>
        </div>
      </div>
    </section>
  );
};

const StatBox = ({ label, value, sub }: { label: string, value: string, sub: string }) => (
    <div className="bg-[#1A1A1A] border border-[#333] rounded-xl p-6">
        <div className="text-sm text-gray-400 mb-2">{label}</div>
        <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">{value}</span>
            <span className="text-xs text-[#00DFA2] bg-[#00DFA2]/10 px-1.5 py-0.5 rounded">{sub}</span>
        </div>
    </div>
);

export default TrafficAnalytics;