import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin, urlparse
import time
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict
import networkx as nx
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import hashlib
import asyncio
import aiohttp
import aiofiles

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class ScrapedContent:
    """Data class for scraped content"""
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]
    tables: List[Dict]
    entities: List[Dict]
    scraped_at: float
    content_hash: str

class EnhancedMOSDACWebScraper:
    """Enhanced web scraper with async support and better error handling"""
    
    def __init__(self, base_url="https://www.mosdac.gov.in", output_dir="./data"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.setup_directories()
        
        # Session configuration
        self.session_config = {
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'timeout': aiohttp.ClientTimeout(total=30),
            'connector': aiohttp.TCPConnector(limit=10, limit_per_host=5)
        }
        
        # Initialize components
        self.scraped_urls = set()
        self.failed_urls = set()
        self.content_cache = {}
        self.entity_extractor = EnhancedEntityExtractor()
        
        # Load existing data if available
        asyncio.create_task(self.load_existing_data())
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = ["raw", "processed", "pdfs", "metadata", "embeddings", "knowledge_graph"]
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
    
    async def load_existing_data(self):
        """Load existing scraped data to avoid reprocessing"""
        cache_file = self.output_dir / "metadata" / "content_cache.json"
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    self.content_cache = json.loads(content)
                logger.info(f"Loaded {len(self.content_cache)} cached items")
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")
    
    async def save_cache(self):
        """Save content cache"""
        cache_file = self.output_dir / "metadata" / "content_cache.json"
        try:
            async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self.content_cache, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Could not save cache: {e}")
    
    def is_valid_url(self, url: str) -> bool:
        """Enhanced URL validation"""
        try:
            parsed = urlparse(url)
            # Check if it's a valid MOSDAC or ISRO related URL
            valid_domains = ['mosdac.gov.in', 'isro.gov.in', 'nrsc.gov.in', 'sac.gov.in']
            domain_check = any(domain in parsed.netloc for domain in valid_domains)
            
            # Exclude certain file types and paths
            excluded_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
            excluded_paths = ['/download/', '/files/', '/media/']
            
            extension_check = not any(url.lower().endswith(ext) for ext in excluded_extensions)
            path_check = not any(path in url.lower() for path in excluded_paths)
            
            return domain_check and extension_check and path_check and len(url) < 500
        except Exception:
            return False
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def extract_enhanced_text_content(self, soup: BeautifulSoup) -> str:
        """Extract and clean text content with better structure preservation"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Extract text with some structure preservation
        text_parts = []
        
        # Extract title
        title = soup.find('title')
        if title:
            text_parts.append(f"Title: {title.get_text(strip=True)}")
        
        # Extract headings with hierarchy
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = heading.name[1]
            text_parts.append(f"{'#' * int(level)} {heading.get_text(strip=True)}")
        
        # Extract paragraphs
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Filter out short paragraphs
                text_parts.append(text)
        
        # Extract list items
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            if text and len(text) > 10:
                text_parts.append(f"• {text}")
        
        return '\n'.join(text_parts)
    
    def extract_enhanced_tables(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract tables with better structure and metadata"""
        tables = []
        
        for i, table in enumerate(soup.find_all('table')):
            # Extract table caption or nearby heading
            caption = ""
            if table.find('caption'):
                caption = table.find('caption').get_text(strip=True)
            else:
                # Look for heading before table
                prev_heading = table.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if prev_heading:
                    caption = prev_heading.get_text(strip=True)
            
            # Extract table data
            rows = []
            headers = []
            
            # Try to find header row
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Extract data rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if cells and any(cell.strip() for cell in cells):  # Skip empty rows
                    rows.append(cells)
            
            if rows:
                tables.append({
                    'id': f"table_{i}",
                    'caption': caption,
                    'headers': headers,
                    'data': rows,
                    'row_count': len(rows),
                    'column_count': len(headers) if headers else len(rows[0]) if rows else 0,
                    'raw_html': str(table)
                })
        
        return tables
    
    def extract_comprehensive_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract comprehensive metadata from HTML"""
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': [],
            'author': '',
            'date_published': '',
            'links': [],
            'images': [],
            'page_type': 'webpage',
            'language': 'en'
        }
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            
            if name in ['description', 'dc.description']:
                metadata['description'] = content
            elif name in ['keywords', 'dc.subject']:
                metadata['keywords'] = [kw.strip() for kw in content.split(',')]
            elif name in ['author', 'dc.creator']:
                metadata['author'] = content
            elif name in ['date', 'dc.date', 'publishdate']:
                metadata['date_published'] = content
            elif name == 'language':
                metadata['language'] = content
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for og in og_tags:
            property_name = og.get('property', '')
            content = og.get('content', '')
            
            if property_name == 'og:title':
                metadata['title'] = metadata['title'] or content
            elif property_name == 'og:description':
                metadata['description'] = metadata['description'] or content
            elif property_name == 'og:type':
                metadata['page_type'] = content
        
        # Extract links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            if self.is_valid_url(full_url):
                metadata['links'].append({
                    'url': full_url,
                    'text': link.get_text(strip=True)[:100],  # Limit text length
                    'title': link.get('title', ''),
                    'type': 'internal' if urlparse(full_url).netloc == urlparse(url).netloc else 'external'
                })
        
        # Extract images
        for img in soup.find_all('img', src=True):
            img_url = urljoin(url, img['src'])
            metadata['images'].append({
                'url': img_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
        
        return metadata
    
    async def scrape_page_enhanced(self, session: aiohttp.ClientSession, url: str) -> Optional[ScrapedContent]:
        """Enhanced page scraping with async support"""
        try:
            # Check if already scraped
            if url in self.scraped_urls:
                logger.debug(f"Already scraped: {url}")
                return None
            
            # Check cache
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if url_hash in self.content_cache:
                logger.debug(f"Using cached content for: {url}")
                cached_data = self.content_cache[url_hash]
                return ScrapedContent(**cached_data)
            
            logger.info(f"Scraping: {url}")
            
            # Make request with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        content = await response.text()
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"Retry {attempt + 1} for {url}: {e}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"Skipping non-HTML content: {url}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract content
            text_content = self.extract_enhanced_text_content(soup)
            
            # Skip if content is too short
            if len(text_content.strip()) < 100:
                logger.warning(f"Skipping page with minimal content: {url}")
                return None
            
            # Generate content hash for deduplication
            content_hash = self.generate_content_hash(text_content)
            
            # Check for duplicate content
            if content_hash in [item.get('content_hash') for item in self.content_cache.values()]:
                logger.debug(f"Skipping duplicate content: {url}")
                return None
            
            tables = self.extract_enhanced_tables(soup)
            metadata = self.extract_comprehensive_metadata(soup, url)
            entities = self.entity_extractor.extract_entities(text_content)
            
            # Create content object
            content_obj = ScrapedContent(
                url=url,
                title=metadata['title'],
                content=text_content,
                metadata=metadata,
                tables=tables,
                entities=entities,
                scraped_at=time.time(),
                content_hash=content_hash
            )
            
            # Cache the content
            self.content_cache[url_hash] = asdict(content_obj)
            self.scraped_urls.add(url)
            
            # Save progress periodically
            if len(self.scraped_urls) % 10 == 0:
                await self.save_cache()
            
            logger.info(f"Successfully scraped: {url} ({len(text_content)} chars, {len(entities)} entities)")
            return content_obj
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            self.failed_urls.add(url)
            return None
    
    async def crawl_website_enhanced(self, max_pages: int = 100, max_depth: int = 3) -> List[ScrapedContent]:
        """Enhanced crawling with async support and depth control"""
        urls_to_visit = [(self.base_url, 0)]  # (url, depth)
        visited_urls = set()
        all_content = []
        
        logger.info(f"Starting async crawl with max_pages={max_pages}, max_depth={max_depth}")
        
        async with aiohttp.ClientSession(**self.session_config) as session:
            while urls_to_visit and len(all_content) < max_pages:
                # Process URLs in batches for better performance
                batch_size = min(5, len(urls_to_visit))
                current_batch = urls_to_visit[:batch_size]
                urls_to_visit = urls_to_visit[batch_size:]
                
                # Create tasks for concurrent processing
                tasks = []
                for url, depth in current_batch:
                    if url not in visited_urls and depth <= max_depth:
                        visited_urls.add(url)
                        tasks.append(self.scrape_page_enhanced(session, url))
                
                # Execute tasks concurrently
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, ScrapedContent):
                            all_content.append(result)
                            
                            # Add new URLs to visit (only if within depth limit)
                            current_depth = next(depth for url, depth in current_batch if url == result.url)
                            if current_depth < max_depth:
                                new_urls = []
                                for link in result.metadata.get('links', []):
                                    link_url = link['url']
                                    if (link_url not in visited_urls and 
                                        link_url not in [u[0] for u in urls_to_visit] and
                                        link_url not in self.failed_urls):
                                        new_urls.append((link_url, current_depth + 1))
                                
                                # Add new URLs (limit to prevent explosion)
                                urls_to_visit.extend(new_urls[:10])  # Limit new URLs per page
                        elif isinstance(result, Exception):
                            logger.error(f"Task failed: {result}")
                
                # Be respectful - add delay between batches
                await asyncio.sleep(1)
                
                # Progress report
                if len(all_content) % 5 == 0:
                    logger.info(f"Scraped {len(all_content)} pages, {len(urls_to_visit)} URLs remaining")
        
        logger.info(f"Crawling completed: {len(all_content)} pages scraped, {len(self.failed_urls)} failed")
        return all_content
    
    async def save_scraped_data_enhanced(self, data: List[ScrapedContent]):
        """Enhanced data saving with multiple formats and better organization"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw data
        raw_file = self.output_dir / "raw" / f"scraped_data_{timestamp}.json"
        async with aiofiles.open(raw_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps([asdict(item) for item in data], indent=2, ensure_ascii=False))
        
        # Create structured datasets
        pages_data = []
        entities_data = []
        tables_data = []
        
        for item in data:
            # Page data
            pages_data.append({
                'url': item.url,
                'title': item.title,
                'content_length': len(item.content),
                'content_hash': item.content_hash,
                'scraped_at': item.scraped_at,
                'entity_count': len(item.entities),
                'table_count': len(item.tables),
                'link_count': len(item.metadata.get('links', [])),
                'image_count': len(item.metadata.get('images', []))
            })
            
            # Entity data
            for entity in item.entities:
                entities_data.append({
                    'source_url': item.url,
                    'source_title': item.title,
                    'text': entity['text'],
                    'type': entity['type'],
                    'confidence': entity.get('confidence', 0.0),
                    'start_pos': entity.get('start', 0),
                    'end_pos': entity.get('end', 0)
                })
            
            # Table data
            for table in item.tables:
                tables_data.append({
                    'source_url': item.url,
                    'source_title': item.title,
                    'table_id': table['id'],
                    'caption': table['caption'],
                    'row_count': table['row_count'],
                    'column_count': table['column_count'],
                    'headers': json.dumps(table['headers']),
                    'data': json.dumps(table['data'])
                })
        
        # Save structured data
        pd.DataFrame(pages_data).to_csv(
            self.output_dir / "processed" / f"pages_{timestamp}.csv", 
            index=False
        )
        
        if entities_data:
            pd.DataFrame(entities_data).to_csv(
                self.output_dir / "processed" / f"entities_{timestamp}.csv", 
                index=False
            )
        
        if tables_data:
            pd.DataFrame(tables_data).to_csv(
                self.output_dir / "processed" / f"tables_{timestamp}.csv", 
                index=False
            )
        
        # Save summary report
        summary = {
            'scraping_session': {
                'timestamp': timestamp,
                'total_pages': len(data),
                'total_entities': len(entities_data),
                'total_tables': len(tables_data),
                'failed_urls': len(self.failed_urls),
                'unique_content_hashes': len(set(item.content_hash for item in data))
            },
            'entity_distribution': self.get_entity_distribution(entities_data),
            'page_statistics': self.get_page_statistics(pages_data),
            'failed_urls': list(self.failed_urls)
        }
        
        async with aiofiles.open(self.output_dir / "metadata" / f"summary_{timestamp}.json", 'w') as f:
            await f.write(json.dumps(summary, indent=2, ensure_ascii=False))
        
        logger.info(f"Data saved with timestamp: {timestamp}")
        logger.info(f"Summary: {summary['scraping_session']}")
    
    def get_entity_distribution(self, entities_data: List[Dict]) -> Dict:
        """Get distribution of entity types"""
        distribution = defaultdict(int)
        for entity in entities_data:
            distribution[entity['type']] += 1
        return dict(distribution)
    
    def get_page_statistics(self, pages_data: List[Dict]) -> Dict:
        """Get page content statistics"""
        if not pages_data:
            return {}
        
        content_lengths = [page['content_length'] for page in pages_data]
        entity_counts = [page['entity_count'] for page in pages_data]
        
        return {
            'total_pages': len(pages_data),
            'avg_content_length': sum(content_lengths) / len(content_lengths),
            'avg_entity_count': sum(entity_counts) / len(entity_counts),
            'max_content_length': max(content_lengths),
            'min_content_length': min(content_lengths)
        }
    
    async def run_full_scrape(self, max_pages: int = 50, max_depth: int = 2):
        """Run complete enhanced scraping process"""
        logger.info("Starting enhanced MOSDAC web scraping...")
        
        try:
            # Crawl website
            scraped_data = await self.crawl_website_enhanced(max_pages, max_depth)
            
            if not scraped_data:
                logger.warning("No data was scraped!")
                return []
            
            # Save data
            await self.save_scraped_data_enhanced(scraped_data)
            
            # Final cache save
            await self.save_cache()
            
            logger.info("Enhanced scraping completed successfully!")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            # Save cache even if scraping fails
            await self.save_cache()
            raise


class EnhancedEntityExtractor:
    """Enhanced entity extraction with better patterns and confidence scoring"""
    
    def __init__(self):
        self.entity_patterns = {
            'SATELLITE': [
                r'INSAT-\d+[A-Z]?',
                r'SCATSAT-\d+',
                r'OCEANSAT-\d+',
                r'CARTOSAT-\d+',
                r'RISAT-\d+',
                r'RESOURCESAT-\d+',
                r'SARAL(?:\s+satellite)?',
                r'MEGHA-TROPIQUES',
                r'KALPANA-\d+',
                r'CHANDRAYAAN-\d+',
                r'MANGALYAAN',
                r'ASTROSAT',
                r'GSAT-\d+[A-Z]?',
                r'IRNSS-\d+[A-Z]?',
                r'NAVIC'
            ],
            'MISSION_TYPE': [
                r'weather\s+forecasting',
                r'oceanography',
                r'earth\s+observation',
                r'communication',
                r'meteorology',
                r'remote\s+sensing',
                r'climate\s+monitoring',
                r'disaster\s+management',
                r'navigation',
                r'broadcasting'
            ],
            'DATA_PRODUCT': [
                r'SST|Sea\s+Surface\s+Temperature',
                r'chlorophyll(?:\s+concentration)?',
                r'wind\s+speed',
                r'wave\s+height',
                r'cloud\s+motion\s+vector',
                r'precipitation',
                r'atmospheric\s+temperature',
                r'humidity\s+profile',
                r'outgoing\s+longwave\s+radiation',
                r'aerosol\s+optical\s+depth',
                r'vegetation\s+index',
                r'soil\s+moisture'
            ],
            'ORGANIZATION': [
                r'ISRO',
                r'MOSDAC',
                r'SAC',
                r'NRSC',
                r'DOS',
                r'IMD',
                r'INCOIS',
                r'ESSO',
                r'NASA',
                r'NOAA',
                r'ESA'
            ],
            'LOCATION': [
                r'Arabian\s+Sea',
                r'Bay\s+of\s+Bengal',
                r'Indian\s+Ocean',
                r'Ahmedabad',
                r'Bhubaneswar',
                r'Hyderabad',
                r'Mumbai',
                r'Chennai',
                r'Kolkata',
                r'Delhi',
                r'Bangalore',
                r'Thiruvananthapuram'
            ],
            'FREQUENCY_BAND': [
                r'L-band',
                r'S-band',
                r'C-band',
                r'X-band',
                r'Ku-band',
                r'Ka-band',
                r'VHF',
                r'UHF'
            ],
            'INSTRUMENT': [
                r'VHRR',
                r'CCD',
                r'LISS',
                r'WiFS',
                r'SCATTEROMETER',
                r'ALTIMETER',
                r'RADIOMETER',
                r'SPECTROMETER'
            ]
        }
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract entities with improved confidence scoring"""
        entities = []
        entity_id = 0
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Calculate confidence based on pattern complexity and context
                    confidence = self.calculate_confidence(match, pattern, text)
                    
                    entities.append({
                        'id': f"entity_{entity_id}",
                        'text': match.group(),
                        'type': entity_type,
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': confidence,
                        'pattern': pattern,
                        'context': self.get_context(text, match.start(), match.end())
                    })
                    entity_id += 1
        
        return self.deduplicate_entities(entities)
    
    def calculate_confidence(self, match, pattern: str, text: str) -> float:
        """Calculate confidence score for extracted entity"""
        base_confidence = 0.8
        
        # Adjust based on pattern specificity
        if r'\d+' in pattern:  # Patterns with numbers are more specific
            base_confidence += 0.1
        
        # Adjust based on context
        context = self.get_context(text, match.start(), match.end(), window=50)
        
        # Look for supporting context words
        supporting_words = {
            'SATELLITE': ['satellite', 'mission', 'orbit', 'launch'],
            'DATA_PRODUCT': ['data', 'product', 'parameter', 'measurement'],
            'ORGANIZATION': ['organization', 'agency', 'institute', 'center'],
            'LOCATION': ['region', 'area', 'coast', 'ocean'],
            'INSTRUMENT': ['instrument', 'sensor', 'detector', 'payload']
        }
        
        # Check if any supporting words are in context
        for word in supporting_words.get(self.get_entity_type(pattern), []):
            if word.lower() in context.lower():
                base_confidence += 0.05
        
        return min(0.99, base_confidence)
    
    def get_entity_type(self, pattern: str) -> str:
        """Get entity type from pattern"""
        for entity_type, patterns in self.entity_patterns.items():
            if pattern in patterns:
                return entity_type
        return 'UNKNOWN'
    
    def get_context(self, text: str, start: int, end: int, window: int = 30) -> str:
        """Get context around entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    def deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities"""
        seen_entities = set()
        unique_entities = []
        
        for entity in entities:
            # Create key for deduplication
            key = (entity['text'].lower(), entity['type'])
            if key not in seen_entities:
                seen_entities.add(key)
                unique_entities.append(entity)
        
        return unique_entities