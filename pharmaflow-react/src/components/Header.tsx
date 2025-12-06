import React, { useState } from 'react';
import { Menu, X, Activity, Home, LayoutDashboard } from 'lucide-react';
import { NAV_ITEMS } from '../constants';
import Button from './ui/Button';
import { Page } from '../types';

interface HeaderProps {
  onNavigate: (page: Page) => void;
}

const Header: React.FC<HeaderProps> = ({ onNavigate }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-lg border-b border-gray-200 shadow-sm transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <div 
            className="flex items-center space-x-2 cursor-pointer group"
            onClick={() => onNavigate('landing')}
          >
            <div className="bg-[#1e3a5f]/10 p-2 rounded-lg group-hover:bg-[#1e3a5f]/20 transition-colors">
                <Activity className="h-6 w-6 text-[#1e3a5f]" />
            </div>
            <span className="text-xl font-bold tracking-tight text-[#0f2744]">
              Pharma<span className="text-[#3B82F6]">Platform</span>
            </span>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center space-x-8">
            {NAV_ITEMS.map((item) => (
              <a
                key={item.label}
                href={item.href}
                className="text-sm font-medium text-gray-600 hover:text-[#3B82F6] transition-colors relative after:content-[''] after:absolute after:w-full after:scale-x-0 after:h-0.5 after:bottom-0 after:left-0 after:bg-[#3B82F6] after:origin-bottom-right after:transition-transform after:duration-300 hover:after:scale-x-100 hover:after:origin-bottom-left"
                onClick={(e) => {
                    if(item.label === 'Home') {
                        e.preventDefault();
                        onNavigate('landing');
                    }
                }}
              >
                {item.label}
              </a>
            ))}
          </nav>

          {/* Desktop Right Actions */}
          <div className="hidden md:flex items-center space-x-3">
             {/* Quick Nav Icons */}
            <div className="flex items-center bg-gray-50 rounded-lg p-1 border border-gray-100 mr-2">
                <button 
                    onClick={() => onNavigate('landing')}
                    className="p-2 text-gray-500 hover:text-[#3B82F6] hover:bg-white rounded-md transition-all duration-200"
                    title="Back to Home"
                >
                    <Home className="w-5 h-5" />
                </button>
                <div className="w-px h-4 bg-gray-200 mx-1"></div>
                <button 
                    onClick={() => onNavigate('admin-login')}
                    className="p-2 text-gray-500 hover:text-[#3B82F6] hover:bg-white rounded-md transition-all duration-200"
                    title="Admin Page"
                >
                    <LayoutDashboard className="w-5 h-5" />
                </button>
            </div>

            <Button variant="primary" className="py-2.5 px-6 text-sm shadow-lg shadow-[#1e3a5f]/20" onClick={() => onNavigate('register')}>
              Register Pharmacy
            </Button>
          </div>

          {/* Mobile Right Actions */}
          <div className="md:hidden flex items-center space-x-3">
            {/* Quick Nav Icons (Mobile) */}
            <div className="flex items-center bg-gray-50 rounded-lg p-1 border border-gray-100">
                <button 
                    onClick={() => onNavigate('landing')}
                    className="p-2 text-gray-500 hover:text-[#3B82F6] hover:bg-white rounded-md transition-all duration-200"
                    title="Back to Home"
                >
                    <Home className="w-4 h-4" />
                </button>
                <div className="w-px h-3 bg-gray-200 mx-1"></div>
                <button 
                    onClick={() => onNavigate('admin-login')}
                    className="p-2 text-gray-500 hover:text-[#3B82F6] hover:bg-white rounded-md transition-all duration-200"
                    title="Admin Page"
                >
                    <LayoutDashboard className="w-4 h-4" />
                </button>
            </div>

            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-gray-600 hover:text-[#3B82F6] p-2 focus:outline-none"
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav */}
      {isOpen && (
        <div className="md:hidden bg-white border-b border-gray-200 animate-in slide-in-from-top-5 duration-200">
          <div className="px-4 pt-2 pb-6 space-y-1">
            {NAV_ITEMS.map((item) => (
              <a
                key={item.label}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className="block px-3 py-4 text-base font-medium text-gray-600 hover:text-[#3B82F6] hover:bg-gray-50 rounded-md transition-colors"
              >
                {item.label}
              </a>
            ))}
            <div className="pt-4">
                <Button fullWidth onClick={() => { setIsOpen(false); onNavigate('register'); }}>
                    Register Pharmacy
                </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;