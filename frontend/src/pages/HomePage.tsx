import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';
import { useStore } from '../store/useStore';
import { getCurrentUser } from '../utils/userContext';
import { getAutomaticContext, getDeviceLabel, getLocationLabel, detectDevice, detectLocation } from '../utils/deviceDetection';

const HomePage = () => {
  const navigate = useNavigate();
  const { systemStatus } = useStore();
  const currentUser = getCurrentUser();
  const autoContext = getAutomaticContext();
  const deviceInfo = detectDevice();
  const locationInfo = detectLocation();

  useEffect(() => {
    // Track page view on mount
    const sessionInfo = autoContext.sessionInfo;
    console.log('Session started:', sessionInfo);
  }, []);

  const features = [
    {
      icon: '🤖',
      title: 'AI-Powered Recommendations',
      description: 'Get personalized product suggestions powered by 5 specialized AI agents',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: '⚡',
      title: 'Real-Time Personalization',
      description: 'Recommendations adapt to your behavior, device, and context automatically',
      color: 'from-purple-500 to-pink-500'
    },
    {
      icon: '🎯',
      title: 'Smart Targeting',
      description: 'Advanced analytics predict what you want before you know it',
      color: 'from-orange-500 to-red-500'
    },
    {
      icon: '✨',
      title: 'Seamless Experience',
      description: 'No manual input needed - everything works automatically in the background',
      color: 'from-green-500 to-emerald-500'
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative overflow-hidden rounded-3xl mb-12"
      >
        <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 p-12 text-white">
          <div className="max-w-4xl">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              className="inline-block text-6xl mb-4"
            >
              {currentUser.avatar || '👋'}
            </motion.div>
            
            <h1 className="text-5xl font-black mb-4 leading-tight">
              Welcome back, {currentUser.name.split(' ')[0]}!
            </h1>
            
            <p className="text-2xl mb-8 opacity-90">
              Your personalized shopping experience powered by advanced AI
            </p>

            <div className="flex gap-4 mb-8">
              <Button 
                onClick={() => navigate('/recommendations')}
                className="bg-white text-purple-600 hover:bg-gray-100 text-lg px-8 py-4"
                size="lg"
              >
                ✨ See My Recommendations
              </Button>
              <Button 
                onClick={() => navigate('/analytics')}
                className="bg-purple-800 text-white hover:bg-purple-900 text-lg px-8 py-4"
                size="lg"
              >
                📊 View Insights
              </Button>
            </div>

            {/* Live Context Display */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <p className="text-sm font-semibold mb-3 opacity-75">🔴 LIVE • Your Current Context</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="opacity-75 mb-1">Device</p>
                  <p className="font-bold">{getDeviceLabel(deviceInfo)}</p>
                </div>
                <div>
                  <p className="opacity-75 mb-1">Location</p>
                  <p className="font-bold">{getLocationLabel(locationInfo)}</p>
                </div>
                <div>
                  <p className="opacity-75 mb-1">Session Time</p>
                  <p className="font-bold">⏱️ {Math.floor(autoContext.session_duration / 60)}m {autoContext.session_duration % 60}s</p>
                </div>
                <div>
                  <p className="opacity-75 mb-1">Pages Viewed</p>
                  <p className="font-bold">👁️ {autoContext.pages_viewed}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Features Grid */}
      <div className="mb-12">
        <h2 className="text-3xl font-black text-gray-900 mb-8">
          🚀 How It Works
        </h2>
        <div className="grid md:grid-cols-2 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index }}
            >
              <Card className="h-full hover:shadow-xl transition-shadow duration-300 border-2 border-gray-100">
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-3xl mb-4 shadow-lg`}>
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Stats Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <h2 className="text-3xl font-black text-gray-900 mb-8">
          📈 Your Impact
        </h2>
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <Card className="bg-gradient-to-br from-blue-600 to-blue-700 text-white text-center p-8">
            <div className="text-5xl font-black mb-2">5</div>
            <div className="text-xl font-semibold opacity-90">AI Agents</div>
            <div className="text-sm opacity-75 mt-2">Working for You</div>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-600 to-purple-700 text-white text-center p-8">
            <div className="text-5xl font-black mb-2">24/7</div>
            <div className="text-xl font-semibold opacity-90">Real-Time</div>
            <div className="text-sm opacity-75 mt-2">Personalization</div>
          </Card>
          
          <Card className="bg-gradient-to-br from-pink-600 to-pink-700 text-white text-center p-8">
            <div className="text-5xl font-black mb-2">100%</div>
            <div className="text-xl font-semibold opacity-90">Automated</div>
            <div className="text-sm opacity-75 mt-2">No Manual Input</div>
          </Card>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200 p-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              🎁 Ready to discover amazing products?
            </h3>
            <p className="text-gray-600 text-lg">
              Our AI has already analyzed your preferences and prepared personalized recommendations
            </p>
          </div>
          <Button 
            onClick={() => navigate('/recommendations')}
            className="bg-gradient-to-r from-green-600 to-blue-600 text-white hover:shadow-xl"
            size="lg"
          >
            Get Started →
          </Button>
        </div>
      </Card>

      {/* System Status Indicator */}
      {systemStatus.system_initialized && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed bottom-6 right-6 bg-green-500 text-white px-4 py-2 rounded-full shadow-lg flex items-center gap-2"
        >
          <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
          <span className="font-semibold text-sm">AI System Active</span>
        </motion.div>
      )}
    </div>
  );
};

export default HomePage;

