import logging
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass
import json
import openai
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI
from langchain.schema import Document as LangChainDocument
from langchain.vectorstores.base import VectorStore
from langchain.embeddings import OpenAIEmbeddings

from app.services.knowledge_graph import KnowledgeGraphService
from app.services.vector_search import VectorSearchService, SearchResult
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class RAGResponse:
    answer: str
    sources: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    confidence: float
    reasoning: str
    query_type: str

class CustomVectorStore(VectorStore):
    """Custom VectorStore wrapper for our VectorSearchService"""
    
    def __init__(self, vector_service: VectorSearchService):
        self.vector_service = vector_service
    
    def similarity_search(self, query: str, k: int = 4, **kwargs) -> List[LangChainDocument]:
        """Synchronous similarity search for LangChain compatibility"""
        # Run async search in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(self.vector_service.search(query, k))
            
            documents = []
            for result in results:
                doc = LangChainDocument(
                    page_content=result.document.content,
                    metadata={
                        **result.document.metadata,
                        'score': result.score,
                        'rank': result.rank
                    }
                )
                documents.append(doc)
            
            return documents
        finally:
            loop.close()
    
    def add_texts(self, texts: List[str], metadatas: List[dict] = None, **kwargs) -> List[str]:
        """Add texts to vector store"""
        # This would be implemented for adding new documents
        pass
    
    @classmethod
    def from_texts(cls, texts: List[str], embedding, metadatas: List[dict] = None, **kwargs):
        """Create vector store from texts"""
        pass

class RAGService:
    """Retrieval-Augmented Generation service combining vector search and knowledge graph"""
    
    def __init__(self, kg_service: KnowledgeGraphService, vector_service: VectorSearchService):
        self.kg_service = kg_service
        self.vector_service = vector_service
        
        # Initialize OpenAI
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.llm = OpenAI(
                temperature=0.7,
                max_tokens=1000,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            logger.warning("OpenAI API key not provided, using mock responses")
            self.llm = None
        
        # Initialize memory for conversation
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Entity extraction patterns
        self.entity_patterns = {
            'SATELLITE': [
                r'INSAT-\d+[A-Z]?', r'SCATSAT-\d+', r'OCEANSAT-\d+', 
                r'CARTOSAT-\d+', r'RISAT-\d+', r'RESOURCESAT-\d+'
            ],
            'LOCATION': [
                r'Arabian\s+Sea', r'Bay\s+of\s+Bengal', r'Indian\s+Ocean',
                r'Mumbai', r'Chennai', r'Delhi', r'Kolkata'
            ],
            'DATA_PRODUCT': [
                r'SST|Sea\s+Surface\s+Temperature', r'chlorophyll',
                r'wind\s+speed', r'wave\s+height', r'precipitation'
            ]
        }
        
        logger.info("RAG Service initialized")
    
    async def process_query(self, query: str, session_id: str = "default", 
                          location: Dict[str, Any] = None) -> RAGResponse:
        """Process user query using RAG approach"""
        logger.info(f"Processing query: {query}")
        
        try:
            # Step 1: Extract entities from query
            query_entities = await self._extract_query_entities(query)
            
            # Step 2: Determine query type
            query_type = await self._classify_query(query, query_entities)
            
            # Step 3: Retrieve relevant information
            vector_results = await self._retrieve_vector_context(query, location)
            kg_context = await self._retrieve_kg_context(query_entities, query_type)
            
            # Step 4: Generate response
            response = await self._generate_response(
                query, vector_results, kg_context, query_entities, query_type
            )
            
            # Step 5: Calculate confidence
            confidence = await self._calculate_confidence(response, vector_results, kg_context)
            
            return RAGResponse(
                answer=response['answer'],
                sources=response['sources'],
                entities=query_entities,
                confidence=confidence,
                reasoning=response.get('reasoning', ''),
                query_type=query_type
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return RAGResponse(
                answer="I apologize, but I encountered an error processing your query. Please try again.",
                sources=[],
                entities=[],
                confidence=0.1,
                reasoning="Error in processing",
                query_type="error"
            )
    
    async def _extract_query_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract entities from user query"""
        import re
        
        entities = []
        entity_id = 0
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        'id': f"query_entity_{entity_id}",
                        'text': match.group(),
                        'type': entity_type,
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.9
                    })
                    entity_id += 1
        
        return entities
    
    async def _classify_query(self, query: str, entities: List[Dict]) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        # Weather-related queries
        weather_keywords = ['weather', 'temperature', 'rainfall', 'wind', 'humidity', 'forecast']
        if any(keyword in query_lower for keyword in weather_keywords):
            return 'weather'
        
        # Satellite-related queries
        satellite_keywords = ['satellite', 'insat', 'scatsat', 'oceansat', 'mission']
        if any(keyword in query_lower for keyword in satellite_keywords) or \
           any(entity['type'] == 'SATELLITE' for entity in entities):
            return 'satellite'
        
        # Ocean/marine queries
        ocean_keywords = ['ocean', 'sea', 'marine', 'sst', 'chlorophyll', 'wave']
        if any(keyword in query_lower for keyword in ocean_keywords):
            return 'ocean'
        
        # Data access queries
        data_keywords = ['data', 'download', 'access', 'api', 'format']
        if any(keyword in query_lower for keyword in data_keywords):
            return 'data_access'
        
        # General information
        return 'general'
    
    async def _retrieve_vector_context(self, query: str, location: Dict = None) -> List[SearchResult]:
        """Retrieve relevant context using vector search"""
        # Apply location filter if provided
        filter_metadata = {}
        if location:
            filter_metadata['location'] = location
        
        # Use hybrid search for better results
        results = await self.vector_service.hybrid_search(query, k=5)
        
        logger.debug(f"Retrieved {len(results)} vector search results")
        return results
    
    async def _retrieve_kg_context(self, entities: List[Dict], query_type: str) -> List[Dict]:
        """Retrieve context from knowledge graph"""
        if not entities:
            return []
        
        entity_names = [entity['text'] for entity in entities]
        
        # Query knowledge graph based on query type
        if query_type == 'satellite':
            kg_results = await self.kg_service.query_for_chatbot(entity_names, 'related')
        elif query_type in ['weather', 'ocean']:
            kg_results = await self.kg_service.query_for_chatbot(entity_names, 'direct')
        else:
            kg_results = await self.kg_service.query_for_chatbot(entity_names, 'related')
        
        logger.debug(f"Retrieved {len(kg_results)} knowledge graph results")
        return kg_results
    
    async def _generate_response(self, query: str, vector_results: List[SearchResult], 
                               kg_context: List[Dict], entities: List[Dict], 
                               query_type: str) -> Dict[str, Any]:
        """Generate response using LLM or rule-based approach"""
        
        # Prepare context
        context_parts = []
        sources = []
        
        # Add vector search context
        for result in vector_results:
            context_parts.append(f"Source: {result.document.metadata.get('title', 'Document')}")
            context_parts.append(f"Content: {result.document.content[:500]}...")
            context_parts.append("---")
            
            sources.append({
                'url': result.document.metadata.get('url', ''),
                'title': result.document.metadata.get('title', 'Document'),
                'content': result.document.content[:200] + "...",
                'relevance': result.score,
                'type': 'document'
            })
        
        # Add knowledge graph context
        for kg_item in kg_context:
            context_parts.append(f"Entity: {kg_item.get('entity', '')}")
            context_parts.append(f"Type: {kg_item.get('type', '')}")
            context_parts.append(f"Properties: {kg_item.get('properties', {})}")
            context_parts.append("---")
            
            sources.append({
                'entity': kg_item.get('entity', ''),
                'type': kg_item.get('type', ''),
                'properties': kg_item.get('properties', {}),
                'relevance': 0.8,
                'type': 'knowledge_graph'
            })
        
        context = "\n".join(context_parts)
        
        if self.llm and settings.OPENAI_API_KEY:
            # Use OpenAI for response generation
            prompt = self._create_prompt(query, context, query_type)
            
            try:
                response = await self._call_openai(prompt)
                answer = response.strip()
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}")
                answer = await self._generate_fallback_response(query, vector_results, kg_context, query_type)
        else:
            # Use rule-based response generation
            answer = await self._generate_fallback_response(query, vector_results, kg_context, query_type)
        
        return {
            'answer': answer,
            'sources': sources,
            'reasoning': f"Generated response based on {len(vector_results)} documents and {len(kg_context)} knowledge graph entities"
        }
    
    def _create_prompt(self, query: str, context: str, query_type: str) -> str:
        """Create prompt for LLM"""
        system_prompt = """You are an AI assistant specialized in MOSDAC (Meteorological & Oceanographic Satellite Data Archival Centre) data and services. 
        
Your role is to provide accurate, helpful information about:
- Indian meteorological and oceanographic satellites (INSAT, SCATSAT, OCEANSAT, etc.)
- Weather data and forecasting
- Ocean data and marine parameters
- Satellite data products and access methods
- ISRO missions and capabilities

Guidelines:
1. Be accurate and cite sources when possible
2. If you don't know something, say so clearly
3. Provide practical information about data access when relevant
4. Use technical terms appropriately but explain them when needed
5. Keep responses concise but comprehensive"""
        
        user_prompt = f"""
Context Information:
{context}

User Question: {query}

Query Type: {query_type}

Please provide a helpful and accurate response based on the context provided. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what information you can.
"""
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API asynchronously"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.7,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
            )
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_fallback_response(self, query: str, vector_results: List[SearchResult], 
                                        kg_context: List[Dict], query_type: str) -> str:
        """Generate fallback response using rule-based approach"""
        
        if query_type == 'satellite':
            return self._generate_satellite_response(query, vector_results, kg_context)
        elif query_type == 'weather':
            return self._generate_weather_response(query, vector_results, kg_context)
        elif query_type == 'ocean':
            return self._generate_ocean_response(query, vector_results, kg_context)
        elif query_type == 'data_access':
            return self._generate_data_access_response(query, vector_results, kg_context)
        else:
            return self._generate_general_response(query, vector_results, kg_context)
    
    def _generate_satellite_response(self, query: str, vector_results: List[SearchResult], 
                                   kg_context: List[Dict]) -> str:
        """Generate satellite-specific response"""
        if not vector_results and not kg_context:
            return "I don't have specific information about that satellite. MOSDAC operates several satellites including INSAT series for meteorology, SCATSAT for ocean wind monitoring, and OCEANSAT for oceanographic observations."
        
        response_parts = []
        
        # Extract satellite information from context
        satellites_mentioned = set()
        for result in vector_results:
            content = result.document.content.lower()
            if 'insat' in content:
                satellites_mentioned.add('INSAT series')
            if 'scatsat' in content:
                satellites_mentioned.add('SCATSAT')
            if 'oceansat' in content:
                satellites_mentioned.add('OCEANSAT')
        
        if satellites_mentioned:
            response_parts.append(f"Based on MOSDAC data, the following satellites are relevant: {', '.join(satellites_mentioned)}.")
        
        # Add specific information from vector results
        if vector_results:
            best_result = vector_results[0]
            response_parts.append(f"According to our records: {best_result.document.content[:300]}...")
        
        return " ".join(response_parts)
    
    def _generate_weather_response(self, query: str, vector_results: List[SearchResult], 
                                 kg_context: List[Dict]) -> str:
        """Generate weather-specific response"""
        response_parts = ["MOSDAC provides comprehensive weather data and forecasting services."]
        
        if vector_results:
            best_result = vector_results[0]
            response_parts.append(f"Current information: {best_result.document.content[:300]}...")
        
        response_parts.append("For real-time weather data, you can access MOSDAC's data portal or use their API services.")
        
        return " ".join(response_parts)
    
    def _generate_ocean_response(self, query: str, vector_results: List[SearchResult], 
                               kg_context: List[Dict]) -> str:
        """Generate ocean-specific response"""
        response_parts = ["MOSDAC provides oceanographic data including sea surface temperature, chlorophyll concentration, and wave parameters."]
        
        if vector_results:
            best_result = vector_results[0]
            response_parts.append(f"Available data: {best_result.document.content[:300]}...")
        
        return " ".join(response_parts)
    
    def _generate_data_access_response(self, query: str, vector_results: List[SearchResult], 
                                     kg_context: List[Dict]) -> str:
        """Generate data access response"""
        return "MOSDAC provides data access through their web portal, FTP services, and APIs. You can register for an account to download satellite data products. For bulk data access, API services are available with proper authentication."
    
    def _generate_general_response(self, query: str, vector_results: List[SearchResult], 
                                 kg_context: List[Dict]) -> str:
        """Generate general response"""
        if vector_results:
            best_result = vector_results[0]
            return f"Based on available information: {best_result.document.content[:400]}..."
        
        return "I can help you with information about MOSDAC satellites, weather data, oceanographic parameters, and data access methods. Could you please be more specific about what you'd like to know?"
    
    async def _calculate_confidence(self, response: Dict, vector_results: List[SearchResult], 
                                  kg_context: List[Dict]) -> float:
        """Calculate confidence score for the response"""
        base_confidence = 0.5
        
        # Boost confidence based on available context
        if vector_results:
            avg_vector_score = sum(r.score for r in vector_results) / len(vector_results)
            base_confidence += avg_vector_score * 0.3
        
        if kg_context:
            base_confidence += min(len(kg_context) * 0.1, 0.2)
        
        # Boost confidence if response contains specific information
        answer_length = len(response['answer'])
        if answer_length > 100:
            base_confidence += 0.1
        
        if len(response['sources']) > 0:
            base_confidence += 0.1
        
        return min(0.95, base_confidence)
    
    async def handle_geospatial_query(self, query: str, location: Dict[str, Any]) -> RAGResponse:
        """Handle location-aware queries"""
        # Add location context to query
        location_context = f"Location: {location.get('address', f'{location.get(\"lat\", \"\")}, {location.get(\"lon\", \"\")}')}. "
        enhanced_query = location_context + query
        
        return await self.process_query(enhanced_query, location=location)
    
    async def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        # This would typically be stored in a database
        # For now, return empty list
        return []
    
    async def clear_conversation_history(self, session_id: str):
        """Clear conversation history for a session"""
        self.memory.clear()
        logger.info(f"Cleared conversation history for session: {session_id}")