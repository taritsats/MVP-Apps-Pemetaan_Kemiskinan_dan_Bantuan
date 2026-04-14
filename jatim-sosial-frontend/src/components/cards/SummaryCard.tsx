import React from 'react';

interface SummaryCardProps {
  label: string;
  icon: React.ReactNode;
  value: React.ReactNode;
  maxValue?: string;
  progress?: {
    value: number; // percentage
    colorClass: string; // e.g. "orange", "green"
  };
  desc?: string;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  label,
  icon,
  value,
  maxValue,
  progress,
  desc
}) => {
  return (
    <div className="summary-card">
      <div className="summary-card-header">
        <span className="label">{label}</span>
        {icon}
      </div>
      <div className={`summary-card-value ${progress ? 'with-progress' : ''}`}>
        {progress ? (
          <>
            <div className="progress-bar-container">
              <div 
                className={`progress-bar ${progress.colorClass}`} 
                style={{ width: `${progress.value}%` }}
              ></div>
            </div>
            <span className="percent-val">{value}</span>
          </>
        ) : (
          <>
            <span className="big-num">{value}</span>
            {maxValue && <span className="max-num">{maxValue}</span>}
          </>
        )}
      </div>
      {desc && <p className="summary-desc">{desc}</p>}
    </div>
  );
};
