import React from 'react';
import { Globe, Layout, ShieldCheck } from 'lucide-react';

const CustomDomain: React.FC = () => {
  return (
    <section id="custom-domain" className="py-24 bg-white border-y border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gray-50 rounded-2xl p-8 md:p-12 border border-gray-100 relative overflow-hidden soft-shadow">
            
            <div className="relative z-10 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                <div>
                    <h2 className="text-3xl font-bold text-[#0f2744] mb-6">Custom Domain Feature</h2>
                    <p className="text-gray-500 text-lg mb-8">
                        Each pharmacy gets its own sub-domain + web app + management dashboard.
                        Establish a professional online presence instantly.
                    </p>
                    
                    <ul className="space-y-4">
                        <li className="flex items-start">
                            <div className="p-1 bg-[#3B82F6]/10 rounded mr-3 mt-1">
                                <Globe className="w-5 h-5 text-[#3B82F6]" />
                            </div>
                            <div>
                                <h4 className="text-[#0f2744] font-medium">Custom Sub-domain</h4>
                                <p className="text-sm text-gray-500">pharmacy-name.platform.com</p>
                            </div>
                        </li>
                        <li className="flex items-start">
                            <div className="p-1 bg-[#3B82F6]/10 rounded mr-3 mt-1">
                                <Layout className="w-5 h-5 text-[#3B82F6]" />
                            </div>
                            <div>
                                <h4 className="text-[#0f2744] font-medium">Patient Web App</h4>
                                <p className="text-sm text-gray-500">Mobile-friendly booking & ordering interface</p>
                            </div>
                        </li>
                        <li className="flex items-start">
                            <div className="p-1 bg-[#3B82F6]/10 rounded mr-3 mt-1">
                                <ShieldCheck className="w-5 h-5 text-[#3B82F6]" />
                            </div>
                            <div>
                                <h4 className="text-[#0f2744] font-medium">Secure Admin Dashboard</h4>
                                <p className="text-sm text-gray-500">Manage everything from a secure panel</p>
                            </div>
                        </li>
                    </ul>
                </div>

                <div className="relative">
                    {/* Abstract Browser UI */}
                    <div className="bg-white rounded-xl border border-gray-200 shadow-2xl overflow-hidden transform rotate-1 hover:rotate-0 transition-transform duration-500">
                        <div className="bg-gray-100 px-4 py-3 border-b border-gray-200 flex items-center space-x-2">
                            <div className="flex space-x-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-400"></div>
                                <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                                <div className="w-3 h-3 rounded-full bg-green-400"></div>
                            </div>
                            <div className="ml-4 flex-1 bg-white border border-gray-200 rounded px-3 py-1 text-xs text-gray-500 font-mono">
                                https://your-pharmacy.pharma-platform.com
                            </div>
                        </div>
                        <div className="p-8 flex flex-col items-center justify-center min-h-[240px] text-center bg-white">
                             <div className="w-16 h-16 bg-gray-50 rounded-full mb-4 flex items-center justify-center border border-gray-100">
                                 <Globe className="w-8 h-8 text-[#3B82F6]" />
                             </div>
                             <h3 className="text-[#0f2744] font-bold text-lg mb-2">Your Pharmacy Name</h3>
                             <p className="text-gray-500 text-sm">Welcome to our digital storefront.</p>
                             <div className="mt-6 flex space-x-3 justify-center">
                                 <div className="h-2 w-20 bg-gray-100 rounded"></div>
                                 <div className="h-2 w-12 bg-gray-100 rounded"></div>
                             </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Decoration */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-[#1e3a5f]/5 rounded-full blur-[100px] pointer-events-none"></div>
        </div>
      </div>
    </section>
  );
};

export default CustomDomain;