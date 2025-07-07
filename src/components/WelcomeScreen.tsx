import React from 'react';
import { Satellite, Database, Bot, TrendingUp, Cloud, Waves } from 'lucide-react';

interface WelcomeScreenProps {
  onQuickStart: (query: string) => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onQuickStart }) => {
  const quickStartQueries = [
    {
      icon: Satellite,
      title: "Satellite Data",
      description: "Ask about INSAT, SCATSAT, and other satellite missions",
      query: "What are the capabilities of INSAT-3D satellite?"
    },
    {
      icon: Cloud,
      title: "Weather Information",
      description: "Get current weather data and forecasts",
      query: "Show me the latest weather forecast for Delhi"
    },
    {
      icon: Waves,
      title: "Ocean Data",
      description: "Access oceanographic and marine data",
      query: "What is the current sea surface temperature in the Arabian Sea?"
    },
    {
      icon: TrendingUp,
      title: "Climate Trends",
      description: "Analyze long-term climate patterns",
      query: "Show me monsoon rainfall trends over the past decade"
    }
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center max-w-2xl">
        {/* Header */}
        <div className="mb-8">
          <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
            <Bot size={36} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Welcome to MOSDAC AI Assistant
          </h1>
          <p className="text-lg text-gray-600">
            Your intelligent companion for meteorological and oceanographic data exploration
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {quickStartQueries.map((item, index) => (
            <div
              key={index}
              onClick={() => onQuickStart(item.query)}
              className="p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-200 hover:border-blue-300 group"
            >
              <div className="flex items-center mb-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3 group-hover:bg-blue-200 transition-colors">
                  <item.icon size={20} className="text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-800">{item.title}</h3>
              </div>
              <p className="text-gray-600 text-sm">{item.description}</p>
            </div>
          ))}
        </div>

        {/* Capabilities */}
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">What I can help you with:</h2>
          <div className="flex flex-wrap justify-center gap-3 mb-6">
            {[
              "Satellite data access", "Weather forecasting", "Ocean monitoring",
              "Climate analysis", "Data visualization", "Research assistance"
            ].map((capability, index) => (
              <span
                key={index}
                className="px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
              >
                {capability}
              </span>
            ))}
          </div>
          <p className="text-gray-600">
            Start by asking a question or selecting one of the quick start options above.
          </p>
        </div>
      </div>
    </div>
  );
};