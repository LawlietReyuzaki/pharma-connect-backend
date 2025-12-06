import React from 'react';
import Button from './ui/Button';
import { Check } from 'lucide-react';
import { Page } from '../types';

interface PricingProps {
    onNavigate?: (page: Page) => void;
}

const Pricing: React.FC<PricingProps> = ({ onNavigate }) => {
  return (
    <section id="pricing" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-[#0f2744] mb-4">Simple Pricing</h2>
          <p className="text-gray-500">Transparent costs. No hidden fees.</p>
        </div>

        <div className="max-w-lg mx-auto bg-white rounded-2xl border border-gray-200 overflow-hidden soft-shadow relative card-hover">
           <div className="absolute top-0 inset-x-0 h-1 bg-[#1e3a5f]"></div>
           <div className="p-8 text-center border-b border-gray-100">
               <h3 className="text-xl font-bold text-[#0f2744] mb-2">Platform Access</h3>
               <div className="text-5xl font-bold text-[#3B82F6] mb-2">$XX<span className="text-lg text-gray-400 font-normal">/mo</span></div>
               <p className="text-sm text-gray-400">Placeholder Pricing</p>
           </div>
           
           <div className="p-8">
               <ul className="space-y-4 mb-8">
                   <li className="flex items-center text-gray-600 text-sm">
                       <Check className="w-5 h-5 text-[#3B82F6] mr-3" /> All Features Included
                   </li>
                   <li className="flex items-center text-gray-600 text-sm">
                       <Check className="w-5 h-5 text-[#3B82F6] mr-3" /> Unlimited Doctors
                   </li>
                   <li className="flex items-center text-gray-600 text-sm">
                       <Check className="w-5 h-5 text-[#3B82F6] mr-3" /> AI Chatbot Integration
                   </li>
                   <li className="flex items-center text-gray-600 text-sm">
                       <Check className="w-5 h-5 text-[#3B82F6] mr-3" /> Custom Sub-domain
                   </li>
               </ul>
               <Button fullWidth onClick={() => onNavigate && onNavigate('register')} className="shadow-lg shadow-[#1e3a5f]/20">
                   Get Started
               </Button>
           </div>
        </div>
      </div>
    </section>
  );
};

export default Pricing;