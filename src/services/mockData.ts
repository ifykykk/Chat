import { Message, Source, Entity, ChatSession } from '../types';

// Mock data for demonstration
export const mockSources: Source[] = [
  {
    url: 'https://mosdac.gov.in/satellite-data',
    title: 'MOSDAC Satellite Data Archive',
    content: 'INSAT-3D provides meteorological and oceanographic data for weather forecasting and climate monitoring.',
    relevance: 0.95
  },
  {
    url: 'https://mosdac.gov.in/weather-services',
    title: 'Weather Services - MOSDAC',
    content: 'Real-time weather data and forecasts using satellite imagery and ground-based observations.',
    relevance: 0.87
  }
];

export const mockEntities: Entity[] = [
  {
    text: 'INSAT-3D',
    label: 'SATELLITE',
    confidence: 0.99
  },
  {
    text: 'weather forecasting',
    label: 'SERVICE',
    confidence: 0.85
  },
  {
    text: 'MOSDAC',
    label: 'ORGANIZATION',
    confidence: 0.95
  }
];

export const mockBotResponses = [
  {
    query: 'insat',
    response: `INSAT-3D is a geostationary meteorological satellite that provides:

• **Weather Monitoring**: Real-time atmospheric conditions, cloud imagery, and precipitation data
• **Disaster Management**: Early warning systems for cyclones, floods, and severe weather events  
• **Climate Research**: Long-term climate data for research and analysis
• **Ocean Monitoring**: Sea surface temperature and oceanographic parameters

The satellite operates from 82°E longitude and covers the entire Indian subcontinent and surrounding regions.`,
    sources: mockSources,
    entities: mockEntities,
    confidence: 0.92
  },
  {
    query: 'weather',
    response: `MOSDAC provides comprehensive weather services including:

• **Real-time Data**: Current weather conditions from satellite and ground observations
• **Forecasting**: Short-term (1-3 days) and medium-term (3-7 days) weather predictions
• **Severe Weather Alerts**: Warnings for cyclones, thunderstorms, and extreme weather
• **Climate Monitoring**: Long-term climate trends and seasonal patterns

Our data is used by meteorological departments, researchers, and disaster management agencies across India.`,
    sources: mockSources.slice(0, 1),
    entities: mockEntities.slice(1, 2),
    confidence: 0.88
  }
];

export const sampleSessions: ChatSession[] = [
  {
    id: '1',
    title: 'INSAT-3D Weather Data',
    messages: [],
    createdAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-01-15')
  },
  {
    id: '2',
    title: 'Oceanographic Data Query',
    messages: [],
    createdAt: new Date('2024-01-14'),
    updatedAt: new Date('2024-01-14')
  }
];

export function getMockResponse(query: string) {
  const lowerQuery = query.toLowerCase();
  
  for (const mock of mockBotResponses) {
    if (lowerQuery.includes(mock.query)) {
      return mock;
    }
  }
  
  // Default response
  return {
    response: `I understand you're asking about "${query}". Based on MOSDAC's data archive, I can help you with:

• **Satellite Data**: Information about INSAT, SCATSAT, and other satellite missions
• **Weather Services**: Current conditions, forecasts, and climate data
• **Ocean Data**: Sea surface temperature, wave height, and marine parameters
• **Research Tools**: Data access, APIs, and analysis capabilities

Could you please be more specific about what aspect you'd like to know more about?`,
    sources: mockSources,
    entities: [],
    confidence: 0.75
  };
}