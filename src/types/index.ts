export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  sources?: Source[];
  entities?: Entity[];
  confidence?: number;
}

export interface Source {
  url: string;
  title: string;
  content: string;
  relevance: number;
}

export interface Entity {
  text: string;
  label: string;
  confidence: number;
  start?: number;
  end?: number;
}

export interface QueryRequest {
  query: string;
  sessionId?: string;
  location?: GeoLocation;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  entities: Entity[];
  confidence: number;
  sessionId: string;
}

export interface GeoLocation {
  lat: number;
  lon: number;
  address?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface KnowledgeGraphNode {
  id: string;
  name: string;
  type: string;
  properties: Record<string, any>;
}

export interface KnowledgeGraphRelation {
  source: string;
  target: string;
  relation: string;
  confidence: number;
}