import React from 'react';
import Button from './ui/Button';
import { ArrowRight, CheckCircle } from 'lucide-react';
import { Page } from '../types';

interface HeroProps {
  onNavigate: (page: Page) => void;
}

const Hero: React.FC<HeroProps> = ({ onNavigate }) => {
  return (
    <section id="hero" className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-[#0f2744] mb-6 leading-tight">
              Pharmacy Management <br/>
              <span className="text-[#3B82F6]">Platform</span>
            </h1>
            
            <p className="text-lg md:text-xl text-gray-500 mb-10 max-w-2xl mx-auto leading-relaxed">
              Register your pharmacy and manage medicines, doctors, chatbot & appointments.
              The complete digital solution for modern healthcare.
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center items-center gap-4">
              <Button className="px-8 py-4 text-lg shadow-xl shadow-[#1e3a5f]/20" onClick={() => onNavigate('register')}>
                Register Pharmacy <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>

            <div className="mt-12 flex flex-wrap justify-center gap-6 text-sm text-gray-500">
                <div className="flex items-center"><CheckCircle className="w-4 h-4 text-[#3B82F6] mr-2" /> Instant Setup</div>
                <div className="flex items-center"><CheckCircle className="w-4 h-4 text-[#3B82F6] mr-2" /> Free Sub-domain</div>
                <div className="flex items-center"><CheckCircle className="w-4 h-4 text-[#3B82F6] mr-2" /> No Credit Card Required</div>
            </div>

        </div>
      </div>
      
      {/* Background Decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl pointer-events-none">
          <div className="absolute top-[10%] left-[10%] w-72 h-72 bg-[#1e3a5f]/5 rounded-full blur-[100px]"></div>
          <div className="absolute top-[30%] right-[10%] w-96 h-96 bg-[#3B82F6]/5 rounded-full blur-[100px]"></div>
      </div>
    </section>
  );
};

export default Hero;