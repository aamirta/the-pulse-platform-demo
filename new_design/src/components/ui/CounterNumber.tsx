import React, { useEffect, useState, useRef } from 'react';
import { useInView } from 'framer-motion';

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
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });
  const [displayValue, setDisplayValue] = useState<string>('0');

  useEffect(() => {
    if (!isInView) return;

    // Parse clean numeric value if possible
    const numericStr = String(value).replace(/[^0-9.]/g, '');
    const targetNum = parseFloat(numericStr);

    if (isNaN(targetNum)) {
      setDisplayValue(String(value));
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
        setDisplayValue(Math.floor(currentNum).toLocaleString());
      }

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setDisplayValue(String(value));
      }
    };

    requestAnimationFrame(animate);
  }, [isInView, value, duration]);

  return (
    <span ref={ref} className={className}>
      {prefix}
      {displayValue}
      {suffix}
    </span>
  );
};
