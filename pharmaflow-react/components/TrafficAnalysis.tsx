import React, { useState, useMemo, useEffect } from 'react';
import { PharmacyProfile } from '../types';
import { 
    Users, 
    MessageSquare, 
    Calendar, 
    Search, 
    TrendingUp, 
    TrendingDown, 
    Filter, 
    BarChart3, 
    PieChart as PieIcon, 
    Activity,
    AlertCircle
} from 'lucide-react';

interface TrafficAnalysisProps {
    pharmacies: PharmacyProfile[];
}

const TrafficAnalysis: React.FC<TrafficAnalysisProps> = ({ pharmacies }) => {
    const [timeRange, setTimeRange] = useState<'today' | '7d' | '30d' | 'custom'>('7d');
    const [selectedPharmacyId, setSelectedPharmacyId] = useState<string>('all');
    const [isLoading, setIsLoading] = useState(false);

    // Simulate data fetching/calculation
    useEffect(() => {
        setIsLoading(true);
        const timer = setTimeout(() => setIsLoading(false), 600);
        return () => clearTimeout(timer);
    }, [timeRange, selectedPharmacyId]);

    // Mock Data Generation based on filters
    const analysisData = useMemo(() => {
        const days = timeRange === 'today' ? 1 : timeRange === '7d' ? 7 : 30;
        const multiplier = selectedPharmacyId === 'all' ? pharmacies.length : 1;
        const data = [];
        const now = new Date();

        for (let i = days - 1; i >= 0; i--) {
            const d = new Date(now);
            d.setDate(d.getDate() - i);
            
            // Randomize somewhat realistic data
            const baseTraffic = Math.floor(Math.random() * 100 + 50) * multiplier;
            const newUsers = Math.floor(baseTraffic * 0.35);
            const repeatUsers = baseTraffic - newUsers;
            
            data.push({
                date: timeRange === 'today' 
                    ? `${d.getHours()}:00` 
                    : d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' }),
                visitors: baseTraffic,
                newUsers,
                repeatUsers,
                interactions: Math.floor(baseTraffic * 1.5),
                appointments: Math.floor(baseTraffic * 0.1),
                queries: Math.floor(baseTraffic * 2.2)
            });
        }
        return data;
    }, [timeRange, selectedPharmacyId, pharmacies.length]);

    // Calculate Summaries
    const summary = useMemo(() => {
        if (analysisData.length === 0) return null;
        
        const totalVisitors = analysisData.reduce((acc, curr) => acc + curr.visitors, 0);
        const avgTraffic = Math.round(totalVisitors / analysisData.length);
        
        const sortedByTraffic = [...analysisData].sort((a, b) => b.visitors - a.visitors);
        const highestDay = sortedByTraffic[0];
        const lowestDay = sortedByTraffic[sortedByTraffic.length - 1];

        const totalNew = analysisData.reduce((acc, curr) => acc + curr.newUsers, 0);
        const totalRepeat = analysisData.reduce((acc, curr) => acc + curr.repeatUsers, 0);

        return {
            avgTraffic,
            highestDay,
            lowestDay,
            totalNew,
            totalRepeat,
            totalVisitors
        };
    }, [analysisData]);

    if (isLoading) {
        return <AnalysisSkeleton />;
    }

    if (analysisData.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl border border-gray-200 shadow-sm">
                <AlertCircle className="w-12 h-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-bold text-[#0f2744]">No traffic data available</h3>
                <p className="text-gray-500">Try adjusting your filters to see results.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Controls */}
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="flex items-center w-full md:w-auto space-x-2 bg-gray-50 p-1 rounded-lg border border-gray-100">
                    <Filter className="w-4 h-4 text-gray-400 ml-2" />
                    <select 
                        className="bg-transparent border-none text-sm font-medium text-gray-700 focus:ring-0 cursor-pointer outline-none w-full md:w-48"
                        value={selectedPharmacyId}
                        onChange={(e) => setSelectedPharmacyId(e.target.value)}
                    >
                        <option value="all">All Pharmacies Combined</option>
                        {pharmacies.map(p => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                    </select>
                </div>

                <div className="flex bg-gray-50 p-1 rounded-lg w-full md:w-auto">
                    {['Today', '7 Days', '30 Days', 'Custom'].map((label) => {
                        const val = label === 'Today' ? 'today' : label === '7 Days' ? '7d' : label === '30 Days' ? '30d' : 'custom';
                        const isActive = timeRange === val;
                        return (
                            <button
                                key={label}
                                onClick={() => setTimeRange(val as any)}
                                className={`flex-1 md:flex-none px-4 py-1.5 text-xs font-medium rounded-md transition-all ${
                                    isActive ? 'bg-white text-[#3B82F6] shadow-sm font-bold' : 'text-gray-500 hover:text-[#0f2744]'
                                }`}
                            >
                                {label}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Main Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard 
                    title="Total Visitors" 
                    value={summary?.totalVisitors.toLocaleString()} 
                    trend="+12.5%" 
                    icon={<Users className="text-[#3B82F6]" />} 
                />
                <StatCard 
                    title="Chatbot Interactions" 
                    value={analysisData.reduce((a, c) => a + c.interactions, 0).toLocaleString()} 
                    trend="+8.1%" 
                    icon={<MessageSquare className="text-[#6366F1]" />} 
                />
                <StatCard 
                    title="Appointments" 
                    value={analysisData.reduce((a, c) => a + c.appointments, 0).toLocaleString()} 
                    trend="-2.4%" 
                    icon={<Calendar className="text-[#8B5CF6]" />} 
                    isNegative
                />
                <StatCard 
                    title="Search Queries" 
                    value={analysisData.reduce((a, c) => a + c.queries, 0).toLocaleString()} 
                    trend="+15.3%" 
                    icon={<Search className="text-[#3B82F6]" />} 
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Traffic Trend Line Chart */}
                <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h3 className="text-lg font-bold text-[#0f2744]">Traffic Trend</h3>
                            <p className="text-xs text-gray-500">Daily visitor volume over time</p>
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-bold text-[#0f2744]">{summary?.avgTraffic}</div>
                            <div className="text-xs text-gray-400">Avg. Daily Visitors</div>
                        </div>
                    </div>
                    
                    <div className="h-64 w-full relative">
                        <SimpleLineChart data={analysisData.map(d => d.visitors)} labels={analysisData.map(d => d.date)} color="#3B82F6" />
                    </div>
                </div>

                {/* Summary & Extremes */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm h-full flex flex-col justify-between">
                        <h3 className="font-bold text-[#0f2744] mb-4">Performance Highlights</h3>
                        
                        <div className="space-y-6">
                            <div className="p-4 bg-green-50 rounded-xl border border-green-100">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-bold text-green-700 uppercase tracking-wide">Highest Peak</span>
                                    <TrendingUp className="w-4 h-4 text-green-600" />
                                </div>
                                <div className="text-2xl font-bold text-[#0f2744]">{summary?.highestDay.visitors}</div>
                                <div className="text-xs text-gray-500">Visitors on {summary?.highestDay.date}</div>
                            </div>

                            <div className="p-4 bg-red-50 rounded-xl border border-red-100">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-bold text-red-700 uppercase tracking-wide">Lowest Drop</span>
                                    <TrendingDown className="w-4 h-4 text-red-600" />
                                </div>
                                <div className="text-2xl font-bold text-[#0f2744]">{summary?.lowestDay.visitors}</div>
                                <div className="text-xs text-gray-500">Visitors on {summary?.lowestDay.date}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Interactions Bar Chart */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="font-bold text-[#0f2744]">User Interactions</h3>
                        <BarChart3 className="w-5 h-5 text-gray-400" />
                    </div>
                    <div className="h-64 flex items-end justify-between space-x-2 md:space-x-4">
                        {analysisData.slice(-7).map((day, idx) => ( // Show last 7 for cleaner bar view
                            <div key={idx} className="flex-1 flex flex-col justify-end group">
                                <div className="w-full bg-[#3B82F6]/20 rounded-t-sm relative transition-all duration-300 group-hover:bg-[#3B82F6]" style={{ height: `${(day.interactions / (Math.max(...analysisData.map(d=>d.interactions)) || 1)) * 100}%` }}>
                                    <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-[#0f2744] text-white text-[10px] px-2 py-1 rounded whitespace-nowrap z-10">
                                        {day.interactions} Actions
                                    </div>
                                </div>
                                <div className="text-[10px] text-gray-400 text-center mt-2 truncate">{day.date}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* User Type Pie Chart (Visual approximation) */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="font-bold text-[#0f2744]">User Demographics</h3>
                        <PieIcon className="w-5 h-5 text-gray-400" />
                    </div>
                    
                    <div className="flex flex-col md:flex-row items-center justify-center gap-8 h-64">
                        {/* CSS Conic Gradient Pie */}
                        <div 
                            className="w-48 h-48 rounded-full shadow-inner relative"
                            style={{ 
                                background: `conic-gradient(#3B82F6 0% ${((summary?.totalNew || 0) / (summary?.totalVisitors || 1)) * 100}%, #6366F1 ${((summary?.totalNew || 0) / (summary?.totalVisitors || 1)) * 100}% 100%)` 
                            }}
                        >
                            <div className="absolute inset-8 bg-white rounded-full flex items-center justify-center flex-col shadow-sm">
                                <span className="text-sm text-gray-400">Total</span>
                                <span className="text-xl font-bold text-[#0f2744]">{summary?.totalVisitors.toLocaleString()}</span>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center">
                                <div className="w-3 h-3 rounded-full bg-[#3B82F6] mr-3"></div>
                                <div>
                                    <div className="text-sm font-bold text-[#0f2744]">{summary?.totalNew.toLocaleString()}</div>
                                    <div className="text-xs text-gray-500">New Users ({Math.round(((summary?.totalNew || 0)/(summary?.totalVisitors || 1))*100)}%)</div>
                                </div>
                            </div>
                            <div className="flex items-center">
                                <div className="w-3 h-3 rounded-full bg-[#6366F1] mr-3"></div>
                                <div>
                                    <div className="text-sm font-bold text-[#0f2744]">{summary?.totalRepeat.toLocaleString()}</div>
                                    <div className="text-xs text-gray-500">Returning ({Math.round(((summary?.totalRepeat || 0)/(summary?.totalVisitors || 1))*100)}%)</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ title, value, trend, icon, isNegative }: any) => (
    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:border-[#3B82F6]/50 transition-colors">
        <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
            <span className={`px-2 py-1 rounded text-xs font-bold flex items-center ${isNegative ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                {isNegative ? <TrendingDown className="w-3 h-3 mr-1" /> : <TrendingUp className="w-3 h-3 mr-1" />}
                {trend}
            </span>
        </div>
        <div className="text-2xl font-bold text-[#0f2744]">{value}</div>
        <div className="text-sm text-gray-500 mt-1">{title}</div>
    </div>
);

const SimpleLineChart = ({ data, labels, color }: { data: number[], labels: string[], color: string }) => {
    const max = Math.max(...data, 1);
    const min = Math.min(...data);
    const range = max - min || 1;
    
    // Create points
    const points = data.map((val, idx) => {
        const x = (idx / (data.length - 1)) * 100;
        const y = 100 - ((val - min) / range) * 100;
        return `${x},${y}`;
    }).join(' ');

    return (
        <svg viewBox="0 0 100 100" className="w-full h-full overflow-visible" preserveAspectRatio="none">
            {/* Grid lines */}
            <line x1="0" y1="25" x2="100" y2="25" stroke="#f3f4f6" strokeWidth="0.5" vectorEffect="non-scaling-stroke" />
            <line x1="0" y1="50" x2="100" y2="50" stroke="#f3f4f6" strokeWidth="0.5" vectorEffect="non-scaling-stroke" />
            <line x1="0" y1="75" x2="100" y2="75" stroke="#f3f4f6" strokeWidth="0.5" vectorEffect="non-scaling-stroke" />
            
            <polyline
                fill="none"
                stroke={color}
                strokeWidth="2"
                points={points}
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            {/* Hover Dots (visual only for end points to keep it simple) */}
            {data.length > 0 && (
                <>
                <circle cx="0" cy={100 - ((data[0]-min)/range)*100} r="1.5" fill="white" stroke={color} strokeWidth="1" vectorEffect="non-scaling-stroke"/>
                <circle cx="100" cy={100 - ((data[data.length-1]-min)/range)*100} r="1.5" fill="white" stroke={color} strokeWidth="1" vectorEffect="non-scaling-stroke"/>
                </>
            )}
            
            {/* X Axis Labels (Simple start/end) */}
            <text x="0" y="115" fontSize="3" fill="#9CA3AF">{labels[0]}</text>
            <text x="100" y="115" fontSize="3" fill="#9CA3AF" textAnchor="end">{labels[labels.length - 1]}</text>
        </svg>
    );
};

const AnalysisSkeleton = () => (
    <div className="space-y-6 animate-pulse">
        <div className="h-16 bg-gray-200 rounded-xl w-full"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1,2,3,4].map(i => <div key={i} className="h-32 bg-gray-200 rounded-xl"></div>)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 h-80 bg-gray-200 rounded-xl"></div>
            <div className="h-80 bg-gray-200 rounded-xl"></div>
        </div>
    </div>
);

export default TrafficAnalysis;