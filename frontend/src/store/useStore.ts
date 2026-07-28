import { create } from 'zustand';
import type { Customer, Product, SystemStatus, NBAResponse } from '../types';

interface AppState {
  // System state
  systemStatus: SystemStatus;
  setSystemStatus: (status: SystemStatus) => void;
  
  // Data
  customers: Customer[];
  setCustomers: (customers: Customer[]) => void;
  
  products: Product[];
  setProducts: (products: Product[]) => void;
  
  // NBA result
  nbaResult: NBAResponse | null;
  setNbaResult: (result: NBAResponse | null) => void;
  
  // UI state
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  // System state
  systemStatus: {
    data_generated: false,
    system_initialized: false,
    orchestrator_ready: false,
    initializing: false,
  },
  setSystemStatus: (status) => set({ systemStatus: status }),
  
  // Data
  customers: [],
  setCustomers: (customers) => set({ customers }),
  
  products: [],
  setProducts: (products) => set({ products }),
  
  // NBA result
  nbaResult: null,
  setNbaResult: (result) => set({ nbaResult: result }),
  
  // UI state
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  
  loading: false,
  setLoading: (loading) => set({ loading }),
}));

