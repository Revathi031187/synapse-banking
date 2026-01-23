import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';

const DataLoaderPage = () => {
  const queryClient = useQueryClient();
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [uploadMode, setUploadMode] = useState<string>(''); // 'customers', 'products', 'transactions'

  // Fetch available datasets
  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['available-datasets'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/datasets/available');
      const data = await response.json();
      return data.datasets;
    },
  });

  // Generate dataset mutation
  const generateMutation = useMutation({
    mutationFn: async (datasetName: string) => {
      const response = await fetch(`http://localhost:8001/api/v2/datasets/generate/${datasetName}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to generate dataset');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['available-datasets'] });
      queryClient.invalidateQueries({ queryKey: ['v2-status'] });
    },
  });

  // Load dataset mutation
  const loadMutation = useMutation({
    mutationFn: async (datasetName: string) => {
      const response = await fetch('http://localhost:8001/api/v2/datasets/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_name: datasetName }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to load dataset');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2-status'] });
    },
  });

  // Upload file mutation
  const uploadMutation = useMutation({
    mutationFn: async ({ dataType, file }: { dataType: string; file: File }) => {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`http://localhost:8001/api/v2/datasets/upload/${dataType}`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to upload file');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2-status'] });
      setUploadMode('');
    },
  });

  const handleGenerate = async (datasetName: string) => {
    await generateMutation.mutateAsync(datasetName);
  };

  const handleLoad = async (datasetName: string) => {
    try {
      await loadMutation.mutateAsync(datasetName);
    } catch (error: any) {
      // If dataset doesn't exist, generate it first
      if (error.message.includes('not found')) {
        await generateMutation.mutateAsync(datasetName);
        await loadMutation.mutateAsync(datasetName);
      }
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, dataType: string) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadMutation.mutateAsync({ dataType, file });
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">📦 Data Loader</h1>
        <p className="text-gray-400">
          Select a pre-loaded dataset or upload your own customer, product, and transaction data
        </p>
      </div>

      {/* Pre-loaded Datasets */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-white mb-4">Pre-loaded Datasets</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {datasetsLoading ? (
            <div className="col-span-3 text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
              <p className="text-gray-400 mt-4">Loading datasets...</p>
            </div>
          ) : (
            datasets?.map((dataset: any) => (
              <DatasetCard
                key={dataset.name}
                name={dataset.name}
                displayName={dataset.display_name}
                status={dataset.status}
                onGenerate={handleGenerate}
                onLoad={handleLoad}
                isGenerating={generateMutation.isPending}
                isLoading={loadMutation.isPending}
              />
            ))
          )}
        </div>
      </div>

      {/* Custom Upload */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-4">Upload Custom Data</h2>
        <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
          <p className="text-gray-400 mb-6">
            Upload your own CSV files. You need to provide customers, products, and transactions data.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { type: 'customers', label: 'Customers', icon: '👥', required: ['customer_id', 'name', 'email'] },
              { type: 'products', label: 'Products', icon: '📦', required: ['product_id', 'product_name', 'category', 'price'] },
              { type: 'transactions', label: 'Transactions', icon: '💳', required: ['transaction_id', 'customer_id', 'product_id', 'total_amount'] }
            ].map((item) => (
              <div
                key={item.type}
                className="bg-white/5 rounded-lg p-4 border border-purple-500/10 hover:border-purple-500/30 transition-all"
              >
                <div className="text-2xl mb-2">{item.icon}</div>
                <h3 className="text-white font-medium mb-2">{item.label}</h3>
                <p className="text-xs text-gray-500 mb-3">
                  Required: {item.required.join(', ')}
                </p>
                <label className="block">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => handleFileUpload(e, item.type)}
                    className="hidden"
                  />
                  <div className="bg-purple-600 hover:bg-purple-700 text-white text-sm px-4 py-2 rounded-lg cursor-pointer text-center transition-colors">
                    {uploadMutation.isPending ? 'Uploading...' : 'Choose File'}
                  </div>
                </label>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Status Messages */}
      <AnimatePresence>
        {loadMutation.isSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="fixed bottom-8 right-8 bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg"
          >
            ✅ Dataset loaded successfully!
          </motion.div>
        )}
        {uploadMutation.isSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="fixed bottom-8 right-8 bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg"
          >
            ✅ File uploaded successfully!
          </motion.div>
        )}
        {(loadMutation.isError || uploadMutation.isError) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="fixed bottom-8 right-8 bg-red-600 text-white px-6 py-4 rounded-lg shadow-lg"
          >
            ❌ {loadMutation.error?.message || uploadMutation.error?.message}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

interface DatasetCardProps {
  name: string;
  displayName: string;
  status: string;
  onGenerate: (name: string) => void;
  onLoad: (name: string) => void;
  isGenerating: boolean;
  isLoading: boolean;
}

const DatasetCard = ({ name, displayName, status, onGenerate, onLoad, isGenerating, isLoading }: DatasetCardProps) => {
  const icons: Record<string, string> = {
    ecommerce: '🛍️',
    sports_academy: '⚽',
    banking: '🏦',
  };

  const descriptions: Record<string, string> = {
    ecommerce: '1000 customers, 50+ products, 10K+ transactions',
    sports_academy: '800 students, 32 programs, 2K+ enrollments',
    banking: '1200 customers, 10 services, 3K+ transactions',
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20 hover:border-purple-500/50 transition-all"
    >
      <div className="text-4xl mb-3">{icons[name] || '📊'}</div>
      <h3 className="text-xl font-bold text-white mb-2">{displayName}</h3>
      <p className="text-sm text-gray-400 mb-4">{descriptions[name]}</p>
      
      <div className="space-y-2">
        {status === 'ready' ? (
          <button
            onClick={() => onLoad(name)}
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-4 py-2 rounded-lg font-medium transition-all disabled:opacity-50"
          >
            {isLoading ? 'Loading...' : 'Load Dataset'}
          </button>
        ) : (
          <button
            onClick={() => onGenerate(name)}
            disabled={isGenerating}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-all disabled:opacity-50"
          >
            {isGenerating ? 'Generating...' : 'Generate Dataset'}
          </button>
        )}
      </div>
      
      <div className="mt-3 text-xs text-gray-500">
        Status: <span className={`font-medium ${status === 'ready' ? 'text-green-400' : 'text-yellow-400'}`}>
          {status === 'ready' ? '● Ready' : '○ Not Generated'}
        </span>
      </div>
    </motion.div>
  );
};

export default DataLoaderPage;

