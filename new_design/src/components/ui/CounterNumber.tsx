import React, { useEffect, useState, useRef } from 'react';
import { useInView } from 'framer-motion';
import { formatCount } from '@/lib/utils';
import { useLanguage } from '@/context/LanguageContext';

interface CounterNumberProps {
  value: string | number;
  duration?: number;
  className?: string;
  prefix?: string;
  suffix?: string;
}

export const CounterNumber: React.FC<CounterNumberProps> = ({
  value,
  duration = 2,
  className = '',
  prefix = '',
  suffix = '',
}) => {
  const { language } = useLanguage();
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });
  const [displayValue, setDisplayValue] = useState<string>('0');

  useEffect(() => {
    if (!isInView) return;

    // Parse clean numeric value if possible
    const numericStr = String(value).replace(/[^0-9.]/g, '');
    const targetNum = parseFloat(numericStr);

    if (isNaN(targetNum)) {
      setDisplayValue(typeof value === 'number' ? formatCount(value, language) : String(value));
      return;
    }

    const startTime = performance.now();
    const isDecimal = String(value).includes('.');

    const animate = (currentTime: number) => {
      const elapsed = (currentTime - startTime) / 1000;
      const progress = Math.min(elapsed / duration, 1);
      
      // Quartic ease out
      const easeProgress = 1 - Math.pow(1 - progress, 4);
      const currentNum = targetNum * easeProgress;

      if (isDecimal) {
        setDisplayValue(currentNum.toFixed(1));
      } else {
        setDisplayValue(formatCount(Math.floor(currentNum), language));
      }

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setDisplayValue(typeof value === 'number' ? formatCount(value, language) : String(value));
      }
    };

    requestAnimationFrame(animate);
  }, [isInView, value, duration, language]);

  return (
    <span ref={ref} className={className}>
      {prefix}
      {displayValue}
      {suffix}
    </span>
  );
};
