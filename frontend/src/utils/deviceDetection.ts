/**
 * Automatic Device and Browser Detection Utility
 * Production-ready context detection without user input
 */

export interface DeviceInfo {
  type: 'mobile' | 'tablet' | 'desktop';
  os: string;
  browser: string;
  screenSize: string;
  isTouchDevice: boolean;
}

export interface LocationInfo {
  type: 'home' | 'work' | 'store' | 'other';
  timezone: string;
  estimatedLocation?: string;
}

export interface SessionInfo {
  sessionId: string;
  startTime: number;
  currentDuration: number;
  pageViews: number;
  lastActivity: number;
}

/**
 * Detect device type from user agent and screen size
 */
export const detectDevice = (): DeviceInfo => {
  const ua = navigator.userAgent;
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  // Detect device type
  let type: 'mobile' | 'tablet' | 'desktop' = 'desktop';
  if (/Mobile|Android|iPhone/i.test(ua) && window.innerWidth < 768) {
    type = 'mobile';
  } else if (/iPad|Android/i.test(ua) && window.innerWidth >= 768 && window.innerWidth < 1024) {
    type = 'tablet';
  }
  
  // Detect OS
  let os = 'Unknown';
  if (/Windows/i.test(ua)) os = 'Windows';
  else if (/Mac/i.test(ua)) os = 'MacOS';
  else if (/Linux/i.test(ua)) os = 'Linux';
  else if (/Android/i.test(ua)) os = 'Android';
  else if (/iOS|iPhone|iPad/i.test(ua)) os = 'iOS';
  
  // Detect browser
  let browser = 'Unknown';
  if (/Chrome/i.test(ua) && !/Edge|Edg/i.test(ua)) browser = 'Chrome';
  else if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) browser = 'Safari';
  else if (/Firefox/i.test(ua)) browser = 'Firefox';
  else if (/Edge|Edg/i.test(ua)) browser = 'Edge';
  
  const screenSize = `${window.innerWidth}x${window.innerHeight}`;
  
  return {
    type,
    os,
    browser,
    screenSize,
    isTouchDevice
  };
};

/**
 * Estimate location based on time and timezone
 * In production, this would use IP geolocation or GPS
 */
export const detectLocation = (): LocationInfo => {
  const hour = new Date().getHours();
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  
  // Simple heuristic: work hours = work, otherwise = home
  // In production, use IP geolocation API or GPS
  let type: 'home' | 'work' | 'store' | 'other' = 'home';
  if (hour >= 9 && hour <= 17 && [1, 2, 3, 4, 5].includes(new Date().getDay())) {
    type = 'work';
  }
  
  return {
    type,
    timezone,
    estimatedLocation: timezone
  };
};

/**
 * Get current session information
 */
export const getSessionInfo = (): SessionInfo => {
  const sessionKey = 'app_session_info';
  const stored = localStorage.getItem(sessionKey);
  
  if (stored) {
    const session = JSON.parse(stored);
    const currentTime = Date.now();
    
    // Update duration and last activity
    session.currentDuration = Math.floor((currentTime - session.startTime) / 1000);
    session.lastActivity = currentTime;
    
    localStorage.setItem(sessionKey, JSON.stringify(session));
    return session;
  } else {
    // Create new session
    const newSession: SessionInfo = {
      sessionId: generateSessionId(),
      startTime: Date.now(),
      currentDuration: 0,
      pageViews: 1,
      lastActivity: Date.now()
    };
    
    localStorage.setItem(sessionKey, JSON.stringify(newSession));
    return newSession;
  }
};

/**
 * Increment page view count
 */
export const trackPageView = (): void => {
  const sessionKey = 'app_session_info';
  const stored = localStorage.getItem(sessionKey);
  
  if (stored) {
    const session = JSON.parse(stored);
    session.pageViews += 1;
    session.lastActivity = Date.now();
    localStorage.setItem(sessionKey, JSON.stringify(session));
  }
};

/**
 * Generate unique session ID
 */
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Get complete automatic context for NBA generation
 */
export const getAutomaticContext = () => {
  const device = detectDevice();
  const location = detectLocation();
  const session = getSessionInfo();
  const now = new Date();
  
  return {
    // Device info
    device: device.type === 'mobile' ? 'mobile_app' : device.type,
    deviceInfo: device,
    
    // Location info
    location: location.type,
    locationInfo: location,
    
    // Session info
    session_duration: session.currentDuration,
    sessionInfo: session,
    
    // Time info
    hour: now.getHours(),
    day_of_week: now.getDay(),
    is_weekend: now.getDay() === 0 || now.getDay() === 6,
    
    // Additional context
    pages_viewed: session.pageViews,
    timestamp: now.toISOString()
  };
};

/**
 * Generate varied context based on customer ID for demo purposes
 * In production, this would come from actual user behavior tracking
 */
export const generateContextForCustomer = (customerId: string) => {
  // Use customer ID to seed "random" but consistent values
  const seed = customerId.split('_')[1] ? parseInt(customerId.split('_')[1]) : 0;
  
  // Device varies by customer
  const devices = ['mobile_app', 'desktop', 'tablet'];
  const device = devices[seed % 3];
  
  // Location varies by customer
  const locations = ['home', 'work', 'store', 'other'];
  const location = locations[seed % 4];
  
  // Session duration varies (1-20 minutes)
  const sessionDuration = 60 + (seed % 20) * 60; // 1-20 minutes in seconds
  
  // Pages viewed varies (1-15 pages)
  const pagesViewed = 1 + (seed % 15);
  
  // Current time
  const now = new Date();
  
  return {
    device,
    location,
    session_duration: sessionDuration,
    pages_viewed: pagesViewed,
    hour: now.getHours(),
    day_of_week: now.getDay(),
    is_weekend: now.getDay() === 0 || now.getDay() === 6,
    timestamp: now.toISOString()
  };
};

/**
 * Get device label for display
 */
export const getDeviceLabelFromType = (deviceType: string): string => {
  const labels: Record<string, string> = {
    'mobile_app': '📱 Mobile App',
    'desktop': '💻 Desktop',
    'tablet': '📲 Tablet'
  };
  return labels[deviceType] || deviceType;
};

/**
 * Get location label for display
 */
export const getLocationLabelFromType = (locationType: string): string => {
  const labels: Record<string, string> = {
    'home': '🏠 Home',
    'work': '🏢 Work',
    'store': '🏪 Store',
    'other': '🌍 Other'
  };
  return labels[locationType] || locationType;
};

