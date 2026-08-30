import type { Variants, Transition } from 'framer-motion';

// Smooth spring transitions inspired by Apple & Linear UI physics
export const springTransition: Transition = {
  type: 'spring',
  stiffness: 120,
  damping: 20,
  mass: 0.8,
};

export const defaultTransition: Transition = {
  duration: 0.6,
  ease: [0.25, 0.1, 0.25, 1.0],
};

// Orchestrated Container Stagger
export const staggerContainer = (staggerChildren = 0.1, delayChildren = 0): Variants => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren,
      delayChildren,
    },
  },
});

// Fade Up Variant
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: defaultTransition,
  },
};

// Fade Down Variant
export const fadeDown: Variants = {
  hidden: { opacity: 0, y: -24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: defaultTransition,
  },
};

// Simple Fade In
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
};

// Scale In
export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.94 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: springTransition,
  },
};

// Slide In Left
export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: defaultTransition,
  },
};

// Slide In Right
export const slideInRight: Variants = {
  hidden: { opacity: 0, x: 30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: defaultTransition,
  },
};

// Floating element variant for ambient background shapes
export const floatingVariant: Variants = {
  animate: {
    y: [0, -10, 0],
    rotate: [0, 2, 0],
    transition: {
      duration: 6,
      repeat: Infinity,
      repeatType: 'reverse',
      ease: 'easeInOut',
    },
  },
};
