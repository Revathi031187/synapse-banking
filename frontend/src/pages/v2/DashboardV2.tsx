import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

const DashboardV2 = () => {
  const { data: status } = useQuery({
    queryKey: ['v2-status'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/status');
      return response.json();
    },
  });

  const pipelineStatus = status?.pipeline_status || {};
  
  const steps = [
    {
      number: 1,
      title: 'Load Data',
      description: 'Select a pre-loaded dataset or upload your own',
      icon: '📦',
      link: '/data-loader',
      complete: pipelineStatus.data_loaded,
      color: 'from-blue-500 to-cyan-500'
    },
    {
      number: 2,
      title: 'Build Personas',
      description: 'Agent A analyzes customers and creates personas',
      icon: '🤖',
      link: '/agent-a',
      complete: pipelineStatus.agent_a_complete,
      color: 'from-purple-500 to-pink-500'
    },
    {
      number: 3,
      title: 'Match Products',
      description: 'Agent B recommends products for each persona',
      icon: '🎯',
      link: '/agent-b',
      complete: pipelineStatus.agent_b_complete,
      color: 'from-green-500 to-emerald-500'
    }
  ];

  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
          Welcome to Personalization Platform v2
        </h1>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto">
          Build advanced AI-powered customer personas and generate personalized product
          recommendations using state-of-the-art machine learning and generative AI.
        </p>
      </div>

      {/* Pipeline Steps */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {steps.map((step, index) => (
          <div key={step.number} className="relative">
            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div className="hidden md:block absolute top-1/2 left-full w-full h-0.5 bg-gradient-to-r from-purple-500/50 to-transparent transform -translate-y-1/2 z-0" />
            )}
            
            {/* Step Card */}
            <Link to={step.link}>
              <div className={`
                relative z-10 bg-white/5 backdrop-blur-sm rounded-xl p-6 
                border-2 transition-all duration-300 hover:scale-105
                ${step.complete 
                  ? 'border-green-500/50 shadow-lg shadow-green-500/20'
                  : 'border-purple-500/20 hover:border-purple-500/50'
                }
              `}>
                {/* Complete Badge */}
                {step.complete && (
                  <div className="absolute -top-3 -right-3 bg-green-500 text-white rounded-full p-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}

                {/* Step Number */}
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br ${step.color} text-white font-bold text-xl mb-4`}>
                  {step.number}
                </div>

                {/* Icon */}
                <div className="text-4xl mb-3">{step.icon}</div>

                {/* Title & Description */}
                <h3 className="text-xl font-bold text-white mb-2">{step.title}</h3>
                <p className="text-gray-400 text-sm">{step.description}</p>

                {/* CTA */}
                <div className="mt-4">
                  <span className="text-purple-400 text-sm font-medium hover:text-purple-300">
                    {step.complete ? 'View Results →' : 'Get Started →'}
                  </span>
                </div>
              </div>
            </Link>
          </div>
        ))}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        <FeatureCard
          icon="🔬"
          title="Advanced Clustering"
          description="K-Means, DBSCAN, and Hierarchical clustering with automatic parameter optimization"
          items={['Silhouette Score', 'Elbow Method', 'PCA & t-SNE Visualization']}
        />
        <FeatureCard
          icon="💰"
          title="RFM Analysis"
          description="Comprehensive Recency, Frequency, Monetary analysis with 9 customer segments"
          items={['Champions', 'Loyal Customers', 'At Risk', 'Hibernating']}
        />
        <FeatureCard
          icon="🤖"
          title="Generative AI"
          description="Together AI integration for persona names, descriptions, and reasoning"
          items={['Llama 3.1 8B', 'Semantic Embeddings', 'Creative Personas']}
        />
        <FeatureCard
          icon="📊"
          title="Rich Visualizations"
          description="Interactive charts and plots for comprehensive insights"
          items={['Scatter Plots', 'Heatmaps', 'Dendrograms', 'Distribution Charts']}
        />
      </div>

      {/* Quick Stats */}
      {status?.current_dataset && (
        <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6 border border-purple-500/30">
          <h3 className="text-lg font-bold text-white mb-4">Current Session</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatItem label="Dataset" value={status.current_dataset.replace('_', ' ').toUpperCase()} />
            <StatItem label="Data Loaded" value={pipelineStatus.data_loaded ? 'YES' : 'NO'} />
            <StatItem label="Agent A" value={pipelineStatus.agent_a_complete ? 'COMPLETE' : 'PENDING'} />
            <StatItem label="Agent B" value={pipelineStatus.agent_b_complete ? 'COMPLETE' : 'PENDING'} />
          </div>
        </div>
      )}
    </div>
  );
};

interface FeatureCardProps {
  icon: string;
  title: string;
  description: string;
  items: string[];
}

const FeatureCard = ({ icon, title, description, items }: FeatureCardProps) => {
  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-sm mb-4">{description}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-xs text-purple-300 flex items-center space-x-2">
            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full"></span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

interface StatItemProps {
  label: string;
  value: string;
}

const StatItem = ({ label, value }: StatItemProps) => {
  return (
    <div>
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className="text-sm font-bold text-purple-300 uppercase">{value}</div>
    </div>
  );
};

export default DashboardV2;

