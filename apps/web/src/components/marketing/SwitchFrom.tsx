import React from 'react';
import { cn } from '@/lib/utils';

interface SwitchFromProps {
  className?: string;
}

const SwitchFrom: React.FC<SwitchFromProps> = ({ className }) => {
  return (
    <section className={cn("py-16 bg-gradient-to-br from-blue-50 to-indigo-100", className)}>
      <div className="container mx-auto px-4">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">
            Switch From Traditional Job Hunting
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l-3 3m6 0l-3-3m-9 3h6m-6 0h6" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Traditional Way</h3>
                <p className="text-gray-600">Manual applications, tracking spreadsheets, endless follow-ups</p>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center text-sm text-gray-600">
                  <svg className="w-4 h-4 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 10.586l4.293-4.293a1 1 0 111.414 0l-5.293-5.293a1 1 0 01-1.414 0l-4 4a1 1 0 01-1.414 0l5.293-5.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Manual resume tailoring for each job
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <svg className="w-4 h-4 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M9 2a1 1 0 000-.2 2l10 12a1 1 0 00.2 2H9a1 1 0 00-.2-2zm0 18a1 1 0 102-.2 2v-2a1 1 0 00-2-2H4a1 1 0 00-2 2v2a1 1 0 002 2z" clipRule="evenodd" />
                  </svg>
                  Track applications manually
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <svg className="w-4 h-4 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000-16zM8.707-7.293a1 1 0 00-1.414-1.414l-6.364 6.364a1 1 0 001.414 1.414l6.364-6.364a1 1 0 00-1.414 0z" clipRule="evenodd" />
                  </svg>
                  Follow up with each company
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-2 relative overflow-hidden">
              <div className="absolute top-4 right-4">
                <span className="bg-green-100 text-green-800 text-xs font-semibold px-3 py-1 rounded-full">
                  Recommended
                </span>
              </div>
              
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7m0 13h-1m-1 0h-1m1 0v-4h-1v4m0-10h-1v4h1m0-10v4h1" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">JobHuntin AI</h3>
                <p className="text-gray-600">AI-powered platform with automated applications</p>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center text-sm text-green-600">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  One-click applications
                </div>
                <div className="flex items-center text-sm text-green-600">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 112.828 2.828a2 2 0 01-2.828 0l-2.829-2.828a2 2 0 112.828 2.828z" clipRule="evenodd" />
                  </svg>
                  AI resume optimization
                </div>
                <div className="flex items-center text-sm text-green-600">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v2a2 2 0 00-2 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2z" />
                  </svg>
                  Real-time tracking
                </div>
                <div className="flex items-center text-sm text-green-600">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M21 12a9 9 0 01-18 0 9 9 0 0118 0zm-9.5 0a1.5 1.5 0 113 0 1.5 1.5 0 013 0z" />
                    <path d="M9 9a1.5 1.5 0 113 0 1.5 1.5 0 013 0z" />
                  </svg>
                  Interview preparation
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7H8v2m0 0h5m-5 0H8m-9 0a3 3 0 00-3 3v14a3 3 0 003 3h14a3 3 0 003-3V8a3 3 0 00-3-3z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Results</h3>
                <p className="text-gray-600">Compare the outcomes</p>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center text-sm text-blue-600">
                  <svg className="w-4 h-4 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 7H8v2m0 0h5m-5 0H8m-9 0a3 3 0 00-3 3v14a3 3 0 003 3h14a3 3 0 003-3V8a3 3 0 00-3-3z" />
                  </svg>
                  85% higher response rate
                </div>
                <div className="flex items-center text-sm text-blue-600">
                  <svg className="w-4 h-4 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 19v-6H4v-6H9l-3 3m0 0l3-3m-3 3h12m-6 0h6m2 5H7a2 2 0 01-2 2v-6a2 2 0 012-2h9l-3-3z" />
                  </svg>
                  60% time saved
                </div>
                <div className="flex items-center text-sm text-blue-600">
                  <svg className="w-4 h-4 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  3x more interviews
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SwitchFrom;
