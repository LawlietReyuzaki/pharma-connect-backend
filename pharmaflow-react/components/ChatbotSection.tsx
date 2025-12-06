import React from 'react';

const ChatbotSection: React.FC = () => {
  return (
    <section id="chatbot" className="py-24 bg-[#0F0F0F]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          
          {/* Text Content */}
          <div className="order-2 lg:order-1">
             <h2 className="text-3xl font-bold text-white mb-6">Real-time AI Chatbot Support</h2>
             <p className="text-gray-400 mb-8 leading-relaxed">
               Empower your patients with instant answers. Our AI model is trained on pharmaceutical data to handle queries about medicine availability, side effects, and appointment scheduling automatically.
             </p>
             <ul className="space-y-4 text-gray-300">
                <li className="flex items-center">
                    <span className="w-2 h-2 bg-[#00C78E] rounded-full mr-3"></span>
                    24/7 Availability
                </li>
                <li className="flex items-center">
                    <span className="w-2 h-2 bg-[#00C78E] rounded-full mr-3"></span>
                    Inventory Sync
                </li>
                <li className="flex items-center">
                    <span className="w-2 h-2 bg-[#00C78E] rounded-full mr-3"></span>
                    Multi-language Support
                </li>
             </ul>
          </div>

          {/* Console UI */}
          <div className="order-1 lg:order-2">
            <div className="rounded-lg overflow-hidden bg-[#1A1A1A] border border-[#333] shadow-2xl font-mono text-sm relative">
                {/* Terminal Header */}
                <div className="bg-[#0A0A0A] px-4 py-2 border-b border-[#333] flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <div className="ml-4 text-gray-500 text-xs pl-4">admin@pharma-ai:~</div>
                </div>
                
                {/* Terminal Body */}
                <div className="p-6 h-80 overflow-y-auto space-y-3 bg-[#050505]">
                    <div className="text-gray-500">
                        <span className="text-[#00C78E]">➜</span> <span className="text-blue-400">~</span> systemctl start pharma-ai-service
                    </div>
                    <div className="text-gray-400">
                        [OK] Started Pharma AI Engine v4.2.0<br/>
                        [INFO] Connecting to Inventory Database... Connected.<br/>
                        [INFO] Listening on port 8080...
                    </div>
                    
                    <div className="pt-4 text-gray-300">
                        <span className="text-[#00C78E] font-bold">User:</span> Do you have Amoxicillin 500mg in stock?
                    </div>
                    
                    <div className="text-[#00C78E]">
                        <span className="font-bold">AI Bot:</span> Checking inventory database... <br/>
                        <span className="opacity-75">{`> Querying SKU #AMX-500`}</span><br/>
                        Yes, we have 45 units available at the Main Street Branch. Would you like to reserve one?
                    </div>

                     <div className="pt-2 text-gray-300">
                        <span className="text-[#00C78E] font-bold">User:</span> Yes, please. And schedule a pickup for 5 PM.
                    </div>
                    
                    <div className="text-[#00C78E]">
                        <span className="font-bold">AI Bot:</span> Order #8921 confirmed. <br/>
                        Reserving 1x Amoxicillin 500mg.<br/>
                        Pickup scheduled for today at 17:00.
                    </div>

                    <div className="pt-2 flex items-center">
                        <span className="text-[#00C78E] mr-2">➜</span>
                        <span className="w-2 h-4 bg-[#00C78E] animate-pulse"></span>
                    </div>
                </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ChatbotSection;