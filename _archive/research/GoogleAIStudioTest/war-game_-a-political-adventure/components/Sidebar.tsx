import React from 'react';
import { type Stats, type MilitaryUnit, type UnitReadiness, type UnitType } from '../types';

interface StatBarProps {
  label: string;
  value: number;
  color: string;
}

const StatBar: React.FC<StatBarProps> = ({ label, value, color }) => (
  <div>
    <div className="flex justify-between items-baseline mb-1">
      <span className="text-sm font-medium text-gray-300">{label}</span>
      <span className="text-lg font-bold" style={{ color }}>{value}</span>
    </div>
    <div className="w-full bg-gray-700 rounded-full h-2.5">
      <div className="h-2.5 rounded-full" style={{ width: `${value}%`, backgroundColor: color }}></div>
    </div>
  </div>
);

const MilitaryUnitDisplay: React.FC<{ units: MilitaryUnit[] }> = ({ units }) => {
  const readinessColorMap: Record<UnitReadiness, string> = {
    High: 'text-green-400 border-green-400',
    Medium: 'text-yellow-400 border-yellow-400',
    Low: 'text-orange-400 border-orange-400',
    Deployed: 'text-blue-400 border-blue-400',
    Damaged: 'text-red-500 border-red-500',
  };

  const unitTypeIcon: Record<UnitType, string> = {
    Naval: '🌊',
    Air: '✈️',
    Ground: '🛡️',
    'Cyber/Intel': '💻',
  };

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-400 border-b border-gray-700 pb-2 pt-4">Order of Battle</h2>
      <div className="space-y-3 mt-3 max-h-60 overflow-y-auto pr-2">
        {units.map((unit) => (
          <div key={unit.id} className="text-sm p-2 bg-gray-800/50 rounded-md">
            <div className="flex justify-between items-center">
              <span className="font-bold text-gray-300">{unitTypeIcon[unit.type]} {unit.name}</span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${readinessColorMap[unit.readiness]}`}>
                {unit.readiness}
              </span>
            </div>
            <div className="text-xs text-gray-400 mt-1">
              <span>Qty: {unit.quantity} | Location: {unit.location}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};


interface SidebarProps {
  stats: Stats;
}

const Sidebar: React.FC<SidebarProps> = ({ stats }) => {
  return (
    <aside className="w-full md:w-80 lg:w-96 bg-gray-900/80 backdrop-blur-sm border-r border-gray-700 p-6 flex flex-col space-y-6">
      <h1 className="text-2xl font-bold text-center text-red-500 tracking-wider uppercase">War Game</h1>
      <div className="bg-gray-800 p-4 rounded-lg">
        <div className="flex justify-between items-center">
          <span className="text-lg font-semibold text-gray-300">Current Turn</span>
          <span className="text-3xl font-bold text-red-400">{stats.currentTurn}</span>
        </div>
      </div>
      <div className="flex-grow space-y-6">
        <h2 className="text-lg font-semibold text-gray-400 border-b border-gray-700 pb-2">Cabinet Status</h2>
        <StatBar label="NSA Affinity (Diplomacy)" value={stats.advisorAffinity.nsa} color="#60a5fa" />
        <StatBar label="CDS Affinity (Military)" value={stats.advisorAffinity.cds} color="#f87171" />
        <StatBar label="GCHQ Affinity (Intel)" value={stats.advisorAffinity.gchq} color="#c084fc" />
        
        <MilitaryUnitDisplay units={stats.militaryResources} />

        <h2 className="text-lg font-semibold text-gray-400 border-b border-gray-700 pb-2 pt-4">National Status</h2>
        <StatBar label="Threat Level" value={stats.threatLevel} color="#f87171" />
        <StatBar label="Domestic Stability" value={stats.domesticStability} color="#facc15" />
        <StatBar label="NATO Backing" value={stats.natoBacking} color="#818cf8" />
      </div>
      <div className="text-center text-xs text-gray-500 mt-auto">
        <p>Based on the Sky News 'War Game' podcast.</p>
        <p>Your choices shape the destiny of nations.</p>
      </div>
    </aside>
  );
};

export default Sidebar;