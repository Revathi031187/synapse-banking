import { useState } from 'react';
import { motion } from 'framer-motion';
import Card from '../components/Card';
import Button from '../components/Button';
import { getCurrentUser, getDemoUsers, switchUser, logout } from '../utils/userContext';
import { getAutomaticContext, getDeviceLabel, getLocationLabel, detectDevice, detectLocation } from '../utils/deviceDetection';

const ProfilePage = () => {
  const [currentUser, setCurrentUser] = useState(getCurrentUser());
  const demoUsers = getDemoUsers();
  const autoContext = getAutomaticContext();
  const deviceInfo = detectDevice();
  const locationInfo = detectLocation();

  const handleSwitchUser = (userId: string) => {
    const newUser = switchUser(userId);
    if (newUser) {
      setCurrentUser(newUser);
      // Reload page to refresh all data
      window.location.reload();
    }
  };

  const handleLogout = () => {
    logout();
    window.location.reload();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-black text-gray-900 mb-2">
          👤 Your Profile
        </h1>
        <p className="text-xl text-gray-600">
          Manage your account and view your activity
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Profile Card */}
        <div className="lg:col-span-2 space-y-6">
          {/* User Info */}
          <Card className="bg-gradient-to-br from-indigo-600 to-purple-700 text-white">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="text-6xl">{currentUser.avatar || '👤'}</div>
                <div>
                  <h2 className="text-3xl font-black mb-1">{currentUser.name}</h2>
                  <p className="text-indigo-200 text-lg">{currentUser.email}</p>
                  <p className="text-sm text-indigo-300 mt-1">Customer ID: {currentUser.customerId}</p>
                </div>
              </div>
              <Button 
                onClick={handleLogout}
                className="bg-white/20 hover:bg-white/30 text-white border-0"
              >
                🚪 Logout
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <p className="text-indigo-200 text-sm mb-1">Member Since</p>
                <p className="text-xl font-bold">Jan 2024</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <p className="text-indigo-200 text-sm mb-1">Status</p>
                <p className="text-xl font-bold">🏆 VIP Member</p>
              </div>
            </div>
          </Card>

          {/* Activity Stats */}
          <Card>
            <h3 className="text-2xl font-bold text-gray-900 mb-6">📊 Your Activity</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 text-center">
                <div className="text-4xl font-black text-blue-600 mb-2">127</div>
                <div className="text-gray-700 font-semibold">Total Orders</div>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 text-center">
                <div className="text-4xl font-black text-purple-600 mb-2">$8,450</div>
                <div className="text-gray-700 font-semibold">Total Spent</div>
              </div>
              <div className="bg-gradient-to-br from-pink-50 to-pink-100 rounded-xl p-6 text-center">
                <div className="text-4xl font-black text-pink-600 mb-2">4.8</div>
                <div className="text-gray-700 font-semibold">Avg Rating</div>
              </div>
            </div>
          </Card>

          {/* Recent Activity */}
          <Card>
            <h3 className="text-2xl font-bold text-gray-900 mb-6">🕐 Recent Activity</h3>
            <div className="space-y-4">
              {[
                { icon: '🛍️', action: 'Viewed personalized recommendations', time: '2 minutes ago', color: 'bg-blue-100 text-blue-600' },
                { icon: '👁️', action: 'Browsed Electronics category', time: '15 minutes ago', color: 'bg-purple-100 text-purple-600' },
                { icon: '⭐', action: 'Rated a product 5 stars', time: '1 hour ago', color: 'bg-yellow-100 text-yellow-600' },
                { icon: '🎁', action: 'Received special offer', time: '3 hours ago', color: 'bg-green-100 text-green-600' },
              ].map((activity, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className={`w-12 h-12 rounded-full ${activity.color} flex items-center justify-center text-xl`}>
                    {activity.icon}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{activity.action}</p>
                    <p className="text-sm text-gray-500">{activity.time}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </Card>

          {/* Preferences */}
          <Card>
            <h3 className="text-2xl font-bold text-gray-900 mb-6">⚙️ Preferences</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-semibold text-gray-900">Email Notifications</p>
                  <p className="text-sm text-gray-500">Receive personalized offers and updates</p>
                </div>
                <button className="bg-green-500 w-12 h-6 rounded-full relative">
                  <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></span>
                </button>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-semibold text-gray-900">AI Recommendations</p>
                  <p className="text-sm text-gray-500">Use AI to personalize your experience</p>
                </div>
                <button className="bg-green-500 w-12 h-6 rounded-full relative">
                  <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></span>
                </button>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-semibold text-gray-900">Location Services</p>
                  <p className="text-sm text-gray-500">Improve recommendations based on location</p>
                </div>
                <button className="bg-green-500 w-12 h-6 rounded-full relative">
                  <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></span>
                </button>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Current Session */}
          <Card className="sticky top-24">
            <h3 className="text-xl font-bold text-gray-900 mb-4">🔴 Current Session</h3>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-gray-600 mb-1">Device</p>
                <p className="font-semibold text-gray-900">{getDeviceLabel(deviceInfo)}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-gray-600 mb-1">Location</p>
                <p className="font-semibold text-gray-900">{getLocationLabel(locationInfo)}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-gray-600 mb-1">Session Duration</p>
                <p className="font-semibold text-gray-900">⏱️ {Math.floor(autoContext.session_duration / 60)}m {autoContext.session_duration % 60}s</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-gray-600 mb-1">Pages Viewed</p>
                <p className="font-semibold text-gray-900">👁️ {autoContext.pages_viewed} pages</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-gray-600 mb-1">Local Time</p>
                <p className="font-semibold text-gray-900">🕐 {new Date().toLocaleTimeString()}</p>
              </div>
            </div>
          </Card>

          {/* Switch User (Demo) */}
          <Card className="bg-gradient-to-br from-orange-50 to-red-50 border-2 border-orange-200">
            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <span>🔄</span> Switch User (Demo)
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Try different user profiles to see how personalization works
            </p>
            <div className="space-y-2">
              {demoUsers.map(user => (
                <button
                  key={user.id}
                  onClick={() => handleSwitchUser(user.id)}
                  disabled={user.id === currentUser.id}
                  className={`w-full text-left p-3 rounded-lg transition-all ${
                    user.id === currentUser.id
                      ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold'
                      : 'bg-white hover:bg-gray-50 text-gray-900'
                  } ${user.id === currentUser.id ? '' : 'hover:shadow-md'}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{user.avatar}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate">{user.name}</p>
                      <p className={`text-xs truncate ${user.id === currentUser.id ? 'text-orange-100' : 'text-gray-500'}`}>
                        {user.customerId}
                      </p>
                    </div>
                    {user.id === currentUser.id && (
                      <span className="text-xs bg-white/20 px-2 py-1 rounded">Active</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </motion.div>
  );
};

export default ProfilePage;

