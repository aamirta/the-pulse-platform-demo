import React from 'react';
import { motion } from 'framer-motion';
import type { Variants } from 'framer-motion';
import { fadeUp } from '@/lib/motion';

interface ScrollRevealProps {
  children: React.ReactNode;
  variants?: Variants;
  className?: string;
  delay?: number;
  viewportAmount?: number;
  once?: boolean;
}

export const ScrollReveal: React.FC<ScrollRevealProps> = ({
  children,
  variants = fadeUp,
  className = '',
  delay = 0,
  viewportAmount = 0.15,
  once = true,
}) => {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount: viewportAmount }}
      variants={variants}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
};
