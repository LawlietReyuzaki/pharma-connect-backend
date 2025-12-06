import React from 'react';
import { FEATURES } from '../constants';
import { CalendarCheck, Package, Bot, LayoutDashboard } from 'lucide-react';

const iconMap: Record<string, React.ReactNode> = {
  CalendarCheck: <CalendarCheck className="w-8 h-8 text-[#3B82F6]" />,
  Package: <Package className="w-8 h-8 text-[#3B82F6]" />,
  Bot: <Bot className="w-8 h-8 text-[#3B82F6]" />,
  LayoutDashboard: <LayoutDashboard className="w-8 h-8 text-[#3B82F6]" />,
};

const Features: React.FC = () => {
  return (
    <section id="features" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-[#0f2744] mb-4">Our Services</h2>
          <p className="text-gray-500 max-w-2xl mx-auto">
            Everything you need to run a modern, digital-first pharmacy.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {FEATURES.map((feature) => (
            <div 
              key={feature.id}
              className="bg-white p-8 rounded-xl border border-gray-100 soft-shadow hover:border-[#3B82F6] transition-colors duration-300 group"
            >
              <div className="mb-6 p-3 bg-gray-50 rounded-lg w-fit group-hover:bg-[#3B82F6]/10 transition-colors">
                {iconMap[feature.iconName]}
              </div>
              <h3 className="text-xl font-semibold text-[#0f2744] mb-3">{feature.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;