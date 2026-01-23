import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, Users, Package, CheckCircle, ArrowRight, Info, Sparkles, Database } from 'lucide-react';
import AcademyDataLoader from './AcademyDataLoader';
import AcademyAgentA from './AcademyAgentA';
import AcademyAgentB from './AcademyAgentB';

type Step = 'welcome' | 'data-loader' | 'agent-a' | 'agent-b';

export default function AcademyWorkflow() {
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [personasDiscovered, setPersonasDiscovered] = useState(false);

  const steps = [
    { id: 'welcome', label: 'Welcome', icon: Sparkles },
    { id: 'data-loader', label: 'Load Data', icon: Database },
    { id: 'agent-a', label: 'Discover Personas', icon: Users },
    { id: 'agent-b', label: 'Get Recommendations', icon: Package }
  ];

  const getStepIndex = (step: Step) => steps.findIndex(s => s.id === step);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Progress Bar */}
      <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          {/* Step Indicator */}
          <div className="flex items-center justify-between mb-2">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = getStepIndex(currentStep) > index;
              const isCurrent = getStepIndex(currentStep) === index;

              return (
                <React.Fragment key={step.id}>
                  <div className="flex items-center">
                    <motion.div
                      initial={{ scale: 0.8 }}
                      animate={{ 
                        scale: isActive ? 1.1 : 1,
                        backgroundColor: isCompleted ? '#10b981' : isActive ? '#059669' : '#e5e7eb'
                      }}
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isCompleted ? 'bg-green-500' : isActive ? 'bg-green-600' : 'bg-gray-300'
                      } transition-all duration-300`}
                    >
                      {isCompleted ? (
                        <CheckCircle className="w-6 h-6 text-white" />
                      ) : (
                        <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                      )}
                    </motion.div>
                    <span className={`ml-3 text-sm font-medium ${
                      isCurrent ? 'text-green-600' : isCompleted ? 'text-gray-700' : 'text-gray-400'
                    }`}>
                      {step.label}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className="flex-1 mx-4">
                      <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: '0%' }}
                          animate={{ 
                            width: getStepIndex(currentStep) > index ? '100%' : '0%'
                          }}
                          transition={{ duration: 0.5 }}
                          className="h-full bg-green-500"
                        />
                      </div>
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Current Step Title */}
          <div className="text-center mt-4">
            <h1 className="text-2xl font-bold text-gray-900">
              {currentStep === 'welcome' && '🏕️ Welcome to Academy Sports Personalization'}
              {currentStep === 'data-loader' && '📊 Step 1: Load Customer Data'}
              {currentStep === 'agent-a' && '👥 Step 2: Discover Customer Personas'}
              {currentStep === 'agent-b' && '🎯 Step 3: Get Personalized Recommendations'}
            </h1>
            <p className="text-gray-600 mt-1">
              {currentStep === 'welcome' && 'Let\'s personalize camping gear for your customers'}
              {currentStep === 'data-loader' && 'Choose which customer dataset to analyze'}
              {currentStep === 'agent-a' && 'Understand who your customers are'}
              {currentStep === 'agent-b' && 'Find the perfect products for each customer'}
            </p>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <AnimatePresence mode="wait">
          {/* Welcome Screen */}
          {currentStep === 'welcome' && (
            <motion.div
              key="welcome"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="bg-white rounded-2xl shadow-lg p-12 max-w-4xl mx-auto">
                <div className="text-center mb-12">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6">
                    <Sparkles className="w-10 h-10 text-green-600" />
                  </div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-4">
                    Personalization Made Simple
                  </h2>
                  <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                    Follow 3 easy steps to understand your customers and recommend the perfect camping gear for each person.
                  </p>
                </div>

                {/* How It Works */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 border-2 border-purple-200">
                    <div className="flex items-center mb-4">
                      <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center mr-4">
                        <Database className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-bold text-gray-900">Step 1: Load Data</h3>
                    </div>
                    <p className="text-gray-700 mb-4 text-sm">
                      Choose which customer dataset to analyze - we have pre-loaded data ready to go.
                    </p>
                    <ul className="space-y-2 text-sm text-gray-600">
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-purple-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>5,000 customer profiles</span>
                      </li>
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-purple-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>57 camping products</span>
                      </li>
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-purple-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>Takes 2 seconds to load</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 border-2 border-green-200">
                    <div className="flex items-center mb-4">
                      <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center mr-4">
                        <Users className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-bold text-gray-900">Step 2: Discover Personas</h3>
                    </div>
                    <p className="text-gray-700 mb-4 text-sm">
                      Agent A analyzes your customer data and groups similar customers into 3 personas.
                    </p>
                    <ul className="space-y-2 text-sm text-gray-600">
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>🏕️ Beginners</span>
                      </li>
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>👨‍👩‍👧‍👦 Families</span>
                      </li>
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>⛰️ Experts</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 border-2 border-blue-200">
                    <div className="flex items-center mb-4">
                      <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center mr-4">
                        <Package className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-bold text-gray-900">Step 3: Get Recommendations</h3>
                    </div>
                    <p className="text-gray-700 mb-4 text-sm">
                      Agent B shows the perfect products for each persona, ranked by compatibility.
                    </p>
                    <ul className="space-y-2 text-sm text-gray-600">
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>Personalized for each type</span>
                      </li>
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>Ranked by probability</span>
                      </li>
                      <li className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span>Instant results</span>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Business Impact */}
                <div className="bg-gradient-to-r from-green-600 to-blue-600 rounded-xl p-8 text-white mb-8">
                  <h3 className="text-2xl font-bold mb-4 text-center">Expected Business Impact</h3>
                  <div className="grid grid-cols-3 gap-6 text-center">
                    <div>
                      <div className="text-4xl font-bold mb-2">228%</div>
                      <div className="text-green-100">Conversion Lift</div>
                    </div>
                    <div>
                      <div className="text-4xl font-bold mb-2">51%</div>
                      <div className="text-green-100">Higher Cart Value</div>
                    </div>
                    <div>
                      <div className="text-4xl font-bold mb-2">-60%</div>
                      <div className="text-green-100">Fewer Returns</div>
                    </div>
                  </div>
                </div>

                {/* Start Button */}
                <div className="text-center">
                  <button
                    onClick={() => setCurrentStep('data-loader')}
                    className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-green-600 to-green-700 text-white text-lg font-semibold rounded-xl hover:from-green-700 hover:to-green-800 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
                  >
                    <span>Let's Get Started</span>
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </button>
                  <p className="text-sm text-gray-500 mt-4">
                    This will take about 3 minutes
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Data Loader Screen */}
          {currentStep === 'data-loader' && (
            <motion.div
              key="data-loader"
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ duration: 0.3 }}
            >
              {/* Helper Card */}
              <div className="bg-purple-50 border-l-4 border-purple-600 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                  <Info className="w-5 h-5 text-purple-600 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold text-purple-900 mb-1">How to load data</h4>
                    <p className="text-sm text-purple-800">
                      Select a dataset from the list below and click <strong>"Load Dataset"</strong>. 
                      We recommend starting with <strong>"Academy Sports V1 (Original dataset)"</strong> which contains 5,000 customer profiles.
                    </p>
                  </div>
                </div>
              </div>

              {/* Data Loader Component */}
              <AcademyDataLoader />

              {/* Navigation */}
              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setCurrentStep('welcome')}
                  className="inline-flex items-center px-6 py-3 bg-white text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all duration-300 shadow border border-gray-300"
                >
                  <ChevronRight className="w-5 h-5 mr-2 rotate-180" />
                  <span>Back to Welcome</span>
                </button>

                <button
                  onClick={() => setCurrentStep('agent-a')}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-lg hover:from-green-700 hover:to-green-800 transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                  <span>Next: Discover Personas</span>
                  <ChevronRight className="w-5 h-5 ml-2" />
                </button>
              </div>
            </motion.div>
          )}

          {/* Agent A Screen */}
          {currentStep === 'agent-a' && (
            <motion.div
              key="agent-a"
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ duration: 0.3 }}
            >
              {/* Helper Card */}
              <div className="bg-blue-50 border-l-4 border-blue-600 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                  <Info className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold text-blue-900 mb-1">How to use Agent A</h4>
                    <p className="text-sm text-blue-800">
                      Click <strong>"Discover Personas"</strong> to analyze your customers. The system will group them into 3 types automatically. 
                      When done, you'll see charts showing who your customers are and how much they spend.
                    </p>
                  </div>
                </div>
              </div>

              {/* Agent A Component */}
              <AcademyAgentA />

              {/* Navigation */}
              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setCurrentStep('data-loader')}
                  className="inline-flex items-center px-6 py-3 bg-white text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all duration-300 shadow border border-gray-300"
                >
                  <ChevronRight className="w-5 h-5 mr-2 rotate-180" />
                  <span>Back to Data Loader</span>
                </button>

                <button
                  onClick={() => setCurrentStep('agent-b')}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                  <span>Next: Get Product Recommendations</span>
                  <ChevronRight className="w-5 h-5 ml-2" />
                </button>
              </div>
            </motion.div>
          )}

          {/* Agent B Screen */}
          {currentStep === 'agent-b' && (
            <motion.div
              key="agent-b"
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ duration: 0.3 }}
            >
              {/* Helper Card */}
              <div className="bg-green-50 border-l-4 border-green-600 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                  <Info className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold text-green-900 mb-1">How to use Agent B</h4>
                    <p className="text-sm text-green-800">
                      Select a <strong>Persona</strong> or <strong>Customer</strong>, optionally enter a search term (like "tent"), 
                      then click <strong>"Get Recommendations"</strong>. You'll see personalized product suggestions ranked by compatibility score.
                    </p>
                  </div>
                </div>
              </div>

              {/* Agent B Component */}
              <AcademyAgentB />

              {/* Back Button */}
              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setCurrentStep('agent-a')}
                  className="inline-flex items-center px-6 py-3 bg-white text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all duration-300 shadow border border-gray-300"
                >
                  <ChevronRight className="w-5 h-5 mr-2 rotate-180" />
                  <span>Back to Personas</span>
                </button>

                <button
                  onClick={() => setCurrentStep('welcome')}
                  className="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-all duration-300"
                >
                  Start Over
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

