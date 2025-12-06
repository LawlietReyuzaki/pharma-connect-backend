import React from 'react';

const ProjectDocumentation: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-sans text-gray-900">
      <div className="max-w-5xl mx-auto bg-white shadow-xl rounded-2xl overflow-hidden border border-gray-200">
        
        {/* Header */}
        <div className="bg-[#0f2744] px-8 py-10 text-white">
          <h1 className="text-4xl font-bold mb-2">PharmaPlatform Technical Documentation</h1>
          <p className="text-blue-200 text-lg">System Architecture, Type Definitions, and Functional Logic</p>
        </div>

        <div className="p-8 md:p-12 space-y-12">

          {/* 1. Project Overview */}
          <section>
            <h2 className="text-2xl font-bold text-[#0f2744] mb-4 pb-2 border-b border-gray-200">1. Project Overview</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              <strong>PharmaPlatform</strong> is a frontend-only React application simulating a SaaS solution for Pharmacy and Clinic management. 
              It demonstrates a modern "Light Mode" aesthetic using a Navy/Royal Blue color palette. 
              The app functions as a Single Page Application (SPA) using React State for routing rather than browser history, making it lightweight and self-contained.
            </p>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <h3 className="font-semibold text-[#0f2744] mb-2">Tech Stack</h3>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li><strong>Framework:</strong> React 19 (Functional Components + Hooks)</li>
                <li><strong>Language:</strong> TypeScript (Strict typing)</li>
                <li><strong>Styling:</strong> Tailwind CSS + Custom CSS Variables</li>
                <li><strong>Icons:</strong> Lucide React</li>
                <li><strong>Build:</strong> ES Modules (No bundler config required)</li>
              </ul>
            </div>
          </section>

          {/* 2. TypeScript Definitions */}
          <section>
            <h2 className="text-2xl font-bold text-[#0f2744] mb-4 pb-2 border-b border-gray-200">2. TypeScript Definitions (types.ts)</h2>
            <p className="text-gray-600 mb-6">
              The application uses strict TypeScript interfaces to define data models and navigation states.
            </p>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-[#1e3a5f] mb-2">2.1 Navigation Types</h3>
                <pre className="bg-[#1e1e1e] text-gray-300 p-4 rounded-lg overflow-x-auto text-sm">
{`// Used in App.tsx to determine which component to render
export type Page = 'landing' | 'register' | 'admin-login' | 'admin-dashboard';

// Used for the Header navigation links
export interface NavItem {
  label: string; // Display text (e.g., "Home")
  href: string;  // Anchor ID (e.g., "#hero")
}`}
                </pre>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-[#1e3a5f] mb-2">2.2 Data Models</h3>
                <pre className="bg-[#1e1e1e] text-gray-300 p-4 rounded-lg overflow-x-auto text-sm">
{`// Represents a registered pharmacy entity.
// Used in: SuperAdminDashboard, PharmacyProfiles, TrafficAnalysis
export interface PharmacyProfile {
  id: number;
  name: string;
  address: string;
  owner: string;
  traffic: string;     // Display string (e.g., "12.5k/mo")
  revenue: string;     // Formatted currency
  apiCost: string;
  hostingCost: string;
  phone: string;
  email: string;
  regNumber: string;   // License number
  lat: number;         // For map visualization (mock)
  lng: number;
  doctors: number;     // Count of active doctors
}

// Used for feature cards on the landing page
export interface Feature {
  id: number;
  title: string;
  description: string;
  iconName: string; // Mapped to Lucide icons
}`}
                </pre>
              </div>
            </div>
          </section>

          {/* 3. Functional Component Logic */}
          <section>
            <h2 className="text-2xl font-bold text-[#0f2744] mb-4 pb-2 border-b border-gray-200">3. Functional Components & Logic</h2>
            
            <div className="space-y-8">
              {/* App.tsx */}
              <div>
                <h3 className="text-xl font-bold text-[#1e3a5f] flex items-center">
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded uppercase tracking-wide mr-2">Router</span>
                  App.tsx
                </h3>
                <p className="text-gray-600 mt-2 mb-3">
                  Acts as the root controller for the Single Page Application logic.
                </p>
                <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
                  <li><strong>State:</strong> <code>currentPage</code> tracks the active view.</li>
                  <li><strong>Logic:</strong> A <code>switch</code> statement renders the appropriate component based on state.</li>
                  <li><strong>Prop Drilling:</strong> Passes <code>setCurrentPage</code> (as <code>onNavigate</code>) to children components to enable navigation.</li>
                </ul>
              </div>

              {/* SuperAdminDashboard */}
              <div>
                <h3 className="text-xl font-bold text-[#1e3a5f] flex items-center">
                  <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded uppercase tracking-wide mr-2">Core Feature</span>
                  SuperAdminDashboard.tsx
                </h3>
                <p className="text-gray-600 mt-2 mb-3">
                  The complex management interface for administrators.
                </p>
                <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
                  <li><strong>Memoization:</strong> Uses <code>useMemo</code> to filter the pharmacy list in real-time based on the <code>searchTerm</code> state without causing unnecessary re-renders.</li>
                  <li><strong>Dual View State:</strong> Manages a <code>selectedPharmacy</code> state. If null, it shows the Master List. If populated, it renders the Detail View.</li>
                  <li><strong>Responsive Design:</strong> Conditionally renders table columns based on screen width using Tailwind breakpoints (e.g., <code>hidden md:block</code>).</li>
                </ul>
              </div>

              {/* TrafficAnalysis */}
              <div>
                <h3 className="text-xl font-bold text-[#1e3a5f] flex items-center">
                  <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded uppercase tracking-wide mr-2">Visualization</span>
                  TrafficAnalysis.tsx
                </h3>
                <p className="text-gray-600 mt-2 mb-3">
                  Handles data visualization and mock analytics generation.
                </p>
                <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
                  <li><strong>Dynamic Data:</strong> Generates data points on-the-fly based on the selected <code>timeRange</code> prop (Today vs 7 Days).</li>
                  <li><strong>SVG Charts:</strong> Implements a lightweight <code>SimpleLineChart</code> component that calculates SVG polygon points mathematically, avoiding heavy 3rd party charting libraries.</li>
                </ul>
              </div>
            </div>
          </section>

          {/* 4. Styling System */}
          <section>
            <h2 className="text-2xl font-bold text-[#0f2744] mb-4 pb-2 border-b border-gray-200">4. Styling System</h2>
            <p className="text-gray-600 mb-4">
              The project relies on Tailwind CSS with a customized color palette defined in CSS variables within <code>index.html</code>.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg bg-[#0f2744] text-white">
                <div className="text-xs opacity-70">Navy 900</div>
                <div className="font-mono">#0f2744</div>
              </div>
              <div className="p-4 rounded-lg bg-[#1e3a5f] text-white">
                <div className="text-xs opacity-70">Navy 800</div>
                <div className="font-mono">#1e3a5f</div>
              </div>
              <div className="p-4 rounded-lg bg-[#3B82F6] text-white">
                <div className="text-xs opacity-70">Royal Blue</div>
                <div className="font-mono">#3B82F6</div>
              </div>
               <div className="p-4 rounded-lg bg-[#F8FAFC] text-gray-800 border border-gray-200">
                <div className="text-xs opacity-70">Slate 50</div>
                <div className="font-mono">#F8FAFC</div>
              </div>
            </div>
          </section>

           {/* 5. Directory Structure */}
           <section>
            <h2 className="text-2xl font-bold text-[#0f2744] mb-4 pb-2 border-b border-gray-200">5. Directory Structure</h2>
            <pre className="bg-gray-50 text-gray-700 p-6 rounded-lg font-mono text-sm border border-gray-200">
{`/
├── index.html              # Entry HTML, Fonts, CSS Variables
├── index.tsx               # React Entry Point
├── App.tsx                 # Main Routing Component
├── types.ts                # TypeScript Interfaces
├── constants.ts            # Mock Database (Pharmacies, Features, etc.)
│
├── components/
│   ├── Header.tsx          # Navigation Bar
│   ├── Hero.tsx            # Landing Page Hero
│   ├── Features.tsx        # Service Grid
│   ├── CustomDomain.tsx    # Feature Highlight Section
│   ├── Pricing.tsx         # Pricing Cards
│   ├── Footer.tsx          # Footer (Contains Admin Access)
│   ├── RegisterPage.tsx    # Public Registration Form
│   ├── SuperAdminLogin.tsx # Admin Authentication
│   ├── SuperAdminDashboard.tsx # Core Admin Logic
│   ├── TrafficAnalysis.tsx # Charts & Data Viz
│   │
│   └── ui/
│       └── Button.tsx      # Reusable Button Component
`}
            </pre>
          </section>

        </div>
      </div>
    </div>
  );
};

export default ProjectDocumentation;
