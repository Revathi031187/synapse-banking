import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import { getCustomers, getProducts, getTransactions, getBehavioralEvents } from '../services/api';
import { useStore } from '../store/useStore';

const DataViewer = () => {
  const { systemStatus } = useStore();
  const [activeTab, setActiveTab] = useState('customers');

  const { data: customers, isLoading: loadingCustomers } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
    enabled: systemStatus.data_generated,
  });

  const { data: products, isLoading: loadingProducts } = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
    enabled: systemStatus.data_generated,
  });

  const { data: transactions, isLoading: loadingTransactions } = useQuery({
    queryKey: ['transactions'],
    queryFn: getTransactions,
    enabled: systemStatus.data_generated,
  });

  const { data: behavioral, isLoading: loadingBehavioral } = useQuery({
    queryKey: ['behavioral'],
    queryFn: getBehavioralEvents,
    enabled: systemStatus.data_generated,
  });

  if (!systemStatus.data_generated) {
    return (
      <Card className="text-center py-12">
        <span className="text-6xl mb-4 block">⚠️</span>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">No Data Generated</h2>
        <p className="text-gray-600">Please generate synthetic data from the Overview page.</p>
      </Card>
    );
  }

  const handleDownload = (dataType: string, data: any[]) => {
    const csvContent = convertToCSV(data);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${dataType}.csv`;
    a.click();
  };

  const convertToCSV = (data: any[]) => {
    if (!data || data.length === 0) return '';
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    for (const row of data) {
      const values = headers.map(header => {
        const val = row[header];
        return typeof val === 'string' ? `"${val}"` : val;
      });
      csvRows.push(values.join(','));
    }
    return csvRows.join('\n');
  };

  const tabs = [
    { id: 'customers', label: '👥 Customers', data: customers, loading: loadingCustomers, count: customers?.length || 0 },
    { id: 'products', label: '🛍️ Products', data: products, loading: loadingProducts, count: products?.length || 0 },
    { id: 'transactions', label: '💳 Transactions', data: transactions, loading: loadingTransactions, count: transactions?.length || 0 },
    { id: 'behavioral', label: '📊 Behavioral Events', data: behavioral, loading: loadingBehavioral, count: behavioral?.length || 0 },
  ];

  const activeData = tabs.find(t => t.id === activeTab);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h1 className="text-4xl font-black text-gray-900 mb-2">💾 Synthetic Data Viewer</h1>
      <p className="text-xl text-gray-600 mb-8">View and download all generated synthetic data</p>

      {/* Tab Navigation */}
      <div className="flex gap-3 mb-6 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-6 py-3 rounded-lg font-bold whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg scale-105'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            {tab.label}
            <span className="ml-2 bg-white bg-opacity-20 px-2 py-1 rounded text-sm">
              {tab.count.toLocaleString()}
            </span>
          </button>
        ))}
      </div>

      {/* Data Display */}
      <Card>
        {activeData?.loading ? (
          <LoadingSpinner message={`Loading ${activeTab}...`} />
        ) : activeData?.data && activeData.data.length > 0 ? (
          <>
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-3xl font-black text-blue-600">{activeData.count.toLocaleString()}</div>
                <div className="text-sm text-gray-700 font-semibold">Total Records</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-3xl font-black text-green-600">{Object.keys(activeData.data[0] || {}).length}</div>
                <div className="text-sm text-gray-700 font-semibold">Columns</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg text-center">
                <div className="text-3xl font-black text-purple-600">{((JSON.stringify(activeData.data).length / 1024).toFixed(1))}KB</div>
                <div className="text-sm text-gray-700 font-semibold">Data Size</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg text-center">
                <Button
                  onClick={() => handleDownload(activeTab, activeData.data!)}
                  variant="primary"
                  size="sm"
                  className="w-full"
                >
                  ⬇️ Download CSV
                </Button>
              </div>
            </div>

            {/* Data Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    {Object.keys(activeData.data[0] || {}).map((key) => (
                      <th key={key} className="px-4 py-3 text-left font-black text-gray-900 border-b-2 border-gray-300">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {activeData.data.slice(0, 50).map((row, idx) => (
                    <tr key={idx} className="border-b border-gray-200 hover:bg-blue-50 transition-colors">
                      {Object.values(row).map((value: any, vidx) => (
                        <td key={vidx} className="px-4 py-3 text-gray-700 font-medium">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {activeData.count > 50 && (
              <div className="mt-4 text-center">
                <p className="text-gray-600 font-semibold">
                  Showing first 50 of {activeData.count.toLocaleString()} records
                </p>
                <p className="text-sm text-gray-500 mt-1">Download CSV to view all records</p>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <span className="text-6xl mb-4 block">📭</span>
            <h3 className="text-xl font-bold text-gray-900 mb-2">No Data Available</h3>
            <p className="text-gray-600">This dataset is empty or failed to load.</p>
          </div>
        )}
      </Card>

      {/* Download All */}
      <Card className="mt-8 bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-black text-gray-900 mb-2">📦 Download All Data</h3>
            <p className="text-gray-600">Get all datasets in a single ZIP file</p>
          </div>
          <Button
            onClick={() => {
              const allData = {
                customers: customers || [],
                products: products || [],
                transactions: transactions || [],
                behavioral: behavioral || [],
              };
              Object.entries(allData).forEach(([key, data]) => {
                if (data.length > 0) {
                  handleDownload(key, data);
                }
              });
            }}
            variant="primary"
            size="lg"
          >
            ⬇️ Download All (CSV)
          </Button>
        </div>
      </Card>
    </motion.div>
  );
};

export default DataViewer;
