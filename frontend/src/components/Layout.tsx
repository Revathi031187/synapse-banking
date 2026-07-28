import { ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { useStore } from '../store/useStore';

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const { sidebarOpen } = useStore();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      <Navbar />
      
      <div className="flex">
        <AnimatePresence>
          {sidebarOpen && <Sidebar />}
        </AnimatePresence>
        
        <motion.main
          className={`flex-1 transition-all duration-300 ${
            sidebarOpen ? 'ml-64' : 'ml-0'
          }`}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="container mx-auto px-6 py-8 max-w-7xl">
            {children}
          </div>
        </motion.main>
      </div>
    </div>
  );
};

export default Layout;

