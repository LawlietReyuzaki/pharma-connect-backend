import React from 'react';
import { STEPS } from '../constants';

const HowItWorks: React.FC = () => {
  return (
    <section className="py-24 bg-[#0F0F0F] border-t border-[#1A1A1A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">How It Works</h2>
          <p className="text-gray-400">Seamless integration into your existing workflow.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative">
            {/* Connector Line for Desktop */}
            <div className="hidden lg:block absolute top-12 left-0 w-full h-0.5 bg-[#333] -z-0"></div>

            {STEPS.map((step, index) => (
            <div key={step.id} className="relative z-10 flex flex-col items-center text-center">
                <div className="w-24 h-24 bg-[#1A1A1A] rounded-full border-4 border-[#0F0F0F] flex items-center justify-center mb-6 shadow-lg shadow-[#00C78E]/5">
                <span className="text-2xl font-bold text-[#00C78E]">{step.id}</span>
                </div>
                <h3 className="text-lg font-medium text-white mb-2">{step.title}</h3>
                <p className="text-sm text-gray-400 max-w-xs">{step.description}</p>
            </div>
            ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;