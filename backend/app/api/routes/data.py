from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.services.enhanced_scraper import EnhancedMOSDACWebScraper
from app.services.vector_search import VectorSearchService
from app.services.knowledge_graph import KnowledgeGraphService
from app.main import get_vector_service, get_kg_service, get_scraper_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ScrapeRequest(BaseModel):
    max_pages: Optional[int] = 50
    max_depth: Optional[int] = 2
    base_url: Optional[str] = None

class ScrapeResponse(BaseModel):
    status: str
    message: str
    pages_scraped: int
    entities_extracted: int
    timestamp: str

class DataIngestionRequest(BaseModel):
    documents: List[Dict[str, Any]]
    build_kg: Optional[bool] = True
    update_vectors: Optional[bool] = True

@router.post("/data/scrape", response_model=ScrapeResponse)
async def start_scraping(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    scraper_service = Depends(get_scraper_service),
    vector_service: VectorSearchService = Depends(get_vector_service),
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Start web scraping process"""
    try:
        logger.info(f"Starting scraping with max_pages={request.max_pages}, max_depth={request.max_depth}")
        
        # Start scraping in background
        background_tasks.add_task(
            run_full_scraping_pipeline,
            scraper_service,
            vector_service,
            kg_service,
            request.max_pages,
            request.max_depth
        )
        
        return ScrapeResponse(
            status="started",
            message="Scraping process started in background",
            pages_scraped=0,
            entities_extracted=0,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error starting scraping: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting scraping: {str(e)}"
        )

@router.post("/data/ingest")
async def ingest_data(
    request: DataIngestionRequest,
    vector_service: VectorSearchService = Depends(get_vector_service),
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Ingest documents into vector store and knowledge graph"""
    try:
        results = {}
        
        # Add to vector store
        if request.update_vectors:
            vector_count = await vector_service.add_documents(request.documents)
            results['vectors_added'] = vector_count
        
        # Build knowledge graph
        if request.build_kg:
            # Extract entities and relationships from documents
            all_entities = []
            all_relationships = []
            
            for doc in request.documents:
                # This would use the entity extractor
                # For now, we'll use mock data
                entities = doc.get('entities', [])
                relationships = doc.get('relationships', [])
                
                all_entities.extend(entities)
                all_relationships.extend(relationships)
            
            kg_stats = await kg_service.build_graph_from_entities(all_entities, all_relationships)
            results['kg_stats'] = kg_stats
        
        return {
            "status": "success",
            "message": "Data ingestion completed",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error ingesting data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting data: {str(e)}"
        )

@router.get("/data/statistics")
async def get_data_statistics(
    vector_service: VectorSearchService = Depends(get_vector_service),
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Get data statistics"""
    try:
        vector_stats = await vector_service.get_statistics()
        kg_stats = await kg_service.get_graph_statistics()
        
        return {
            "vector_search": vector_stats,
            "knowledge_graph": kg_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting statistics: {str(e)}"
        )

@router.get("/data/search")
async def search_data(
    query: str,
    k: int = 5,
    search_type: str = "hybrid",
    vector_service: VectorSearchService = Depends(get_vector_service)
):
    """Search data using vector search"""
    try:
        if search_type == "semantic":
            results = await vector_service.search(query, k)
        elif search_type == "hybrid":
            results = await vector_service.hybrid_search(query, k)
        else:
            results = await vector_service.search(query, k)
        
        return {
            "query": query,
            "results": [
                {
                    "content": result.document.content[:200] + "...",
                    "metadata": result.document.metadata,
                    "score": result.score,
                    "rank": result.rank
                }
                for result in results
            ],
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching data: {str(e)}"
        )

@router.get("/data/entities")
async def search_entities(
    query: str,
    entity_type: Optional[str] = None,
    limit: int = 10,
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Search entities in knowledge graph"""
    try:
        if entity_type:
            results = await kg_service.find_entities_by_type(entity_type, limit)
        else:
            results = await kg_service.search_entities(query, limit)
        
        return {
            "query": query,
            "entity_type": entity_type,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching entities: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching entities: {str(e)}"
        )

async def run_full_scraping_pipeline(
    scraper_service,
    vector_service: VectorSearchService,
    kg_service: KnowledgeGraphService,
    max_pages: int,
    max_depth: int
):
    """Run complete scraping and data processing pipeline"""
    try:
        logger.info("Starting full scraping pipeline...")
        
        # Step 1: Scrape data
        scraped_data = await scraper_service.run_full_scrape(max_pages, max_depth)
        
        if not scraped_data:
            logger.warning("No data scraped")
            return
        
        # Step 2: Prepare documents for vector store
        documents = []
        all_entities = []
        
        for item in scraped_data:
            documents.append({
                'id': f"scraped_{item.url.replace('/', '_')}",
                'content': item.content,
                'metadata': {
                    'url': item.url,
                    'title': item.title,
                    'scraped_at': item.scraped_at,
                    'entity_count': len(item.entities),
                    'table_count': len(item.tables)
                }
            })
            
            # Collect entities for knowledge graph
            for entity in item.entities:
                all_entities.append({
                    'text': entity['text'],
                    'type': entity['type'],
                    'confidence': entity.get('confidence', 0.8),
                    'source_url': item.url,
                    'source_title': item.title
                })
        
        # Step 3: Add to vector store
        vector_count = await vector_service.add_documents(documents)
        logger.info(f"Added {vector_count} documents to vector store")
        
        # Step 4: Build knowledge graph
        # Generate simple relationships based on co-occurrence
        relationships = []
        for i, entity1 in enumerate(all_entities):
            for entity2 in all_entities[i+1:i+10]:  # Limit to avoid explosion
                if (entity1['source_url'] == entity2['source_url'] and 
                    entity1['type'] != entity2['type']):
                    relationships.append({
                        'source': entity1['text'],
                        'source_type': entity1['type'],
                        'target': entity2['text'],
                        'target_type': entity2['type'],
                        'relation': 'co_occurs_with',
                        'confidence': 0.6,
                        'source_url': entity1['source_url']
                    })
        
        kg_stats = await kg_service.build_graph_from_entities(all_entities, relationships)
        logger.info(f"Built knowledge graph: {kg_stats}")
        
        # Step 5: Save indexes
        await vector_service.save_index()
        
        logger.info("Full scraping pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Error in scraping pipeline: {e}")
        raise