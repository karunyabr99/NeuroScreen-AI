import React from 'react';
import { cn } from '../../lib/utils';

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  color?: string;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  color = "bg-neuro-600",
  className,
  ...props
}) => {
  const boundedValue = Math.max(0, Math.min(100, value));

  return (
    <div
      className={cn("w-full bg-slate-100 rounded-full h-2 overflow-hidden", className)}
      {...props}
    >
      <div
        className={cn("h-full transition-all duration-300 rounded-full", color)}
        style={{ width: `${boundedValue}%` }}
      />
    </div>
  );
};

