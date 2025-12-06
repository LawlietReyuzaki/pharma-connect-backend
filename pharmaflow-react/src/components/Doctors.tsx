import React from 'react';
import { DOCTORS } from '../constants';
import Button from './ui/Button';

const Doctors: React.FC = () => {
  return (
    <section id="doctors" className="py-24 bg-[#1A1A1A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-end mb-12">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">Our Specialists</h2>
            <p className="text-gray-400">Top rated doctors available for online consultation.</p>
          </div>
          <Button variant="outline" className="mt-4 md:mt-0">View All Doctors</Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {DOCTORS.map((doctor) => (
            <div key={doctor.id} className="bg-[#0F0F0F] border border-[#333] rounded-xl overflow-hidden hover:shadow-lg hover:shadow-[#00C78E]/5 transition-all">
              <div className="h-48 bg-[#252525] flex items-center justify-center">
                {/* Placeholder Avatar */}
                <div className="w-24 h-24 rounded-full bg-[#333] flex items-center justify-center text-gray-500">
                    <span className="text-2xl font-semibold">{doctor.name.charAt(4)}</span>
                </div>
              </div>
              <div className="p-6">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-semibold text-white">{doctor.name}</h3>
                </div>
                <p className="text-[#00C78E] text-sm font-medium mb-4">{doctor.specialty}</p>
                
                <div className="flex items-center justify-between mb-6">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${doctor.available ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                        {doctor.available ? 'Available' : 'Busy'}
                    </span>
                    <span className="text-xs text-gray-500">4.9 ★</span>
                </div>

                <Button variant="secondary" fullWidth disabled={!doctor.available}>
                  {doctor.available ? 'Book Appointment' : 'Next Available: 2 PM'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Doctors;