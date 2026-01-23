import axios from 'axios';
import type { 
  Customer, 
  Product, 
  Transaction, 
  BehavioralEvent, 
  NBAResponse,
  SystemStatus 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds for ML operations
});

// Health check
export const checkHealth = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

// System operations
export const generateSyntheticData = async (config?: {
  num_customers?: number;
  num_products?: number;
  num_transactions?: number;
  num_events?: number;
}) => {
  const response = await api.post('/api/generate-data', config || {});
  return response.data;
};

export const initializeSystem = async () => {
  const response = await api.post('/api/initialize-system');
  return response.data;
};

export const getSystemStatus = async (): Promise<SystemStatus> => {
  const response = await api.get('/api/status');
  return response.data;
};

// Data access
export const getCustomers = async (): Promise<Customer[]> => {
  const response = await api.get('/api/data/customers');
  return response.data;
};

export const getProducts = async (): Promise<Product[]> => {
  const response = await api.get('/api/data/products');
  return response.data;
};

export const getTransactions = async (): Promise<Transaction[]> => {
  const response = await api.get('/api/data/transactions');
  return response.data;
};

export const getBehavioralEvents = async (): Promise<BehavioralEvent[]> => {
  const response = await api.get('/api/data/behavioral');
  return response.data;
};

// NBA Generation
export const generateNBA = async (params: {
  customer_id: string;
  device: string;
  location: string;
  session_duration: number;
  top_n: number;
}): Promise<NBAResponse> => {
  const response = await api.post('/api/generate-nba', params);
  return response.data;
};

// Agent insights
export const getAgentInsights = async (agentId: string) => {
  const response = await api.get(`/api/agent-insights/${agentId}`);
  return response.data;
};

// Individual agent execution
export const executeAgent = async (agentId: string, params: any) => {
  const response = await api.post(`/api/execute-agent/${agentId}`, params);
  return response.data;
};

// Analytics
export const getAnalytics = async () => {
  const response = await api.get('/api/analytics');
  return response.data;
};

// Download data
export const downloadData = async (dataType: string) => {
  const response = await api.get(`/api/download/${dataType}`, {
    responseType: 'blob',
  });
  return response.data;
};

export default api;

