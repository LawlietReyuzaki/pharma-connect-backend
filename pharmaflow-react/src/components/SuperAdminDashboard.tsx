import React, { useState, useMemo } from 'react';
import { SAMPLE_PHARMACIES } from '../constants';
import { PharmacyProfile } from '../types';
import Button from './ui/Button';
import TrafficAnalysis from './TrafficAnalysis';
import { 
    LayoutDashboard, 
    ArrowLeft, 
    MapPin, 
    Phone, 
    Mail, 
    Building, 
    Activity, 
    Users, 
    TrendingUp, 
    Server, 
    Database, 
    Cpu,
    Trash2,
    Search,
    Filter,
    Edit3,
    BarChart2,
    List,
    Home,
    XCircle,
    MoreHorizontal
} from 'lucide-react';
import { Page } from '../types';

interface SuperAdminDashboardProps {
    onNavigate: (page: Page) => void;
}

const SuperAdminDashboard: React.FC<SuperAdminDashboardProps> = ({ onNavigate }) => {
  const [activeTab, setActiveTab] = useState<'pharmacies' | 'analytics'>('pharmacies');
  const [selectedPharmacy, setSelectedPharmacy] = useState<PharmacyProfile | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter Logic
  const filteredPharmacies = useMemo(() => {
    const term = searchTerm.toLowerCase();
    return SAMPLE_PHARMACIES.filter(p => 
        p.name.toLowerCase().includes(term) ||
        p.address.toLowerCase().includes(term) ||
        p.owner.toLowerCase().includes(term) ||
        p.regNumber.toLowerCase().includes(term) ||
        p.phone.toLowerCase().includes(term) ||
        p.id.toString().includes(term)
    );
  }, [searchTerm]);

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans text-[#0f2744]">
      {/* Dashboard Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex justify-between items-center">
              <div className="flex items-center space-x-3">
                  <div className="bg-[#1e3a5f]/10 p-2 rounded-lg">
                    <LayoutDashboard className="w-5 h-5 text-[#1e3a5f]" />
                  </div>
                  <span className="font-bold text-[#0f2744] tracking-tight hidden sm:block">Super Admin Dashboard</span>
                  <span className="font-bold text-[#0f2744] tracking-tight sm:hidden">Admin</span>
              </div>
              
              {/* Navigation Tabs (Desktop) */}
              <div className="hidden md:flex items-center bg-gray-50 rounded-lg p-1 mx-4 border border-gray-100">
                  <button 
                    onClick={() => { setActiveTab('pharmacies'); setSelectedPharmacy(null); }}
                    className={`flex items-center px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-all ${activeTab === 'pharmacies' ? 'bg-white text-[#3B82F6] shadow-sm ring-1 ring-gray-200' : 'text-gray-500 hover:text-gray-700'}`}
                  >
                      <List className="w-4 h-4 mr-1.5" /> Pharmacies
                  </button>
                  <button 
                    onClick={() => setActiveTab('analytics')}
                    className={`flex items-center px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-all ${activeTab === 'analytics' ? 'bg-white text-[#3B82F6] shadow-sm ring-1 ring-gray-200' : 'text-gray-500 hover:text-gray-700'}`}
                  >
                      <BarChart2 className="w-4 h-4 mr-1.5" /> Traffic Analysis
                  </button>
              </div>

              <div className="flex items-center space-x-3">
                  {/* Quick Nav Icons */}
                  <div className="flex items-center bg-gray-50 rounded-lg p-1 border border-gray-100 flex-shrink-0">
                      <button 
                          onClick={() => onNavigate('landing')}
                          className="p-2 text-gray-500 hover:text-[#3B82F6] hover:bg-white rounded-md transition-all duration-200"
                          title="Back to Home"
                      >
                          <Home className="w-5 h-5 sm:w-5 sm:h-5" />
                      </button>
                      <div className="w-px h-4 bg-gray-200 mx-1"></div>
                      <button 
                          onClick={() => onNavigate('admin-login')}
                          className="p-2 text-gray-500 hover:text-[#3B82F6] hover:bg-white rounded-md transition-all duration-200"
                          title="Admin Page"
                      >
                          <LayoutDashboard className="w-5 h-5 sm:w-5 sm:h-5" />
                      </button>
                  </div>
                  
                  <div className="hidden lg:flex flex-col items-end pl-2 border-l border-gray-100">
                    <span className="text-sm font-semibold text-[#0f2744]">Administrator</span>
                    <span className="text-xs text-gray-500">admin@system.com</span>
                  </div>
                  <button onClick={() => onNavigate('landing')} className="text-sm text-red-500 hover:text-red-600 font-medium px-3 py-1 rounded-md hover:bg-red-50 transition-colors ml-2 whitespace-nowrap">Logout</button>
              </div>
          </div>

          {/* Mobile Tabs (Visible only on small screens) */}
          <div className="md:hidden flex p-2 border-t border-gray-100 bg-white justify-center space-x-4">
               <button 
                    onClick={() => { setActiveTab('pharmacies'); setSelectedPharmacy(null); }}
                    className={`flex items-center px-4 py-2 text-sm font-medium border-b-2 transition-all ${activeTab === 'pharmacies' ? 'border-[#3B82F6] text-[#3B82F6]' : 'border-transparent text-gray-500'}`}
                  >
                      <List className="w-4 h-4 mr-2" /> Pharmacies
                  </button>
                  <button 
                    onClick={() => setActiveTab('analytics')}
                    className={`flex items-center px-4 py-2 text-sm font-medium border-b-2 transition-all ${activeTab === 'analytics' ? 'border-[#3B82F6] text-[#3B82F6]' : 'border-transparent text-gray-500'}`}
                  >
                      <BarChart2 className="w-4 h-4 mr-2" /> Analysis
                  </button>
          </div>
      </header>

      <main className="flex-grow p-4 sm:p-6 max-w-7xl mx-auto w-full">
        
        {activeTab === 'analytics' ? (
            /* ================= TRAFFIC ANALYTICS VIEW ================= */
            <div className="space-y-6">
                 <div>
                    <h2 className="text-2xl font-bold text-[#0f2744]">Daily Traffic Analysis</h2>
                    <p className="text-gray-500 text-sm mt-1">Monitor real-time visitors, interactions, and platform usage.</p>
                </div>
                <TrafficAnalysis pharmacies={SAMPLE_PHARMACIES} />
            </div>
        ) : selectedPharmacy ? (
            /* ================= DETAILED VIEW ================= */
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                <button 
                    onClick={() => setSelectedPharmacy(null)}
                    className="flex items-center text-sm text-gray-500 hover:text-[#0f2744] mb-4 transition-colors group"
                >
                    <ArrowLeft className="w-4 h-4 mr-1 group-hover:-translate-x-1 transition-transform" /> Back to Pharmacy List
                </button>

                {/* Header Info */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-3xl font-bold text-[#0f2744]">{selectedPharmacy.name}</h1>
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full border border-green-200 uppercase tracking-wide">Active</span>
                        </div>
                        <div className="flex flex-wrap items-center text-gray-500 mt-2 space-x-4 text-sm">
                            <span className="flex items-center"><MapPin className="w-3.5 h-3.5 mr-1.5 text-gray-400" /> {selectedPharmacy.address}</span>
                            <span className="flex items-center"><Building className="w-3.5 h-3.5 mr-1.5 text-gray-400" /> {selectedPharmacy.regNumber}</span>
                        </div>
                    </div>
                    <div className="flex space-x-3">
                         <Button variant="secondary" className="px-4 py-2 text-sm flex items-center shadow-none">
                             <Edit3 className="w-4 h-4 mr-2" /> Edit Details
                         </Button>
                         <Button variant="danger" className="px-4 py-2 text-sm flex items-center shadow-none">
                             <Trash2 className="w-4 h-4 mr-2" /> Suspend
                         </Button>
                    </div>
                </div>

                {/* 1. Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard label="Total Traffic" value={selectedPharmacy.traffic} icon={<Activity className="text-[#3B82F6]" />} />
                    <StatCard label="Appointments" value="142" icon={<Users className="text-[#6366F1]" />} />
                    <StatCard label="Doctors Active" value={selectedPharmacy.doctors.toString()} icon={<Users className="text-green-500" />} />
                    <StatCard label="Revenue (Est)" value={selectedPharmacy.revenue} icon={<TrendingUp className="text-[#8B5CF6]" />} />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* 2. Pharmacy Info & Contact */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <h3 className="font-bold text-[#0f2744] mb-4">Pharmacy Details</h3>
                        <div className="space-y-4 text-sm">
                            <div className="flex justify-between py-3 border-b border-gray-50">
                                <span className="text-gray-500">Owner Name</span>
                                <span className="font-medium text-[#0f2744]">{selectedPharmacy.owner}</span>
                            </div>
                            <div className="flex justify-between py-3 border-b border-gray-50">
                                <span className="text-gray-500">Email</span>
                                <span className="font-medium text-[#0f2744] flex items-center"><Mail className="w-3 h-3 mr-2 text-gray-400" /> {selectedPharmacy.email}</span>
                            </div>
                             <div className="flex justify-between py-3 border-b border-gray-50">
                                <span className="text-gray-500">Phone</span>
                                <span className="font-medium text-[#0f2744] flex items-center"><Phone className="w-3 h-3 mr-2 text-gray-400" /> {selectedPharmacy.phone}</span>
                            </div>
                            <div className="flex justify-between py-3 border-b border-gray-50">
                                <span className="text-gray-500">Reg Number</span>
                                <span className="font-mono text-[#0f2744] flex items-center">{selectedPharmacy.regNumber}</span>
                            </div>
                             <div className="h-32 bg-gray-100 rounded-lg mt-4 flex items-center justify-center text-gray-400 text-xs border border-gray-200">
                                 [Map View: {selectedPharmacy.lat}, {selectedPharmacy.lng}]
                             </div>
                        </div>
                    </div>

                    {/* 3. Traffic Analysis */}
                    <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                         <div className="flex justify-between items-center mb-6">
                            <h3 className="font-bold text-[#0f2744]">Traffic Analysis</h3>
                            <select className="text-xs border-gray-200 rounded-lg text-gray-600 bg-gray-50 p-2 outline-none focus:ring-2 focus:ring-[#3B82F6]">
                                <option>Last 30 Days</option>
                                <option>Last 7 Days</option>
                            </select>
                         </div>
                         {/* Placeholder Chart */}
                         <div className="h-64 flex items-end justify-between space-x-2 px-4 border-b border-gray-100 pb-2">
                             {[35, 55, 40, 70, 45, 60, 50, 75, 55, 80, 65, 90].map((h, i) => (
                                 <div key={i} className="w-full bg-[#3B82F6]/10 hover:bg-[#3B82F6]/30 rounded-t-md transition-all relative group" style={{ height: `${h}%` }}>
                                     <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-[#0f2744] text-white text-[10px] px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                                         {h * 10} Visits
                                     </div>
                                 </div>
                             ))}
                         </div>
                         <div className="flex justify-between mt-3 text-xs text-gray-400 font-medium">
                             <span>1st</span><span>5th</span><span>10th</span><span>15th</span><span>20th</span><span>25th</span>
                         </div>
                    </div>
                </div>

                {/* 4. Costing & Infrastructure */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Costing Overview */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <h3 className="font-bold text-[#0f2744] mb-6">Costing Overview</h3>
                        <div className="space-y-4">
                            <CostRow label="Hosting Plan" value={selectedPharmacy.hostingCost} sub="Standard Tier" />
                            <CostRow label="API Usage" value="$12.45" sub="1450 Calls" />
                            <CostRow label="Chatbot Consumption" value="$8.50" sub="8500 Tokens" />
                            <div className="pt-4 border-t border-gray-100 flex justify-between items-center mt-4">
                                <span className="font-bold text-[#0f2744]">Total Monthly</span>
                                <span className="text-xl font-bold text-[#3B82F6]">$69.95</span>
                            </div>
                        </div>
                    </div>

                    {/* Infrastructure Breakdown */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                         <h3 className="font-bold text-[#0f2744] mb-6">Infrastructure Breakdown</h3>
                         <div className="overflow-x-auto">
                             <table className="w-full text-sm text-left">
                                 <thead className="text-gray-500 bg-gray-50 text-xs uppercase font-semibold">
                                     <tr>
                                         <th className="px-3 py-2 rounded-l-lg">Resource</th>
                                         <th className="px-3 py-2 text-right rounded-r-lg">Cost</th>
                                     </tr>
                                 </thead>
                                 <tbody className="divide-y divide-gray-50">
                                     <tr>
                                         <td className="px-3 py-3 flex items-center"><Server className="w-3 h-3 mr-2 text-gray-400"/> Server Instances</td>
                                         <td className="px-3 py-3 text-right font-mono text-gray-600">$45.00</td>
                                     </tr>
                                      <tr>
                                         <td className="px-3 py-3 flex items-center"><Database className="w-3 h-3 mr-2 text-gray-400"/> Database Storage</td>
                                         <td className="px-3 py-3 text-right font-mono text-gray-600">$12.00</td>
                                     </tr>
                                      <tr>
                                         <td className="px-3 py-3 flex items-center"><Cpu className="w-3 h-3 mr-2 text-gray-400"/> AI Processing</td>
                                         <td className="px-3 py-3 text-right font-mono text-gray-600">$8.50</td>
                                     </tr>
                                     <tr>
                                         <td className="px-3 py-3 flex items-center"><Activity className="w-3 h-3 mr-2 text-gray-400"/> Bandwidth</td>
                                         <td className="px-3 py-3 text-right font-mono text-gray-600">$4.45</td>
                                     </tr>
                                 </tbody>
                             </table>
                         </div>
                    </div>
                </div>
            </div>
        ) : (
            /* ================= NEW LIST VIEW ================= */
            <div className="space-y-6 animate-in fade-in duration-500">
                
                {/* Header & Search Section */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
                    <div>
                        <h2 className="text-2xl font-bold text-[#0f2744]">Registered Pharmacies</h2>
                        <p className="text-gray-500 text-sm mt-1">Manage, monitor, and configure active deployments.</p>
                    </div>
                    
                    <div className="w-full md:w-auto flex flex-col sm:flex-row gap-3">
                        <div className="relative group flex-grow">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Search className="h-5 w-5 text-gray-400 group-focus-within:text-[#3B82F6] transition-colors" />
                            </div>
                            <input
                                type="text"
                                className="block w-full md:w-80 pl-10 pr-3 py-2.5 border border-gray-200 rounded-xl leading-5 bg-gray-50 text-[#0f2744] placeholder-gray-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#3B82F6] focus:border-transparent transition-all duration-200 sm:text-sm shadow-sm"
                                placeholder="Search Name, City, Owner, ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <button className="inline-flex items-center justify-center px-4 py-2.5 border border-gray-200 shadow-sm text-sm font-medium rounded-xl text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#3B82F6] transition-all">
                            <Filter className="h-4 w-4 mr-2 text-gray-500" /> Filter
                        </button>
                    </div>
                </div>

                {/* List Content */}
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                    {/* Desktop Table Header */}
                    <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-4 bg-gray-50/50 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-wider">
                        <div className="col-span-4 pl-2">Pharmacy Details</div>
                        <div className="col-span-3">Owner Info</div>
                        <div className="col-span-2">Location</div>
                        <div className="col-span-2">Status</div>
                        <div className="col-span-1 text-right">Actions</div>
                    </div>

                    <div className="divide-y divide-gray-100">
                        {filteredPharmacies.length > 0 ? (
                            filteredPharmacies.map((pharmacy) => (
                                <div 
                                    key={pharmacy.id} 
                                    className="group grid grid-cols-1 md:grid-cols-12 gap-4 px-6 py-5 hover:bg-gray-50/80 transition-all duration-200 items-center cursor-pointer md:cursor-default"
                                    onClick={(e) => {
                                        // On mobile, clicking row opens detail
                                        if (window.innerWidth < 768) setSelectedPharmacy(pharmacy);
                                    }}
                                >
                                    {/* Pharmacy Details */}
                                    <div className="col-span-1 md:col-span-4 flex items-center space-x-4">
                                        <div className="flex-shrink-0">
                                            <div className="h-12 w-12 rounded-xl bg-[#1e3a5f]/10 flex items-center justify-center text-[#1e3a5f] border border-[#1e3a5f]/20 group-hover:scale-105 transition-transform duration-200">
                                                <Building className="h-6 w-6" />
                                            </div>
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <div className="text-sm font-bold text-[#0f2744] truncate flex items-center gap-2">
                                                {pharmacy.name}
                                            </div>
                                            <div className="flex items-center gap-2 mt-0.5">
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-600 border border-gray-200">
                                                    ID #{pharmacy.id}
                                                </span>
                                                <span className="text-[10px] font-mono text-gray-400">{pharmacy.regNumber}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Owner Info */}
                                    <div className="col-span-1 md:col-span-3 hidden md:block">
                                        <div className="text-sm text-[#0f2744] flex items-center font-medium">
                                            <Users className="w-3.5 h-3.5 mr-2 text-gray-400" /> {pharmacy.owner}
                                        </div>
                                        <div className="text-sm text-gray-500 flex items-center mt-1">
                                            <Phone className="w-3.5 h-3.5 mr-2 text-gray-400" /> {pharmacy.phone}
                                        </div>
                                    </div>

                                    {/* Location */}
                                    <div className="col-span-1 md:col-span-2 hidden md:block">
                                        <div className="text-sm text-gray-600 flex items-start">
                                            <MapPin className="w-3.5 h-3.5 mr-2 mt-0.5 text-gray-400 flex-shrink-0" />
                                            <span className="line-clamp-2">{pharmacy.address}</span>
                                        </div>
                                    </div>

                                    {/* Status */}
                                    <div className="col-span-1 md:col-span-2 flex items-center justify-between md:justify-start">
                                        <span className="md:hidden text-sm font-medium text-gray-500">Status</span>
                                        {pharmacy.id % 2 !== 0 ? (
                                             <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                                                <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5"></span>
                                                Active
                                             </span>
                                        ) : (
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200">
                                                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-1.5"></span>
                                                Inactive
                                            </span>
                                        )}
                                    </div>

                                    {/* Actions */}
                                    <div className="col-span-1 md:col-span-1 flex justify-end">
                                        <Button 
                                            variant="secondary" 
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setSelectedPharmacy(pharmacy);
                                            }}
                                            className="px-3 py-2 text-xs hidden md:inline-flex items-center hover:bg-[#1e3a5f] hover:text-white hover:border-[#1e3a5f] transition-colors shadow-none"
                                        >
                                            View / Edit
                                        </Button>
                                        <button className="md:hidden text-gray-400 p-2">
                                            <MoreHorizontal className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            ))
                        ) : (
                            /* Empty State */
                            <div className="flex flex-col items-center justify-center py-24 text-center">
                                <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-6">
                                    <Search className="w-10 h-10 text-gray-300" />
                                </div>
                                <h3 className="text-xl font-bold text-[#0f2744]">No registered pharmacy found</h3>
                                <p className="text-gray-500 max-w-sm mt-2">
                                    We couldn't find any pharmacy matching "{searchTerm}". Try adjusting your search filters.
                                </p>
                                <button 
                                    onClick={() => setSearchTerm('')}
                                    className="mt-8 text-[#3B82F6] hover:text-[#1e3a5f] font-semibold text-sm flex items-center bg-[#3B82F6]/10 px-4 py-2 rounded-lg transition-colors"
                                >
                                    Clear Search <XCircle className="ml-2 w-4 h-4" />
                                </button>
                            </div>
                        )}
                    </div>
                    
                    {/* Pagination Footer (Visual Only) */}
                    {filteredPharmacies.length > 0 && (
                        <div className="bg-gray-50/50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                            <div className="text-xs text-gray-500">
                                Showing <span className="font-bold text-[#0f2744]">{filteredPharmacies.length}</span> results
                            </div>
                            <div className="flex space-x-2">
                                <button className="px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-medium text-gray-600 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors" disabled>Previous</button>
                                <button className="px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-medium text-gray-600 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors" disabled>Next</button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        )}
      </main>
    </div>
  );
};

const StatCard = ({ label, value, icon }: any) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-500">{label}</h4>
            {icon}
        </div>
        <div className="text-2xl font-bold text-[#0f2744]">{value}</div>
    </div>
);

const CostRow = ({ label, value, sub }: any) => (
    <div className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0">
        <div>
            <div className="text-sm font-medium text-gray-700">{label}</div>
            <div className="text-xs text-gray-400">{sub}</div>
        </div>
        <div className="font-mono text-[#0f2744] font-medium">{value}</div>
    </div>
);

export default SuperAdminDashboard;