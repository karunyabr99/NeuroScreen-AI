import React from 'react';
import { cn } from '../../lib/utils';
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'warning' | 'danger' | 'success';
  title?: string;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  className,
  ...props
}) => {
  const configs = {
    info: {
      bg: "bg-sky-50",
      border: "border-sky-200",
      text: "text-sky-900",
      icon: <Info className="w-5 h-5 text-sky-600 flex-shrink-0" />
    },
    warning: {
      bg: "bg-amber-50",
      border: "border-amber-200",
      text: "text-amber-900",
      icon: <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
    },
    danger: {
      bg: "bg-rose-50",
      border: "border-rose-200",
      text: "text-rose-900",
      icon: <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
    },
    success: {
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      text: "text-emerald-900",
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
    }
  };

  const current = configs[variant];

  return (
    <div
      className={cn(
        "p-4 rounded-xl border flex items-start gap-3",
        current.bg,
        current.border,
        current.text,
        className
      )}
      {...props}
    >
      {current.icon}
      <div className="text-sm">
        {title && <h5 className="font-semibold mb-0.5 tracking-tight">{title}</h5>}
        <div className="opacity-90 leading-relaxed text-xs">{children}</div>
      </div>
    </div>
  );
};

