import { ShieldCheck, Zap } from 'lucide-react';

type PremiumBadgeProps = {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showText?: boolean;
};

export function PremiumBadge({
  className = '',
  size = 'md',
  showIcon = true,
  showText = true,
}: PremiumBadgeProps) {
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-xs px-2 py-1',
    lg: 'text-sm px-3 py-1.5',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-3.5 w-3.5',
    lg: 'h-4 w-4',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full bg-gradient-to-r from-yellow-400 to-amber-500 text-black font-medium ${sizeClasses[size]} ${className}`}
    >
      {showIcon && <Zap className={`${iconSizes[size]} mr-1 fill-current`} />}
      {showText && 'Premium'}
    </span>
  );
}
