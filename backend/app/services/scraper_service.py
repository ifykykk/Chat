import asyncio
import logging
from typing import List, Dict, Any
from app.services.enhanced_scraper import EnhancedMOSDACWebScraper, ScrapedContent
from app.core.config import settings

logger = logging.getLogger(__name__)

class ScraperService:
    """Service wrapper for the enhanced scraper"""
    
    def __init__(self):
        self.scraper = EnhancedMOSDACWebScraper(
            base_url=settings.MOSDAC_BASE_URL,
            output_dir=settings.DATA_DIR
        )
        logger.info("Scraper service initialized")
    
    async def run_full_scrape(self, max_pages: int = None, max_depth: int = None) -> List[ScrapedContent]:
        """Run full scraping process"""
        max_pages = max_pages or settings.MAX_SCRAPE_PAGES
        max_depth = max_depth or settings.MAX_SCRAPE_DEPTH
        
        logger.info(f"Starting scraping with max_pages={max_pages}, max_depth={max_depth}")
        
        try:
            scraped_data = await self.scraper.run_full_scrape(max_pages, max_depth)
            logger.info(f"Scraping completed: {len(scraped_data)} pages")
            return scraped_data
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
    
    async def scrape_single_url(self, url: str) -> ScrapedContent:
        """Scrape a single URL"""
        logger.info(f"Scraping single URL: {url}")
        
        try:
            import aiohttp
            async with aiohttp.ClientSession(**self.scraper.session_config) as session:
                content = await self.scraper.scrape_page_enhanced(session, url)
                return content
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            raise
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return {
            "scraped_urls": len(self.scraper.scraped_urls),
            "failed_urls": len(self.scraper.failed_urls),
            "cached_items": len(self.scraper.content_cache)
        }