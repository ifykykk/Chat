from neo4j import GraphDatabase
import json
import logging
from typing import Dict, List, Any, Optional
import asyncio
from dataclasses import dataclass
import networkx as nx
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeGraphNode:
    id: str
    name: str
    type: str
    properties: Dict[str, Any]

@dataclass
class KnowledgeGraphRelation:
    source: str
    target: str
    relation: str
    confidence: float
    properties: Dict[str, Any] = None

class KnowledgeGraphService:
    """Neo4j-based Knowledge Graph Service"""
    
    def __init__(self):
        self.driver = None
        self.graph = nx.DiGraph()  # NetworkX graph for local operations
        
    async def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    logger.info("Successfully connected to Neo4j")
                    await self.initialize_schema()
                else:
                    raise Exception("Neo4j connection test failed")
                    
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    async def initialize_schema(self):
        """Initialize Neo4j schema with constraints and indexes"""
        schema_queries = [
            # Create constraints
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT satellite_name IF NOT EXISTS FOR (s:Satellite) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT organization_name IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",
            "CREATE CONSTRAINT location_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
            
            # Create indexes
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX satellite_mission IF NOT EXISTS FOR (s:Satellite) ON (s.mission_type)",
            "CREATE INDEX data_product_type IF NOT EXISTS FOR (d:DataProduct) ON (d.product_type)",
        ]
        
        with self.driver.session() as session:
            for query in schema_queries:
                try:
                    session.run(query)
                    logger.debug(f"Executed schema query: {query}")
                except Exception as e:
                    logger.warning(f"Schema query failed (may already exist): {query} - {e}")
    
    async def create_entity_node(self, entity: KnowledgeGraphNode):
        """Create entity node in Neo4j"""
        query = """
        MERGE (e:Entity {id: $id})
        SET e.name = $name,
            e.type = $type,
            e.properties = $properties,
            e.created_at = datetime(),
            e.updated_at = datetime()
        """
        
        # Also create specific type label
        type_query = f"""
        MERGE (e:Entity {{id: $id}})
        SET e:{entity.type}
        """
        
        with self.driver.session() as session:
            session.run(query, 
                       id=entity.id, 
                       name=entity.name, 
                       type=entity.type, 
                       properties=json.dumps(entity.properties))
            
            # Add type-specific label
            session.run(type_query, id=entity.id)
            
        logger.debug(f"Created entity node: {entity.name} ({entity.type})")
    
    async def create_relationship(self, relation: KnowledgeGraphRelation):
        """Create relationship between entities"""
        query = """
        MATCH (a:Entity {id: $source})
        MATCH (b:Entity {id: $target})
        MERGE (a)-[r:RELATES {type: $relation_type}]->(b)
        SET r.confidence = $confidence,
            r.properties = $properties,
            r.created_at = datetime(),
            r.updated_at = datetime()
        """
        
        with self.driver.session() as session:
            session.run(query,
                       source=relation.source,
                       target=relation.target,
                       relation_type=relation.relation,
                       confidence=relation.confidence,
                       properties=json.dumps(relation.properties or {}))
        
        logger.debug(f"Created relationship: {relation.source} -{relation.relation}-> {relation.target}")
    
    async def query_graph(self, cypher_query: str, parameters: Dict = None) -> List[Dict]:
        """Execute Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Graph query failed: {e}")
            return []
    
    async def find_related_entities(self, entity_name: str, max_depth: int = 2) -> List[Dict]:
        """Find entities related to given entity"""
        query = """
        MATCH (start:Entity {name: $entity_name})
        MATCH path = (start)-[*1..$max_depth]-(related:Entity)
        RETURN DISTINCT related.name as name, 
               related.type as type, 
               related.properties as properties,
               length(path) as distance
        ORDER BY distance, related.name
        LIMIT 20
        """
        
        return await self.query_graph(query, {
            'entity_name': entity_name,
            'max_depth': max_depth
        })
    
    async def find_entities_by_type(self, entity_type: str, limit: int = 50) -> List[Dict]:
        """Find entities by type"""
        query = """
        MATCH (e:Entity {type: $entity_type})
        RETURN e.name as name, 
               e.type as type, 
               e.properties as properties
        ORDER BY e.name
        LIMIT $limit
        """
        
        return await self.query_graph(query, {
            'entity_type': entity_type,
            'limit': limit
        })
    
    async def get_entity_relationships(self, entity_name: str) -> List[Dict]:
        """Get all relationships for an entity"""
        query = """
        MATCH (e:Entity {name: $entity_name})-[r]-(related:Entity)
        RETURN type(r) as relationship_type,
               r.confidence as confidence,
               related.name as related_entity,
               related.type as related_type,
               startNode(r).name = $entity_name as is_outgoing
        ORDER BY r.confidence DESC
        """
        
        return await self.query_graph(query, {'entity_name': entity_name})
    
    async def search_entities(self, search_term: str, limit: int = 10) -> List[Dict]:
        """Search entities by name or properties"""
        query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($search_term)
           OR any(prop IN keys(e.properties) WHERE toLower(toString(e.properties[prop])) CONTAINS toLower($search_term))
        RETURN e.name as name,
               e.type as type,
               e.properties as properties
        ORDER BY 
            CASE WHEN toLower(e.name) = toLower($search_term) THEN 1
                 WHEN toLower(e.name) STARTS WITH toLower($search_term) THEN 2
                 ELSE 3 END,
            e.name
        LIMIT $limit
        """
        
        return await self.query_graph(query, {
            'search_term': search_term,
            'limit': limit
        })
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        queries = {
            'total_entities': "MATCH (e:Entity) RETURN count(e) as count",
            'total_relationships': "MATCH ()-[r]->() RETURN count(r) as count",
            'entity_types': """
                MATCH (e:Entity) 
                RETURN e.type as type, count(e) as count 
                ORDER BY count DESC
            """,
            'relationship_types': """
                MATCH ()-[r]->() 
                RETURN type(r) as type, count(r) as count 
                ORDER BY count DESC
            """
        }
        
        stats = {}
        for stat_name, query in queries.items():
            result = await self.query_graph(query)
            if stat_name in ['total_entities', 'total_relationships']:
                stats[stat_name] = result[0]['count'] if result else 0
            else:
                stats[stat_name] = result
        
        return stats
    
    async def build_graph_from_entities(self, entities_data: List[Dict], relationships_data: List[Dict]):
        """Build knowledge graph from extracted entities and relationships"""
        logger.info("Building knowledge graph from extracted data...")
        
        # Create entity nodes
        entity_count = 0
        for entity_data in entities_data:
            try:
                entity = KnowledgeGraphNode(
                    id=f"{entity_data['type']}_{entity_data['text'].replace(' ', '_')}",
                    name=entity_data['text'],
                    type=entity_data['type'],
                    properties={
                        'confidence': entity_data.get('confidence', 0.8),
                        'source_url': entity_data.get('source_url', ''),
                        'context': entity_data.get('context', ''),
                        'extraction_method': 'pattern_matching'
                    }
                )
                
                await self.create_entity_node(entity)
                entity_count += 1
                
            except Exception as e:
                logger.error(f"Failed to create entity {entity_data}: {e}")
        
        # Create relationships
        relationship_count = 0
        for rel_data in relationships_data:
            try:
                relation = KnowledgeGraphRelation(
                    source=f"{rel_data['source_type']}_{rel_data['source'].replace(' ', '_')}",
                    target=f"{rel_data['target_type']}_{rel_data['target'].replace(' ', '_')}",
                    relation=rel_data['relation'],
                    confidence=rel_data.get('confidence', 0.7),
                    properties={
                        'extraction_method': rel_data.get('method', 'co_occurrence'),
                        'source_url': rel_data.get('source_url', '')
                    }
                )
                
                await self.create_relationship(relation)
                relationship_count += 1
                
            except Exception as e:
                logger.error(f"Failed to create relationship {rel_data}: {e}")
        
        logger.info(f"Knowledge graph built: {entity_count} entities, {relationship_count} relationships")
        return {'entities': entity_count, 'relationships': relationship_count}
    
    async def export_graph_data(self, format: str = 'json') -> Dict[str, Any]:
        """Export knowledge graph data"""
        if format == 'json':
            # Export as JSON
            entities_query = """
            MATCH (e:Entity)
            RETURN e.id as id, e.name as name, e.type as type, e.properties as properties
            """
            
            relationships_query = """
            MATCH (a:Entity)-[r]->(b:Entity)
            RETURN a.id as source, b.id as target, type(r) as relation, 
                   r.confidence as confidence, r.properties as properties
            """
            
            entities = await self.query_graph(entities_query)
            relationships = await self.query_graph(relationships_query)
            
            return {
                'entities': entities,
                'relationships': relationships,
                'metadata': await self.get_graph_statistics()
            }
        
        elif format == 'networkx':
            # Export as NetworkX graph
            entities = await self.query_graph("MATCH (e:Entity) RETURN e")
            relationships = await self.query_graph("MATCH (a)-[r]->(b) RETURN a, r, b")
            
            # Build NetworkX graph
            G = nx.DiGraph()
            
            for entity in entities:
                G.add_node(entity['e']['id'], **entity['e'])
            
            for rel in relationships:
                G.add_edge(
                    rel['a']['id'], 
                    rel['b']['id'], 
                    relation=rel['r']['type'],
                    **rel['r']
                )
            
            return G
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def query_for_chatbot(self, entities: List[str], query_type: str = 'related') -> List[Dict]:
        """Query knowledge graph for chatbot responses"""
        if query_type == 'related':
            # Find entities related to query entities
            query = """
            MATCH (e:Entity)
            WHERE e.name IN $entities
            MATCH (e)-[r*1..2]-(related:Entity)
            RETURN DISTINCT related.name as entity,
                   related.type as type,
                   related.properties as properties,
                   collect(DISTINCT type(r)) as relationship_types
            ORDER BY related.name
            LIMIT 20
            """
            
        elif query_type == 'direct':
            # Get direct information about entities
            query = """
            MATCH (e:Entity)
            WHERE e.name IN $entities
            RETURN e.name as entity,
                   e.type as type,
                   e.properties as properties
            """
            
        elif query_type == 'path':
            # Find paths between entities
            if len(entities) >= 2:
                query = """
                MATCH (start:Entity {name: $start_entity})
                MATCH (end:Entity {name: $end_entity})
                MATCH path = shortestPath((start)-[*1..4]-(end))
                RETURN [node in nodes(path) | {name: node.name, type: node.type}] as path_nodes,
                       [rel in relationships(path) | type(rel)] as path_relations
                LIMIT 5
                """
                
                return await self.query_graph(query, {
                    'start_entity': entities[0],
                    'end_entity': entities[1]
                })
        
        return await self.query_graph(query, {'entities': entities})