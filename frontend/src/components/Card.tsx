import { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface CardProps {
  children: ReactNode;
  className?: string;
  gradient?: boolean;
  hover?: boolean;
}

const Card = ({ children, className = '', gradient = false, hover = true }: CardProps) => {
  const baseClass = gradient
    ? 'bg-gradient-to-br from-white to-gray-50'
    : 'bg-white';

  const hoverClass = hover
    ? 'hover:shadow-xl hover:scale-[1.02] transition-all duration-300'
    : '';

  return (
    <motion.div
      className={`${baseClass} rounded-xl shadow-lg p-6 ${hoverClass} ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
};

export default Card;

