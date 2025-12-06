import React from 'react';
import Button from './ui/Button';
import { MessageSquare, Calendar, Database, FileText } from 'lucide-react';

const ApiBilling: React.FC = () => {
  return (
    <section className="py-24 bg-[#0D0D0D] border-t border-[#1A1A1A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-end mb-12">
            <div>
                <h2 className="text-3xl font-bold text-white mb-2">API Billing & Usage</h2>
                <p className="text-gray-400">Monitor your consumption and control costs.</p>
            </div>
            <Button variant="outline" className="mt-4 md:mt-0">View Full API Logs</Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <BillingCard 
                icon={<MessageSquare className="text-[#00DFA2]" />}
                title="AI Chatbot API"
                cost="$0.002"
                unit="per message"
                total="$42.50"
                usage="21,250 msgs"
            />
             <BillingCard 
                icon={<Calendar className="text-blue-400" />}
                title="Appointments API"
                cost="$0.05"
                unit="per booking"
                total="$12.40"
                usage="248 bookings"
            />
             <BillingCard 
                icon={<Database className="text-purple-400" />}
                title="Inventory Sync"
                cost="$10.00"
                unit="flat rate"
                total="$10.00"
                usage="Active"
            />
            <div className="bg-[#1A1A1A] p-6 rounded-xl border border-[#333] flex flex-col justify-center items-center text-center">
                 <div className="w-16 h-16 rounded-full bg-[#0D0D0D] border border-[#333] flex items-center justify-center mb-4">
                    <FileText className="text-gray-400" />
                 </div>
                 <h4 className="text-white font-semibold mb-2">Monthly Invoice</h4>
                 <div className="text-3xl font-bold text-[#00DFA2] mb-4">$64.90</div>
                 <Button variant="secondary" className="text-xs py-2 h-auto">Download PDF</Button>
            </div>
        </div>
      </div>
    </section>
  );
};

const BillingCard = ({ icon, title, cost, unit, total, usage }: any) => (
    <div className="bg-[#1A1A1A] p-6 rounded-xl border border-[#333] hover:border-[#00DFA2] transition-colors group">
        <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-[#0D0D0D] rounded-lg group-hover:bg-[#00DFA2]/10 transition-colors">
                {icon}
            </div>
            <div>
                <h4 className="text-white font-medium">{title}</h4>
                <div className="text-xs text-gray-500">{cost} / {unit}</div>
            </div>
        </div>
        <div className="mb-4">
            <div className="text-xs text-gray-400 mb-1">Current Usage</div>
            <div className="text-lg font-bold text-white">{usage}</div>
        </div>
        <div className="pt-4 border-t border-[#333] flex justify-between items-center">
            <span className="text-xs text-gray-500">Est. Cost</span>
            <span className="text-sm font-bold text-[#00DFA2]">{total}</span>
        </div>
    </div>
);

export default ApiBilling;