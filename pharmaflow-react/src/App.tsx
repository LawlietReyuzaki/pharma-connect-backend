
import React, { useState } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import Features from './components/Features';
import CustomDomain from './components/CustomDomain';
import Pricing from './components/Pricing';
import Footer from './components/Footer';
import RegisterPage from './components/RegisterPage';
import SuperAdminLogin from './components/SuperAdminLogin';
import SuperAdminDashboard from './components/SuperAdminDashboard';
import { Page } from './types';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('landing');

  const renderPage = () => {
    switch(currentPage) {
        case 'register':
            return <RegisterPage onNavigate={setCurrentPage} />;
        case 'admin-login':
            return <SuperAdminLogin onNavigate={setCurrentPage} />;
        case 'admin-dashboard':
            return <SuperAdminDashboard onNavigate={setCurrentPage} />;
        case 'landing':
        default:
            return (
                <div className="min-h-screen bg-gray-50 font-sans antialiased text-gray-900">
                    <Header onNavigate={setCurrentPage} />
                    <main>
                        <Hero onNavigate={setCurrentPage} />
                        <Features />
                        <CustomDomain />
                        <Pricing onNavigate={setCurrentPage} />
                    </main>
                    <Footer onNavigate={setCurrentPage} />
                </div>
            );
    }
  };

  return (
      <>
        {renderPage()}
      </>
  );
};

export default App;