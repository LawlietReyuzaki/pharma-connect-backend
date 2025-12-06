import React from 'react';
import { Activity, Lock } from 'lucide-react';
import { Page } from '../types';

interface FooterProps {
    onNavigate: (page: Page) => void;
}

const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  return (
    <footer id="footer" className="bg-white border-t border-gray-200 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center">
          
          <div className="flex items-center space-x-2 mb-4 md:mb-0">
             <Activity className="h-6 w-6 text-[#1e3a5f]" />
             <span className="text-lg font-bold text-[#0f2744]">
               Pharma<span className="text-[#3B82F6]">Platform</span>
             </span>
          </div>

          <div className="text-gray-500 text-sm">
             contact@pharmaplatform.com
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-100 flex justify-between items-center">
            <p className="text-gray-400 text-sm">
                &copy; {new Date().getFullYear()} Pharma Platform. All rights reserved.
            </p>
            
            {/* Hidden Admin Access */}
            <button 
                onClick={() => onNavigate('admin-login')}
                className="text-gray-300 hover:text-gray-500 transition-colors flex items-center text-xs"
            >
                <Lock className="w-3 h-3 mr-1" /> Super Admin Access
            </button>
        </div>
      </div>
    </footer>
  );
};

export default Footer;