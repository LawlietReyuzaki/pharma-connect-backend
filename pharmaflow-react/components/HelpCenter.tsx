import React from 'react';
import Button from './ui/Button';
import { LifeBuoy, MessageCircle, FileQuestion, Mail } from 'lucide-react';

const HelpCenter: React.FC = () => {
  return (
    <section id="help" className="py-24 bg-[#0D0D0D] border-t border-[#1A1A1A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            
            {/* Left Col */}
            <div className="lg:col-span-1">
                <h2 className="text-3xl font-bold text-white mb-4">Help Center</h2>
                <p className="text-gray-400 mb-8">
                    Need assistance? Our support team is online 24/7 to help you manage your pharmacy platform.
                </p>
                <div className="space-y-4">
                    <Button fullWidth className="justify-start">
                        <MessageCircle className="mr-3 h-5 w-5" /> Live Chat Support
                    </Button>
                    <Button fullWidth variant="secondary" className="justify-start">
                        <Mail className="mr-3 h-5 w-5" /> Email Support
                    </Button>
                </div>
            </div>

            {/* Right Col */}
            <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                 {/* Ticket Panel */}
                 <div className="bg-[#1A1A1A] p-6 rounded-xl border border-[#333]">
                     <LifeBuoy className="h-8 w-8 text-[#00DFA2] mb-4" />
                     <h3 className="text-lg font-bold text-white mb-2">Open a Ticket</h3>
                     <p className="text-sm text-gray-400 mb-6">For technical issues or billing disputes.</p>
                     <div className="space-y-3">
                         <input className="w-full bg-[#0D0D0D] border border-[#333] rounded p-3 text-sm text-white focus:border-[#00DFA2] outline-none" placeholder="Subject" />
                         <textarea className="w-full bg-[#0D0D0D] border border-[#333] rounded p-3 text-sm text-white focus:border-[#00DFA2] outline-none h-24" placeholder="Describe your issue..."></textarea>
                         <Button className="w-full py-2 text-sm">Submit Ticket</Button>
                     </div>
                 </div>

                 {/* KB Links */}
                 <div className="bg-[#1A1A1A] p-6 rounded-xl border border-[#333]">
                     <FileQuestion className="h-8 w-8 text-blue-400 mb-4" />
                     <h3 className="text-lg font-bold text-white mb-2">Knowledge Base</h3>
                     <p className="text-sm text-gray-400 mb-6">Quick guides for common tasks.</p>
                     <ul className="space-y-3">
                         <li><a href="#" className="text-sm text-gray-300 hover:text-[#00DFA2] flex items-center"><span className="w-1.5 h-1.5 bg-[#333] rounded-full mr-2"></span> How to Add Doctors</a></li>
                         <li><a href="#" className="text-sm text-gray-300 hover:text-[#00DFA2] flex items-center"><span className="w-1.5 h-1.5 bg-[#333] rounded-full mr-2"></span> Integrating AI Chatbot</a></li>
                         <li><a href="#" className="text-sm text-gray-300 hover:text-[#00DFA2] flex items-center"><span className="w-1.5 h-1.5 bg-[#333] rounded-full mr-2"></span> Managing Inventory Stocks</a></li>
                         <li><a href="#" className="text-sm text-gray-300 hover:text-[#00DFA2] flex items-center"><span className="w-1.5 h-1.5 bg-[#333] rounded-full mr-2"></span> API Billing FAQ</a></li>
                     </ul>
                 </div>
            </div>

        </div>
      </div>
    </section>
  );
};

export default HelpCenter;