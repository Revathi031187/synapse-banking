/**
 * User Context Management
 * Simulates user authentication and profile for production demo
 */

export interface User {
  id: string;
  name: string;
  email: string;
  customerId: string;
  avatar?: string;
  preferences?: {
    theme?: 'light' | 'dark';
    notifications?: boolean;
  };
}

const DEMO_USERS: User[] = [
  {
    id: 'user_001',
    name: 'Sarah Johnson',
    email: 'sarah.johnson@example.com',
    customerId: 'CUST_000001',
    avatar: '👩‍💼'
  },
  {
    id: 'user_002',
    name: 'Michael Chen',
    email: 'michael.chen@example.com',
    customerId: 'CUST_000007',
    avatar: '👨‍💻'
  },
  {
    id: 'user_003',
    name: 'Emily Rodriguez',
    email: 'emily.r@example.com',
    customerId: 'CUST_000015',
    avatar: '👩‍🎨'
  },
  {
    id: 'user_004',
    name: 'James Wilson',
    email: 'j.wilson@example.com',
    customerId: 'CUST_000023',
    avatar: '👨‍🔬'
  },
  {
    id: 'user_005',
    name: 'Lisa Anderson',
    email: 'lisa.a@example.com',
    customerId: 'CUST_000031',
    avatar: '👩‍🏫'
  }
];

/**
 * Get current logged-in user (simulated)
 * In production, this would come from JWT token, session, or auth provider
 */
export const getCurrentUser = (): User => {
  const storedUser = localStorage.getItem('current_user');
  
  if (storedUser) {
    return JSON.parse(storedUser);
  } else {
    // Default to first demo user
    const defaultUser = DEMO_USERS[0];
    localStorage.setItem('current_user', JSON.stringify(defaultUser));
    return defaultUser;
  }
};

/**
 * Switch user (for demo purposes)
 */
export const switchUser = (userId: string): User | null => {
  const user = DEMO_USERS.find(u => u.id === userId);
  if (user) {
    localStorage.setItem('current_user', JSON.stringify(user));
    return user;
  }
  return null;
};

/**
 * Get all demo users
 */
export const getDemoUsers = (): User[] => {
  return DEMO_USERS;
};

/**
 * Simulate login
 */
export const login = (email: string): User | null => {
  const user = DEMO_USERS.find(u => u.email === email);
  if (user) {
    localStorage.setItem('current_user', JSON.stringify(user));
    return user;
  }
  return null;
};

/**
 * Logout
 */
export const logout = (): void => {
  localStorage.removeItem('current_user');
  localStorage.removeItem('app_session_info');
};

/**
 * Check if user is logged in
 */
export const isAuthenticated = (): boolean => {
  return localStorage.getItem('current_user') !== null;
};

