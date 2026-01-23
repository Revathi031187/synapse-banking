import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { FolderOpen, Database, CheckCircle2, AlertCircle, Eye, X } from 'lucide-react';

export default function RetailDataLoader() {
  const queryClient = useQueryClient();
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [viewingTable, setViewingTable] = useState<string | null>(null);
  const [tableData, setTableData] = useState<any | null>(null);
  
  // Fetch available datasets
  const { data: datasetsData, isLoading } = useQuery({
    queryKey: ['retail-datasets'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8002/api/retail/datasets');
      return res.json();
    }
  });
  
  // Load dataset mutation
  const loadMutation = useMutation({
    mutationFn: async (datasetName: string) => {
      const res = await fetch('http://localhost:8002/api/retail/datasets/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_name: datasetName })
      });
      if (!res.ok) throw new Error('Failed to load dataset');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['retail-status'] });
    }
  });
  
  // Function to view table data
  const handleViewTable = async (tableName: string) => {
    try {
      const res = await fetch(`http://localhost:8002/api/retail/datasets/view/${selectedDataset}/${tableName}`);
      const data = await res.json();
      setTableData(data);
      setViewingTable(tableName);
    } catch (error) {
      console.error('Error loading table:', error);
    }
  };
  
  const datasets = datasetsData?.datasets || [];
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600 mx-auto mb-4"></div>
          <div className="text-gray-900 text-xl font-semibold">Loading datasets...</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center space-x-3">
          <FolderOpen className="w-10 h-10 text-pink-600" />
          <span>Retail Data Loader</span>
        </h1>
        <p className="text-gray-600 text-lg">Select and load a retail dataset to begin persona analysis</p>
      </div>
      
      {/* Dataset Selection */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Available Datasets</h2>
        
        {datasets.length === 0 && (
          <div className="card bg-yellow-50 border-yellow-300">
            <div className="card-body">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
                <div>
                  <div className="text-yellow-900 font-semibold mb-2">No Datasets Found</div>
                  <p className="text-yellow-800 text-sm mb-3">
                    No pre-loaded datasets detected. Generate data by running:
                  </p>
                  <code className="block bg-gray-900 text-gray-100 p-3 rounded-lg text-sm font-mono">
                    py -3.10 utils/retail_data_generator.py
                  </code>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div className="grid gap-6">
          {datasets.map((dataset: any) => (
            <motion.div
              key={dataset.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`card cursor-pointer transition-all duration-300 ${
                selectedDataset === dataset.name
                  ? 'border-pink-500 shadow-lg bg-pink-50'
                  : 'hover:border-pink-300 hover:shadow-md'
              }`}
              onClick={() => setSelectedDataset(dataset.name)}
            >
              <div className="card-body">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2 flex items-center space-x-2">
                      <span>🛒</span>
                      <span>{dataset.display_name}</span>
                    </h3>
                    <p className="text-gray-600 text-sm">{dataset.description}</p>
                  </div>
                  <div className="text-5xl">🛍️</div>
                </div>
                
                {/* Tables */}
                <div className="grid md:grid-cols-2 gap-3 mb-4">
                  {dataset.tables.map((table: string) => (
                    <div key={table} className="flex items-center justify-between bg-gray-50 border border-gray-200 px-4 py-3 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <Database className="w-4 h-4 text-gray-500" />
                        <span className="text-gray-900 text-sm font-medium">{table}</span>
                      </div>
                      {loadMutation.isSuccess && selectedDataset === dataset.name && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewTable(table);
                          }}
                          className="text-pink-600 hover:text-pink-700 font-medium transition-colors flex items-center space-x-1 text-sm"
                        >
                          <Eye className="w-4 h-4" />
                          <span>View</span>
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Stats */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex items-center space-x-6 text-sm">
                    <div>
                      <span className="text-gray-600">Customers:</span>
                      <span className="text-gray-900 ml-2 font-bold">{dataset.customer_count?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Products:</span>
                      <span className="text-pink-600 ml-2 font-bold">{dataset.product_count}</span>
                    </div>
                  </div>
                  
                  {selectedDataset === dataset.name && (
                    <div className="badge badge-blue flex items-center space-x-1">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Selected</span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
      
      {/* Load Button */}
      {selectedDataset && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-gradient-to-br from-pink-50 to-orange-50 border-pink-300"
        >
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-gray-900 font-bold text-xl mb-2">Ready to Load Dataset</h3>
                <p className="text-gray-700 text-sm">
                  Dataset is pre-loaded in ChromaDB and ready for persona analysis
                </p>
              </div>
              <button
                onClick={() => loadMutation.mutate(selectedDataset)}
                disabled={loadMutation.isPending}
                className="bg-pink-600 hover:bg-pink-700 text-white px-8 py-3 rounded-lg font-semibold transition-all shadow-md hover:shadow-lg disabled:opacity-50 flex items-center space-x-2"
              >
                <CheckCircle2 className="w-5 h-5" />
                <span>{loadMutation.isPending ? 'Confirming...' : 'Confirm Dataset'}</span>
              </button>
            </div>
            
            {loadMutation.isSuccess && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-4 pt-4 border-t border-pink-300"
              >
                <div className="flex items-center space-x-3 mb-3">
                  <CheckCircle2 className="w-6 h-6 text-pink-600" />
                  <span className="font-semibold text-pink-900 text-lg">Dataset Confirmed!</span>
                </div>
                <p className="text-gray-700 text-sm">
                  You can now proceed to Agent A to identify customer personas, or use the agent navigation above.
                </p>
              </motion.div>
            )}
            
            {loadMutation.isError && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-4 pt-4 border-t border-red-300"
              >
                <div className="flex items-center space-x-3">
                  <AlertCircle className="w-6 h-6 text-red-600" />
                  <span className="font-semibold text-red-900">Failed to load dataset</span>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>
      )}
      
      {/* Table Viewer Modal */}
      <AnimatePresence>
        {viewingTable && tableData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setViewingTable(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              className="bg-white border border-gray-300 rounded-xl shadow-2xl max-w-6xl w-full max-h-[85vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="border-b border-gray-200 p-6 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1 flex items-center space-x-2">
                      <Database className="w-6 h-6 text-pink-600" />
                      <span>{viewingTable}</span>
                    </h3>
                    <p className="text-gray-600 text-sm">
                      Showing {tableData.preview_count} of {tableData.record_count} records
                    </p>
                  </div>
                  <button
                    onClick={() => setViewingTable(null)}
                    className="text-gray-500 hover:text-gray-900 transition-colors p-2 hover:bg-gray-200 rounded-lg"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
              </div>
              
              {/* Table Content */}
              <div className="overflow-auto max-h-[calc(85vh-140px)] p-6">
                <table className="w-full text-sm border-collapse">
                  <thead className="sticky top-0 bg-gray-50 border-b-2 border-gray-300">
                    <tr>
                      {tableData.records.length > 0 &&
                        Object.keys(tableData.records[0]).map((key) => (
                          <th key={key} className="text-left px-4 py-3 text-gray-900 font-semibold whitespace-nowrap bg-gray-50">
                            {key}
                          </th>
                        ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.records.map((record: any, idx: number) => (
                      <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                        {Object.values(record).map((value: any, vidx: number) => (
                          <td key={vidx} className="px-4 py-3 text-gray-700 whitespace-nowrap">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
