"""
Web MCP Tools
Provides HTTP requests, web scraping, and search capabilities
"""

import httpx
import json
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re
from bs4 import BeautifulSoup

from ..registry import MCPTool, ToolResult, ToolCategory


class HTTPRequestTool(MCPTool):
    """Tool for making HTTP requests"""
    
    def __init__(self, timeout: int = 30, max_redirects: int = 5):
        super().__init__(
            name="http_request",
            description="Make HTTP requests to web endpoints",
            category=ToolCategory.WEB
        )
        self.timeout = timeout
        self.max_redirects = max_redirects
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to make the request to"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method (GET, POST, PUT, DELETE, etc.)",
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers to include",
                    "default": {}
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters",
                    "default": {}
                },
                "data": {
                    "type": "object",
                    "description": "Request body data (for POST, PUT, etc.)",
                    "default": {}
                },
                "json": {
                    "type": "object",
                    "description": "JSON data to send in request body",
                    "default": {}
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Follow HTTP redirects",
                    "default": True
                }
            },
            "required": ["url"]
        }
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        url = params["url"]
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        query_params = params.get("params", {})
        data = params.get("data", {})
        json_data = params.get("json", {})
        follow_redirects = params.get("follow_redirects", True)
        
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ToolResult(
                    success=False,
                    error="Invalid URL format"
                )
            
            # Set default headers
            default_headers = {
                "User-Agent": "Agentic-Research-Copilot/1.0"
            }
            headers = {**default_headers, **headers}
            
            # Make request
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=follow_redirects,
                max_redirects=self.max_redirects
            ) as client:
                
                request_kwargs = {
                    "url": url,
                    "headers": headers,
                    "params": query_params
                }
                
                if json_data:
                    request_kwargs["json"] = json_data
                elif data:
                    request_kwargs["data"] = data
                
                response = await client.request(method, **request_kwargs)
            
            # Parse response
            content_type = response.headers.get("content-type", "").lower()
            
            # Try to parse JSON if content type suggests it
            response_data = None
            if "application/json" in content_type:
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
            else:
                response_data = response.text
            
            return ToolResult(
                success=True,
                data={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response_data,
                    "url": str(response.url),
                    "encoding": response.encoding
                },
                metadata={
                    "method": method,
                    "content_type": content_type,
                    "content_length": len(response.content),
                    "elapsed_time": response.elapsed.total_seconds()
                }
            )
            
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error=f"Request timeout after {self.timeout} seconds"
            )
        except httpx.RequestError as e:
            return ToolResult(
                success=False,
                error=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"HTTP request failed: {str(e)}"
            )


class WebScrapeTool(MCPTool):
    """Tool for web scraping and content extraction"""
    
    def __init__(self):
        super().__init__(
            name="web_scrape",
            description="Scrape and extract content from web pages",
            category=ToolCategory.WEB
        )
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the web page to scrape"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector to extract specific elements (optional)"
                },
                "extract_links": {
                    "type": "boolean",
                    "description": "Extract all links from the page",
                    "default": False
                },
                "extract_images": {
                    "type": "boolean",
                    "description": "Extract all images from the page",
                    "default": False
                },
                "clean_text": {
                    "type": "boolean",
                    "description": "Clean and normalize extracted text",
                    "default": True
                },
                "max_content_length": {
                    "type": "integer",
                    "description": "Maximum content length to return",
                    "default": 50000
                }
            },
            "required": ["url"]
        }
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        url = params["url"]
        selector = params.get("selector")
        extract_links = params.get("extract_links", False)
        extract_images = params.get("extract_images", False)
        clean_text = params.get("clean_text", True)
        max_content_length = params.get("max_content_length", 50000)
        
        try:
            # Fetch the web page
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Agentic-Research-Copilot/1.0"
                })
                response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ""
            
            # Extract main content
            content = ""
            if selector:
                # Use specific selector
                elements = soup.select(selector)
                content = "\n".join([elem.get_text() for elem in elements])
            else:
                # Extract main content areas
                main_selectors = [
                    'main', 'article', '.content', '#content', 
                    '.post', '.entry', 'body'
                ]
                
                for sel in main_selectors:
                    elements = soup.select(sel)
                    if elements:
                        content = elements[0].get_text()
                        break
                
                if not content:
                    content = soup.get_text()
            
            # Clean text if requested
            if clean_text:
                content = self._clean_text(content)
            
            # Truncate if too long
            if len(content) > max_content_length:
                content = content[:max_content_length] + "... [truncated]"
            
            result_data = {
                "title": title_text,
                "description": description,
                "content": content,
                "url": url,
                "content_length": len(content)
            }
            
            # Extract links if requested
            if extract_links:
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(url, href)
                    elif not href.startswith(('http://', 'https://')):
                        href = urljoin(url, href)
                    
                    links.append({
                        "url": href,
                        "text": link.get_text().strip(),
                        "title": link.get('title', '')
                    })
                
                result_data["links"] = links[:100]  # Limit to 100 links
            
            # Extract images if requested
            if extract_images:
                images = []
                for img in soup.find_all('img', src=True):
                    src = img['src']
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        src = urljoin(url, src)
                    elif not src.startswith(('http://', 'https://')):
                        src = urljoin(url, src)
                    
                    images.append({
                        "url": src,
                        "alt": img.get('alt', ''),
                        "title": img.get('title', '')
                    })
                
                result_data["images"] = images[:50]  # Limit to 50 images
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "page_size": len(response.text),
                    "scraped_at": datetime.now().isoformat()
                }
            )
            
        except httpx.HTTPStatusError as e:
            return ToolResult(
                success=False,
                error=f"HTTP error {e.response.status_code}: {e.response.reason_phrase}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Web scraping failed: {str(e)}"
            )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common unwanted patterns
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines
        text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces/tabs
        
        return text.strip()


class SearchTool(MCPTool):
    """Tool for web search (placeholder - would integrate with search APIs)"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="web_search",
            description="Search the web for information",
            category=ToolCategory.SEARCH
        )
        self.api_key = api_key
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 10
                },
                "language": {
                    "type": "string",
                    "description": "Language for search results",
                    "default": "en"
                },
                "safe_search": {
                    "type": "boolean",
                    "description": "Enable safe search filtering",
                    "default": True
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        query = params["query"]
        num_results = params.get("num_results", 10)
        language = params.get("language", "en")
        safe_search = params.get("safe_search", True)
        
        # This is a placeholder implementation
        # In a real implementation, you would integrate with:
        # - Google Custom Search API
        # - Bing Search API
        # - DuckDuckGo API
        # - SerpAPI
        # etc.
        
        try:
            # Placeholder search results
            results = [
                {
                    "title": f"Search result for: {query}",
                    "url": "https://example.com/search-result",
                    "snippet": f"This is a placeholder search result for the query '{query}'. In a real implementation, this would return actual search results from a search engine API.",
                    "source": "example.com"
                }
            ]
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "language": language
                },
                metadata={
                    "search_engine": "placeholder",
                    "safe_search": safe_search,
                    "searched_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )