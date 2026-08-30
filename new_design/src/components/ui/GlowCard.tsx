import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface GlowCardProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: string;
  onClick?: () => void;
}

export const GlowCard: React.FC<GlowCardProps> = ({
  children,
  className = '',
  glowColor = 'rgba(213, 100, 38, 0.12)', // Muted warm terracotta tint
  onClick,
}) => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <motion.div
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ y: -4, transition: { duration: 0.2, ease: 'easeInOut' } }}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      className={`relative overflow-hidden rounded-2xl bg-card/90 dark:bg-card/85 border border-border/50 dark:border-border/40 shadow-soft-sm hover:shadow-soft-lg transition-all duration-200 ease-in-out ${
        onClick ? 'cursor-pointer' : ''
      } ${className}`}
    >
      {/* Dynamic Cursor Light Overlay */}
      {isHovered && (
        <div
          className="pointer-events-none absolute -inset-px transition-opacity duration-300"
          style={{
            background: `radial-gradient(400px circle at ${mousePosition.x}px ${mousePosition.y}px, ${glowColor}, transparent 70%)`,
          }}
        />
      )}

      {/* Glass highlight line on top */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-foreground/10 dark:via-foreground/15 to-transparent pointer-events-none" />

      <div className="relative z-10">{children}</div>
    </motion.div>
  );
};
