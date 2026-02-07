import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { FolderOpen, Database, CheckCircle2, AlertCircle, Eye, X, Upload } from 'lucide-react';

export default function BankingDataLoader() {
  const queryClient = useQueryClient();
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [viewingTable, setViewingTable] = useState<string | null>(null);
  const [tableData, setTableData] = useState<any | null>(null);
  
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';
  
  // Fetch available datasets
  const { data: datasetsData, isLoading } = useQuery({
    queryKey: ['banking-datasets'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/datasets`);
      return res.json();
    }
  });
  
  // Load dataset mutation
  const loadMutation = useMutation({
    mutationFn: async (datasetName: string) => {
      const res = await fetch(`${API_BASE_URL}/api/banking/datasets/load`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_name: datasetName })
      });
      if (!res.ok) throw new Error('Failed to load dataset');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['banking-status'] });
      // Clear Agent A results when new dataset is loaded
      queryClient.removeQueries({ queryKey: ['banking-agent-a-results'] });
    }
  });
  
  // Function to view table data
  const handleViewTable = async (tableName: string) => {
    try {
      const datasetToUse = selectedDataset || datasetsData?.datasets?.[0]?.name || 'banking_v1';
      const res = await fetch(`${API_BASE_URL}/api/banking/datasets/view/${datasetToUse}/${tableName}`);
      
      if (!res.ok) {
        console.error('Failed to fetch table:', res.status, res.statusText);
        alert(`Failed to load table: ${res.statusText}`);
        return;
      }
      
      const data = await res.json();
      console.log('✅ Table data loaded:', tableName, data);
      setTableData(data);
      setViewingTable(tableName);
    } catch (error) {
      console.error('Error loading table:', error);
      alert(`Error loading table: ${error}`);
    }
  };
  
  const datasets = datasetsData?.datasets || [];
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700 mx-auto mb-4"></div>
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
          <FolderOpen className="w-10 h-10 text-blue-700" />
          <span>🏦 Banking Data Loader</span>
        </h1>
        <p className="text-gray-600 text-lg">Select and load the banking customer dataset to begin persona analysis</p>
      </div>
      
      {/* Dataset Selection */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Available Datasets</h2>
        
        {datasets.length === 0 && (
          <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
              <div>
                <div className="text-amber-900 font-semibold mb-2">No Datasets Found</div>
                <p className="text-amber-800 text-sm mb-3">
                  No pre-loaded datasets detected. Generate banking data by running:
                </p>
                <code className="block bg-gray-900 text-gray-100 p-3 rounded-lg text-sm font-mono">
                  python utils/banking_data_generator.py
                </code>
                <p className="text-amber-800 text-xs mt-2">
                  This will generate 5,000 banking customers with realistic profiles and transactions
                </p>
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
              className={`bg-white rounded-xl shadow-sm border-2 cursor-pointer transition-all duration-300 ${
                selectedDataset === dataset.name
                  ? 'border-blue-500 shadow-lg bg-blue-50'
                  : 'border-blue-200 hover:border-blue-400 hover:shadow-md'
              }`}
              onClick={() => setSelectedDataset(dataset.name)}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
                        <span>🏦</span>
                        <span>{dataset.display_name || dataset.name}</span>
                      </h3>
                      {dataset.status === 'ready' && (
                        <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                          <CheckCircle2 className="w-4 h-4 mr-1" />
                          Ready
                        </span>
                      )}
                      {dataset.status === 'not_generated' && (
                        <span className="inline-flex items-center px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-semibold">
                          <AlertCircle className="w-4 h-4 mr-1" />
                          Generate First
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 text-sm mb-3">{dataset.description}</p>
                    
                    {/* Tables Info */}
                    {dataset.tables && (
                      <div className="grid md:grid-cols-3 gap-3 mt-4">
                        {dataset.tables.map((table: any) => (
                          <div key={table.name} className="bg-white rounded-lg border border-blue-100 p-3">
                            <div className="flex items-center justify-between mb-1">
                              <div className="text-sm font-semibold text-gray-900">{table.display_name}</div>
                              {table.loaded && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleViewTable(table.name);
                                  }}
                                  className="text-blue-700 hover:text-blue-800 p-1"
                                  title="View data"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                            <div className="text-xs text-gray-600">
                              {table.loaded ? (
                                <span className="flex items-center gap-1">
                                  <CheckCircle2 className="w-3 h-3 text-green-600" />
                                  {table.row_count?.toLocaleString() || 0} rows
                                </span>
                              ) : (
                                <span className="text-amber-600">Not loaded</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Load Button */}
                <div className="mt-4 pt-4 border-t border-blue-100">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      loadMutation.mutate(dataset.name);
                    }}
                    disabled={loadMutation.isPending || dataset.status !== 'ready'}
                    className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loadMutation.isPending ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Loading Dataset...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-5 h-5" />
                        <span>Load Dataset into System</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
      
      {loadMutation.isSuccess && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-green-50 border-2 border-green-300 rounded-xl p-6"
        >
          <div className="flex items-start space-x-3">
            <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
            <div>
              <div className="text-green-900 font-bold text-lg mb-2">✅ Dataset Loaded Successfully!</div>
              <p className="text-green-800 text-sm mb-3">
                The banking dataset has been loaded into ChromaDB. You can now proceed to run Agent A for customer segmentation.
              </p>
              <a
                href="/banking/agent-a"
                className="inline-flex items-center gap-2 bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-800 transition-colors text-sm"
              >
                Proceed to Agent A →
              </a>
            </div>
          </div>
        </motion.div>
      )}
      
      {loadMutation.isError && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-red-50 border-2 border-red-300 rounded-xl p-6"
        >
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
            <div>
              <div className="text-red-900 font-bold text-lg mb-2">Failed to Load Dataset</div>
              <p className="text-red-800 text-sm">
                {(loadMutation.error as Error).message}
              </p>
            </div>
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
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={() => {
              setViewingTable(null);
              setTableData(null);
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="bg-gradient-to-r from-blue-700 to-blue-800 text-white p-6 flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold flex items-center gap-2">
                    <Database className="w-6 h-6" />
                    {viewingTable}
                  </h3>
                  <p className="text-blue-100 text-sm mt-1">
                    Showing {tableData.data?.length || 0} of {tableData.total_rows?.toLocaleString() || 0} rows
                  </p>
                </div>
                <button
                  onClick={() => {
                    setViewingTable(null);
                    setTableData(null);
                  }}
                  className="text-white hover:bg-blue-600 p-2 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              {/* Modal Body */}
              <div className="p-6 overflow-auto max-h-[calc(90vh-120px)]">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        {tableData.columns?.map((col: string) => (
                          <th
                            key={col}
                            className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {tableData.data?.map((row: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          {tableData.columns?.map((col: string) => (
                            <td
                              key={col}
                              className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap"
                            >
                              {typeof row[col] === 'number' 
                                ? row[col].toLocaleString()
                                : row[col] !== null && row[col] !== undefined
                                  ? String(row[col])
                                  : '-'
                              }
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
