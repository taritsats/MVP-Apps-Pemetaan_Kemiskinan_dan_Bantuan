import React from 'react';
import { ShieldCheck, Home, Briefcase, AlertTriangle, Check } from 'lucide-react';

export interface RecommendationData {
  id: string;
  title: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  match: number;
  desc: string;
  estimate: string;
  isReceived: boolean;
}

interface RecommendationCardProps {
  data: RecommendationData;
  isSelected?: boolean;
  isLocked?: boolean;
  onToggle?: (id: string, isReceived: boolean) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  data,
  isSelected = false,
  isLocked = false,
  onToggle
}) => {
  const getIcon = (id: string) => {
    switch (id) {
      case 'pkh': return <Briefcase size={20} className="text-blue" />;
      case 'rutilahu': return <Home size={20} className="text-orange" />;
      default: return <ShieldCheck size={20} className="text-cyan" />;
    }
  };

  return (
    <div 
      className={`rec-card ${isSelected ? 'selected' : ''} ${data.isReceived ? 'disabled' : ''} ${isLocked ? 'locked' : ''}`}
      onClick={() => onToggle && onToggle(data.id, data.isReceived)}
    >
      {/* Checkbox Area */}
      {!data.isReceived && (
        <div className="rec-checkbox">
          {isSelected ? <Check size={16} className="text-white" /> : null}
        </div>
      )}
      
      <div className="rec-card-header flex-between">
        <div className="rec-icon">
          {getIcon(data.id)}
        </div>
        <div className="rec-priority-col">
          <span className={`priority-badge ${data.priority.toLowerCase()}`}>
            PRIORITY: {data.priority}
          </span>
          <span className="match-text">{data.match}% Match</span>
        </div>
      </div>
      
      <h4 className="rec-title">{data.title}</h4>
      
      {data.isReceived && (
        <div className="received-warning">
          <AlertTriangle size={14} />
          Sudah Menerima Program Ini
        </div>
      )}
      
      <p className="rec-desc">{data.desc}</p>
      
      <div className="rec-estimate">
        Estimasi: {data.estimate}
      </div>
    </div>
  );
};
