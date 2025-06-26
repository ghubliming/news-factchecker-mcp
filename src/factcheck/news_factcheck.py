#!/usr/bin/env python3
"""
News Fact-Checker MCP Server
============================

A Model Context Protocol (MCP) server that provides news fact-checking and trending topics functionality.

This server offers two main tools:
1. fact_check_headline - Verifies news headlines using web search and AI analysis
2. get_trending_topics - Retrieves current trending news topics by region

The server uses Google's Gemini 2.5 Flash for AI analysis and multiple search APIs for data gathering.

Author: AI Assistant
Version: 2.1.0
License: MIT
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import httpx
import google.generativeai as genai
from datetime import datetime
import os
from urllib.parse import quote_plus
import re
from dotenv import load_dotenv
import mcp
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
from mcp.server import NotificationOptions

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("news-factcheck-mcp")

# =============================================================================
# MAIN NEWS FACT-CHECKER CLASS
# =============================================================================

class NewsFactChecker:
    """
    Main class for news fact-checking and trending topics functionality.
    
    This class handles:
    - Web searches for news verification
    - AI-powered fact-checking analysis using Gemini
    - Trending topics retrieval from multiple sources
    - Professional formatting of results
    """
    
    def __init__(self, gemini_api_key: str, search_api_key: Optional[str] = None, news_api_key: Optional[str] = None):
        """
        Initialize the NewsFactChecker with required API keys.
        
        Args:
            gemini_api_key (str): Required Google Gemini API key for AI analysis
            search_api_key (Optional[str]): Optional NewsAPI key for enhanced search
            news_api_key (Optional[str]): Optional additional news API key
            
        Raises:
            Exception: If Gemini API key is invalid or service unavailable
        """
        self.gemini_api_key = gemini_api_key
        self.search_api_key = search_api_key
        self.news_api_key = news_api_key
        
        # Configure Google Gemini AI service
        try:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("✓ Gemini AI service initialized successfully")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Gemini AI: {e}")
            raise
        
        # Initialize HTTP client with reasonable timeout
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={'User-Agent': 'NewsFactChecker-MCP/2.1.0'}
        )
        logger.info("✓ HTTP client initialized")
    
    async def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web for information related to a news headline.
        
        This method uses multiple search strategies:
        1. DuckDuckGo Instant Answer API (primary, free)
        2. NewsAPI (fallback, requires API key)
        3. Direct web search (last resort)
        
        Args:
            query (str): Search query (usually the news headline)
            num_results (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results with title, snippet, URL, and source
        """
        logger.info(f"🔍 Searching web for: '{query}'")
        
        try:
            # PRIMARY: Use DuckDuckGo Instant Answer API (free and reliable)
            search_url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = await self.http_client.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Extract instant answer if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'Instant Answer'),
                    'snippet': data.get('Abstract'),
                    'url': data.get('AbstractURL', ''),
                    'source': data.get('AbstractSource', 'DuckDuckGo')
                })
                logger.info("✓ Found DuckDuckGo instant answer")
            
            # Extract related topics
            for topic in data.get('RelatedTopics', [])[:num_results-1]:
                if isinstance(topic, dict) and topic.get('Text'):
                    # Handle nested topics
                    if 'Topics' in topic:
                        for subtopic in topic['Topics'][:2]:  # Limit subtopics
                            if subtopic.get('Text'):
                                results.append({
                                    'title': self._extract_title_from_url(subtopic.get('FirstURL', '')),
                                    'snippet': subtopic.get('Text'),
                                    'url': subtopic.get('FirstURL', ''),
                                    'source': 'DuckDuckGo'
                                })
                    else:
                        results.append({
                            'title': self._extract_title_from_url(topic.get('FirstURL', '')),
                            'snippet': topic.get('Text'),
                            'url': topic.get('FirstURL', ''),
                            'source': 'DuckDuckGo'
                        })
            
            # FALLBACK: Try NewsAPI if we don't have enough results
            if len(results) < 2:
                logger.info("📰 Attempting NewsAPI fallback search")
                await self._search_news_api(query, results)
            
            # LAST RESORT: Try web search with simplified approach
            if not results:
                logger.info("🌐 Attempting direct web search fallback")
                await self._search_web_fallback(query, results)
            
            logger.info(f"✓ Found {len(results)} search results")
            return results[:num_results]
            
        except httpx.TimeoutException:
            logger.error("⏰ Search timeout - network too slow")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"🚫 HTTP error during search: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected search error: {e}")
            return []
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from a URL."""
        if not url:
            return 'Related Topic'
        
        # Extract the last part of the URL and clean it up
        title = url.split('/')[-1]
        title = title.replace('_', ' ').replace('-', ' ')
        title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        return title.title() if title else 'Related Topic'
    
    async def _search_news_api(self, query: str, results: List[Dict]) -> None:
        """
        Fallback search using NewsAPI service.
        
        Args:
            query (str): Search query
            results (List[Dict]): List to append results to (modified in place)
        """
        try:
            if not self.search_api_key:
                logger.info("ℹ️ NewsAPI key not available, skipping NewsAPI search")
                return
                
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'apiKey': self.search_api_key,
                'sortBy': 'relevancy',
                'pageSize': 5,
                'language': 'en',
                'from': (datetime.now().replace(day=1)).strftime('%Y-%m-%d')  # This month
            }
            
            response = await self.http_client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for article in data.get('articles', []):
                    if article.get('title') and article.get('description'):
                        results.append({
                            'title': article.get('title', ''),
                            'snippet': article.get('description', ''),
                            'url': article.get('url', ''),
                            'source': article.get('source', {}).get('name', 'NewsAPI')
                        })
                logger.info(f"✓ NewsAPI returned {len(data.get('articles', []))} articles")
            else:
                logger.warning(f"⚠️ NewsAPI returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ NewsAPI search error: {e}")

    async def _search_web_fallback(self, query: str, results: List[Dict]) -> None:
        """
        Last resort web search using multiple strategies.
        
        Args:
            query (str): Search query
            results (List[Dict]): List to append results to (modified in place)
        """
        try:
            # Try alternative search engines or APIs
            # This is a placeholder for additional search methods
            # You could add Bing API, Google Custom Search, etc.
            
            # For now, create a fallback response
            results.append({
                'title': f'Search Results for: {query}',
                'snippet': 'Unable to retrieve detailed search results. Manual verification recommended.',
                'url': f'https://duckduckgo.com/?q={quote_plus(query)}',
                'source': 'Fallback Search'
            })
            logger.info("⚠️ Using fallback search result")
            
        except Exception as e:
            logger.error(f"❌ Fallback search error: {e}")

    async def get_trending_topics(self, location: str = "international") -> List[Dict[str, Any]]:
        """
        Retrieve trending news topics based on location preference.
        
        This method tries multiple sources in order:
        1. NewsAPI for trending headlines
        2. RSS feeds from major news outlets
        3. Search-based trending topic discovery
        
        Args:
            location (str): Either "local"/"india" for Indian news or "international" for global news
            
        Returns:
            List[Dict[str, Any]]: List of trending topics with metadata
        """
        logger.info(f"📈 Fetching trending topics for: {location}")
        
        try:
            trending_topics = []
            
            # STRATEGY 1: Use NewsAPI for trending topics (most reliable)
            if self.news_api_key:
                logger.info("📊 Trying NewsAPI for trending topics")
                trending_topics = await self._get_newsapi_trending(location)
            
            # STRATEGY 2: Fallback to RSS feeds (free but less reliable)
            if not trending_topics:
                logger.info("📡 Trying RSS feeds for trending topics")
                trending_topics = await self._get_rss_trending(location)
            
            # STRATEGY 3: Search-based trending discovery (last resort)
            if not trending_topics:
                logger.info("🔍 Trying search-based trending discovery")
                trending_topics = await self._get_search_trending(location)
            
            logger.info(f"✓ Retrieved {len(trending_topics)} trending topics")
            return trending_topics[:10]  # Return top 10 trending topics
            
        except Exception as e:
            logger.error(f"❌ Error getting trending topics: {e}")
            return []
    
    async def _get_newsapi_trending(self, location: str) -> List[Dict[str, Any]]:
        """Get trending news from NewsAPI service."""
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': self.news_api_key,
                'pageSize': 10,
                'sortBy': 'popularity'
            }
            
            # Configure location-based parameters
            if location.lower() in ["local", "india"]:
                params['country'] = 'in'
                logger.info("🇮🇳 Fetching Indian trending topics")
            elif location.lower() == "international":
                params['country'] = 'us'  # Use US as proxy for international
                logger.info("🌍 Fetching international trending topics")
            else:
                params['q'] = f"{location} news"
                logger.info(f"🔍 Fetching trending topics for: {location}")
            
            response = await self.http_client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                topics = []
                for article in data.get('articles', []):
                    topics.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'published_at': article.get('publishedAt', ''),
                        'category': 'trending'
                    })
                return topics
            else:
                logger.warning(f"⚠️ NewsAPI returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ NewsAPI trending error: {e}")
        return []
    
    async def _get_rss_trending(self, location: str) -> List[Dict[str, Any]]:
        """Get trending topics from RSS feeds of major news outlets."""
        try:
            # Define RSS feeds based on location
            if location.lower() in ["local", "india"]:
                rss_feeds = [
                    "https://feeds.feedburner.com/ndtvnews-latest",
                    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                ]
                logger.info("📡 Using Indian RSS feeds")
            else:  # international
                rss_feeds = [
                    "https://rss.cnn.com/rss/edition.rss",
                    "https://feeds.bbci.co.uk/news/rss.xml",
                ]
                logger.info("📡 Using international RSS feeds")
            
            topics = []
            for feed_url in rss_feeds:
                try:
                    response = await self.http_client.get(feed_url)
                    if response.status_code == 200:
                        content = response.text
                        # Simple RSS parsing using regex
                        titles = re.findall(
                            r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', 
                            content, 
                            re.IGNORECASE
                        )
                        links = re.findall(r'<link>(.*?)</link>', content, re.IGNORECASE)
                        descriptions = re.findall(
                            r'<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>', 
                            content, 
                            re.IGNORECASE
                        )
                        
                        for i, title_match in enumerate(titles[:5]):
                            title = title_match[0] if title_match[0] else title_match[1]
                            if title and title.lower() not in ['rss', 'news', '']:
                                desc = ""
                                if i < len(descriptions):
                                    desc = descriptions[i][0] if descriptions[i][0] else descriptions[i][1]
                                
                                topics.append({
                                    'title': title.strip(),
                                    'description': desc[:200] + "..." if len(desc) > 200 else desc,
                                    'url': links[i] if i < len(links) else '',
                                    'source': feed_url.split('/')[2],
                                    'published_at': datetime.now().isoformat(),
                                    'category': 'trending'
                                })
                        logger.info(f"✓ Parsed {len(titles)} items from {feed_url}")
                except Exception as feed_error:
                    logger.error(f"❌ RSS feed error for {feed_url}: {feed_error}")
                    continue
            
            return topics
        except Exception as e:
            logger.error(f"❌ RSS trending error: {e}")
        return []
    
    async def _get_search_trending(self, location: str) -> List[Dict[str, Any]]:
        """Get trending topics using targeted search queries."""
        try:
            # Define search queries based on location
            if location.lower() in ["local", "india"]:
                search_queries = [
                    "India news today trending",
                    "Indian politics latest news",
                    "Bollywood news today"
                ]
                logger.info("🔍 Using Indian search queries")
            else:  # international
                search_queries = [
                    "world news today trending",
                    "international politics current",
                    "global economy news latest"
                ]
                logger.info("🔍 Using international search queries")
            
            topics = []
            for query in search_queries:
                search_results = await self.search_web(query, 2)
                for result in search_results:
                    if result.get('title') and result.get('snippet'):
                        topics.append({
                            'title': result['title'],
                            'description': result['snippet'][:200] + "..." if len(result['snippet']) > 200 else result['snippet'],
                            'url': result.get('url', ''),
                            'source': result.get('source', 'Search'),
                            'published_at': datetime.now().isoformat(),
                            'category': 'trending'
                        })
            
            return topics
        except Exception as e:
            logger.error(f"❌ Search trending error: {e}")
        return []
    
    async def analyze_with_gemini(self, headline: str, search_results: List[Dict]) -> Dict[str, Any]:
        """
        Use Google Gemini AI to analyze a headline against search results.
        
        This is the core fact-checking logic that:
        1. Prepares context from search results
        2. Sends structured prompt to Gemini
        3. Parses and validates the AI response
        4. Returns structured fact-check analysis
        
        Args:
            headline (str): The news headline to analyze
            search_results (List[Dict]): Supporting search results for context
            
        Returns:
            Dict[str, Any]: Structured fact-check analysis with verdict, confidence, etc.
        """
        logger.info(f"🤖 Starting Gemini AI analysis for headline: '{headline[:50]}...'")
        
        try:
            # Prepare search context for AI analysis
            context = "SEARCH RESULTS FOR VERIFICATION:\n"
            context += "=" * 50 + "\n"
            
            for i, result in enumerate(search_results, 1):
                context += f"\nRESULT {i}:\n"
                context += f"Title: {result.get('title', 'N/A')}\n"
                context += f"Source: {result.get('source', 'Unknown')}\n"
                context += f"Content: {result.get('snippet', 'N/A')}\n"
                context += f"URL: {result.get('url', 'N/A')}\n"
                context += "-" * 30 + "\n"
            
            # Structured prompt for consistent AI analysis
            prompt = f"""You are a professional fact-checking expert. Analyze this news headline against the provided search results.

HEADLINE TO FACT-CHECK: "{headline}"

{context}

Provide a comprehensive fact-check analysis in valid JSON format:

{{
    "verdict": "TRUE|FALSE|PARTIALLY_TRUE|UNVERIFIED|MISLEADING",
    "confidence": 0.85,
    "truthfulness_percentage": 75,
    "explanation": "Clear, detailed explanation of your analysis in 2-3 sentences",
    "evidence": [
        {{
            "source": "source name",
            "supports": true,
            "relevance": "high",
            "summary": "brief summary of what this source says"
        }}
    ],
    "concerns": ["specific concerns about the headline"],
    "recommendations": "What readers should know or do"
}}

VERDICT GUIDELINES:
- TRUE (85-100%): Factually accurate and well-supported
- FALSE (0-15%): Contains significant factual errors
- PARTIALLY_TRUE (40-75%): Mixed accuracy with some false elements
- UNVERIFIED (30-60%): Cannot be confirmed with available evidence
- MISLEADING (20-50%): Technically true but presented deceptively

Focus on factual accuracy, not opinions. Be thorough but concise."""
            
            # Call Gemini AI with error handling
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            response_text = response.text.strip()
            logger.info(f"✓ Received Gemini response ({len(response_text)} characters)")
            
            # Extract and parse JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    analysis = json.loads(json_match.group())
                    
                    # Validate required fields
                    required_fields = ['verdict', 'confidence', 'truthfulness_percentage', 'explanation']
                    if all(field in analysis for field in required_fields):
                        logger.info(f"✓ AI analysis complete - Verdict: {analysis.get('verdict')}")
                        return analysis
                    else:
                        logger.warning("⚠️ AI response missing required fields")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON parsing error: {e}")
            
            # Fallback: Create structured response from raw text
            logger.info("⚠️ Using fallback analysis parsing")
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.5,
                "truthfulness_percentage": 50,
                "explanation": f"AI analysis completed but response format was non-standard: {response_text[:200]}...",
                "evidence": [],
                "concerns": ["Could not parse structured AI analysis"],
                "recommendations": "Manual verification recommended due to parsing issues"
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini analysis error: {e}")
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "truthfulness_percentage": 0,
                "explanation": f"AI analysis service temporarily unavailable: {str(e)}",
                "evidence": [],
                "concerns": ["Analysis service error"],
                "recommendations": "Please try again later or verify manually"
            }
    
    async def fact_check_headline(self, headline: str) -> Dict[str, Any]:
        """
        Main fact-checking function that orchestrates the entire verification process.
        
        This function:
        1. Searches the web for relevant information
        2. Analyzes findings with AI
        3. Structures and returns comprehensive results
        
        Args:
            headline (str): The news headline to fact-check
            
        Returns:
            Dict[str, Any]: Complete fact-check analysis with verdict and evidence
        """
        logger.info(f"🎯 Starting fact-check process for: '{headline}'")
        
        # Input validation
        if not headline or not headline.strip():
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "truthfulness_percentage": 0,
                "explanation": "No headline provided for fact-checking",
                "evidence": [],
                "concerns": ["Empty or invalid headline"],
                "recommendations": "Please provide a valid news headline"
            }
        
        headline = headline.strip()
        
        # Step 1: Search for supporting/contradicting information
        logger.info("📊 Step 1: Searching for verification sources")
        search_results = await self.search_web(headline)
        
        if not search_results:
            logger.warning("⚠️ No search results found - returning unverified")
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "truthfulness_percentage": 0,
                "explanation": "Unable to find any search results to verify this headline. This could indicate a very recent story, incorrect information, or search service issues.",
                "evidence": [],
                "concerns": ["No verifiable sources found", "Possible misinformation"],
                "recommendations": "Seek additional sources and wait for more reporting before sharing"
            }
        
        # Step 2: AI-powered analysis
        logger.info("🤖 Step 2: Performing AI analysis")
        analysis = await self.analyze_with_gemini(headline, search_results)
        
        # Step 3: Add metadata and finalize
        analysis.update({
            "headline": headline,
            "search_results_count": len(search_results),
            "timestamp": datetime.now().isoformat(),
            "sources_analyzed": [result.get('source', 'Unknown') for result in search_results]
        })
        
        logger.info(f"✅ Fact-check completed - Final verdict: {analysis.get('verdict')}")
        return analysis
    
    async def close(self):
        """Clean up resources and close connections."""
        logger.info("🔄 Cleaning up NewsFactChecker resources")
        try:
            await self.http_client.aclose()
            logger.info("✓ HTTP client closed successfully")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

# =============================================================================
# MCP SERVER SETUP AND GLOBAL VARIABLES
# =============================================================================

# Global fact checker instance - initialized in main()
fact_checker: Optional[NewsFactChecker] = None

# Create MCP server application
app = mcp.server.Server("news-factcheck")

# =============================================================================
# MCP TOOL DEFINITIONS
# =============================================================================

@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    Define available MCP tools for the fact-checking server.
    
    Returns:
        list[Tool]: List of available tools with detailed schemas
    """
    return [
        Tool(
            name="fact_check_headline",
            description="""
            🔍 FACT-CHECK NEWS HEADLINE
            
            Comprehensive news headline verification using AI analysis and web search.
            
            This tool:
            • Searches multiple sources for verification data
            • Uses Google Gemini AI for professional fact-checking analysis  
            • Provides verdict (TRUE/FALSE/PARTIALLY_TRUE/UNVERIFIED/MISLEADING)
            • Gives confidence scores and truthfulness percentages
            • Lists supporting/contradicting evidence with sources
            • Offers recommendations for readers
            
            Perfect for: Verifying news claims, checking viral stories, academic research
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "headline": {
                        "type": "string",
                        "description": "The news headline or claim to fact-check (e.g., 'Scientists discover cure for cancer')",
                        "minLength": 5,
                        "maxLength": 500
                    }
                },
                "required": ["headline"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_trending_topics",
            description="""
            📈 GET TRENDING NEWS TOPICS
            
            Retrieve current trending news topics from multiple authoritative sources.
            
            This tool:
            • Aggregates trending topics from NewsAPI, RSS feeds, and search engines
            • Supports both local (India/Mumbai) and international news coverage
            • Provides topic titles, descriptions, sources, and publication dates
            • Returns up to 10 most relevant trending topics
            • Includes source credibility information
            
            Perfect for: Content creators, journalists, staying informed, market research
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "enum": ["local", "international", "india"],
                        "description": "News coverage area: 'local' or 'india' for Indian/Mumbai regional news, 'international' for global news",
                        "default": "local"
                    }
                },
                "required": [],
                "additionalProperties": False
            }
        )
    ]

# =============================================================================
# MCP TOOL HANDLERS
# =============================================================================

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle MCP tool calls with comprehensive error handling and logging.
    
    Args:
        name (str): Name of the tool being called
        arguments (dict): Tool arguments provided by the client
        
    Returns:
        list[TextContent]: Formatted response content
    """
    global fact_checker
    
    logger.info(f"🛠️ Tool called: {name} with arguments: {arguments}")
    
    # Verify service initialization
    if not fact_checker:
        error_msg = """
❌ FACT-CHECKING SERVICE UNAVAILABLE

The news fact-checking service is not properly initialized. This usually means:
• GEMINI_API_KEY environment variable is missing or invalid
• Network connectivity issues
• Service startup failed

Please check your API key configuration and try again.
        """.strip()
        logger.error("Service not initialized when tool called")
        return [TextContent(type="text", text=error_msg)]
    
    # Handle fact-checking tool
    if name == "fact_check_headline":
        headline = arguments.get("headline", "").strip()
        
        # Input validation
        if not headline:
            error_msg = """
❌ INVALID INPUT

No headline provided for fact-checking. Please provide a news headline or claim to analyze.

Example: "Scientists discover cure for cancer in breakthrough study"
            """.strip()
            return [TextContent(type="text", text=error_msg)]
            
        if len(headline) < 5:
            return [TextContent(type="text", text="❌ ERROR: Headline too short. Please provide a meaningful news headline (at least 5 characters).")]
            
        if len(headline) > 500:
            return [TextContent(type="text", text="❌ ERROR: Headline too long. Please limit to 500 characters or less.")]
        
        try:
            logger.info(f"🎯 Processing fact-check request for: '{headline[:50]}...'")
            result = await fact_checker.fact_check_headline(headline)
            formatted_result = format_fact_check_result(result)
            logger.info("✅ Fact-check completed successfully")
            return [TextContent(type="text", text=formatted_result)]
            
        except Exception as e:
            error_msg = f"""
❌ FACT-CHECK PROCESS FAILED

An error occurred during the fact-checking process:
{str(e)}

This could be due to:
• Temporary API service issues
• Network connectivity problems  
• Rate limiting from search services

Please try again in a few moments.
            """.strip()
            logger.error(f"Fact-check error: {e}")
            return [TextContent(type="text", text=error_msg)]
    
    # Handle trending topics tool
    elif name == "get_trending_topics":
        location = arguments.get("location", "local")
        
        # Validate location parameter
        valid_locations = ["local", "international", "india"]
        if location not in valid_locations:
            return [TextContent(type="text", text=f"❌ ERROR: Invalid location '{location}'. Must be one of: {', '.join(valid_locations)}")]
        
        try:
            logger.info(f"📈 Processing trending topics request for: {location}")
            topics = await fact_checker.get_trending_topics(location)
            formatted_topics = format_trending_topics(topics, location)
            logger.info(f"✅ Retrieved {len(topics)} trending topics")
            return [TextContent(type="text", text=formatted_topics)]
            
        except Exception as e:
            error_msg = f"""
❌ TRENDING TOPICS RETRIEVAL FAILED

An error occurred while fetching trending topics:
{str(e)}

This could be due to:
• Temporary news API service issues
• Network connectivity problems
• RSS feed parsing errors

Please try again in a few moments.
            """.strip()
            logger.error(f"Trending topics error: {e}")
            return [TextContent(type="text", text=error_msg)]
    
    # Handle unknown tool requests
    else:
        error_msg = f"""
❌ UNKNOWN TOOL REQUEST

Tool '{name}' is not recognized. Available tools:
• fact_check_headline - Verify news headlines using AI analysis
• get_trending_topics - Get current trending news by region

Please check the tool name and try again.
        """.strip()
        logger.warning(f"Unknown tool requested: {name}")
        return [TextContent(type="text", text=error_msg)]

# =============================================================================
# MCP RESOURCE DEFINITIONS
# =============================================================================

@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    """
    Define available MCP resources for status checking and quick access.
    
    Resources provide read-only access to service status and cached data.
    
    Returns:
        list[Resource]: List of available resources
    """
    return [
        Resource(
            uri="factcheck://status",
            name="🟢 Fact Checker Service Status",
            description="Current operational status of the news fact-checking service including API connectivity and system health",
            mimeType="text/plain"
        ),
        Resource(
            uri="trending://local",
            name="📈 Indian/Mumbai Trending Topics",
            description="Current trending news topics in India and Mumbai region from multiple authoritative sources",
            mimeType="text/plain"
        ),
        Resource(
            uri="trending://international",
            name="🌍 International Trending Topics", 
            description="Current trending international news topics from global news sources and agencies",
            mimeType="text/plain"
        ),
        Resource(
            uri="factcheck://help",
            name="❓ Usage Guide and Examples",
            description="Comprehensive guide on how to use the fact-checking tools effectively with examples",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """
    Handle MCP resource read requests with detailed status and information.
    
    Args:
        uri (str): Resource URI to read
        
    Returns:
        str: Resource content
    """
    global fact_checker
    
    logger.info(f"📖 Resource requested: {uri}")
    
    if uri == "factcheck://status":
        if fact_checker:
            try:
                # Test service connectivity
                test_result = await fact_checker.search_web("test connectivity", 1)
                status = "🟢 OPERATIONAL" if test_result else "🟡 LIMITED"
                
                return f"""
================================================================================
                    NEWS FACT-CHECKER SERVICE STATUS
================================================================================

SERVICE STATUS: {status}
TIMESTAMP: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}

✅ CORE SERVICES:
• Gemini AI Analysis: ACTIVE
• Web Search Engine: ACTIVE  
• HTTP Client: ACTIVE
• MCP Server: ACTIVE

🔧 CONFIGURED APIS:
• Google Gemini: ✅ Configured
• NewsAPI: {'✅ Configured' if fact_checker.news_api_key else '⚠️ Not configured (optional)'}
• Search API: {'✅ Configured' if fact_checker.search_api_key else '⚠️ Not configured (optional)'}

📊 CAPABILITIES:
• Fact-check news headlines: AVAILABLE
• Trending topics (local): AVAILABLE
• Trending topics (international): AVAILABLE
• Multi-source verification: AVAILABLE
• Professional reporting: AVAILABLE

🌐 SEARCH METHODS:
• DuckDuckGo API: Primary method
• NewsAPI: Fallback method
• RSS Feeds: Backup method
• Direct Search: Last resort

The service is ready to fact-check news headlines and retrieve trending topics.
For help, access the factcheck://help resource.

================================================================================
                """.strip()
            except Exception as e:
                return f"""
🔴 SERVICE STATUS: DEGRADED

Error during status check: {str(e)}

The fact-checking service may be experiencing issues. Please try again later.
                """.strip()
        else:
            return """
🔴 SERVICE STATUS: UNAVAILABLE

The news fact-checking service is not initialized. 

COMMON CAUSES:
• Missing GEMINI_API_KEY environment variable
• Invalid API key configuration
• Service startup failure

RESOLUTION:
1. Ensure GEMINI_API_KEY is set in your environment
2. Verify API key is valid and has proper permissions
3. Restart the MCP server

For technical support, check the server logs for detailed error information.
            """.strip()
    
    elif uri == "trending://local":
        if fact_checker:
            try:
                topics = await fact_checker.get_trending_topics("local")
                return format_trending_topics(topics, "local")
            except Exception as e:
                return f"❌ ERROR: Unable to retrieve local trending topics - {str(e)}"
        else:
            return "❌ ERROR: Fact-checking service unavailable"
    
    elif uri == "trending://international":
        if fact_checker:
            try:
                topics = await fact_checker.get_trending_topics("international")
                return format_trending_topics(topics, "international")
            except Exception as e:
                return f"❌ ERROR: Unable to retrieve international trending topics - {str(e)}"
        else:
            return "❌ ERROR: Fact-checking service unavailable"
    
    elif uri == "factcheck://help":
        return """
================================================================================
                    NEWS FACT-CHECKER USAGE GUIDE
================================================================================

🎯 FACT-CHECKING TOOL
Tool Name: fact_check_headline

PURPOSE: Verify the accuracy of news headlines using AI analysis and web search

USAGE:
{
    "tool": "fact_check_headline",
    "arguments": {
        "headline": "Your news headline here"
    }
}

EXAMPLES:
✅ Good: "NASA announces discovery of water on Mars"
✅ Good: "Stock market drops 5% amid inflation concerns"
✅ Good: "New COVID variant detected in 12 countries"

❌ Avoid: "This is amazing!" (too vague)
❌ Avoid: "" (empty headline)
❌ Avoid: Single words or very short phrases

RESPONSE FORMAT:
• Verdict: TRUE/FALSE/PARTIALLY_TRUE/UNVERIFIED/MISLEADING
• Confidence: 0.0-1.0 (how sure the AI is)
• Truthfulness: 0-100% (percentage of accuracy)
• Explanation: Detailed analysis
• Evidence: Supporting sources
• Concerns: Potential issues
• Recommendations: What to do next

================================================================================

📈 TRENDING TOPICS TOOL
Tool Name: get_trending_topics

PURPOSE: Get current trending news topics by region

USAGE:
{
    "tool": "get_trending_topics", 
    "arguments": {
        "location": "local|international|india"
    }
}

LOCATION OPTIONS:
• "local" or "india": Indian and Mumbai regional news
• "international": Global news from major outlets

RESPONSE INCLUDES:
• Topic headlines and descriptions
• Source information and credibility
• Publication dates
• Reference URLs
• Category classification

================================================================================

💡 BEST PRACTICES:

1. FACT-CHECKING:
   • Use complete, specific headlines
   • Check recent and controversial claims
   • Review all evidence sources provided
   • Consider the confidence score in your decisions

2. TRENDING TOPICS:
   • Refresh regularly for latest trends
   • Cross-reference with fact-checking tool
   • Consider source reliability
   • Use for content planning and awareness

3. INTERPRETATION:
   • TRUE (85-100%): Highly reliable, safe to share
   • PARTIALLY_TRUE (40-84%): Verify specific claims
   • UNVERIFIED (30-60%): Wait for more sources
   • FALSE (0-29%): Likely misinformation, don't share

================================================================================

🔧 TROUBLESHOOTING:

Common Issues:
• "Service unavailable": Check API key configuration
• "No results found": Try rephrasing the headline
• "Analysis failed": Network/API temporary issues

Support:
• Check factcheck://status for service health
• Review server logs for detailed errors
• Ensure stable internet connection

================================================================================
        """.strip()
    
    else:
        return f"❌ ERROR: Resource not found - {uri}"

# =============================================================================
# RESPONSE FORMATTING FUNCTIONS
# =============================================================================

def format_fact_check_result(result: Dict[str, Any]) -> str:
    """
    Format fact-check results into a professional, easy-to-read report.
    
    Args:
        result (Dict[str, Any]): Raw fact-check analysis from AI
        
    Returns:
        str: Professionally formatted fact-check report
    """
    # Extract key information with defaults
    verdict = result.get("verdict", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    truthfulness_pct = result.get("truthfulness_percentage", 0)
    explanation = result.get("explanation", "No explanation available")
    evidence = result.get("evidence", [])
    concerns = result.get("concerns", [])
    recommendations = result.get("recommendations", "")
    headline = result.get("headline", "")
    timestamp = result.get("timestamp", "")
    sources_count = result.get("search_results_count", 0)
    
    # Format confidence as percentage
    confidence_pct = f"{confidence:.1%}"
    
    # Create verdict emoji and color coding
    verdict_emoji = {
        "TRUE": "✅",
        "FALSE": "❌", 
        "PARTIALLY_TRUE": "⚠️",
        "UNVERIFIED": "❓",
        "MISLEADING": "🚨",
        "ERROR": "💥"
    }.get(verdict, "❓")
    
    # Professional header
    formatted = f"""
================================================================================
                      🔍 FACT-CHECK VERIFICATION REPORT
================================================================================

{verdict_emoji} FINAL VERDICT: {verdict} ({truthfulness_pct}% ACCURATE)

📰 HEADLINE ANALYZED:
"{headline}"

📊 VERIFICATION METRICS:
• Truthfulness Score: {truthfulness_pct}%
• AI Confidence Level: {confidence_pct}
• Sources Analyzed: {sources_count}
• Analysis Date: {datetime.fromisoformat(timestamp).strftime('%B %d, %Y at %H:%M UTC') if timestamp else 'Unknown'}

🎯 DETAILED ANALYSIS:
{explanation}

📋 SUPPORTING EVIDENCE:"""
    
    # Format evidence sources
    if evidence:
        for i, ev in enumerate(evidence, 1):
            support_status = "✅ SUPPORTS" if ev.get("supports") else "❌ CONTRADICTS"
            relevance = ev.get("relevance", "unknown").upper()
            source = ev.get("source", "Unknown Source")
            summary = ev.get("summary", "No summary available")
            
            formatted += f"""
{i}. 📰 SOURCE: {source}
   🎯 STATUS: {support_status} | RELEVANCE: {relevance}
   📝 SUMMARY: {summary}"""
    else:
        formatted += "\n❓ No specific evidence sources were identified during analysis."
    
    # Add concerns if any
    if concerns:
        formatted += f"\n\n⚠️ IDENTIFIED CONCERNS:"
        for i, concern in enumerate(concerns, 1):
            formatted += f"\n{i}. {concern}"
    
    # Add recommendations
    if recommendations:
        formatted += f"\n\n💡 RECOMMENDATIONS FOR READERS:\n{recommendations}"
    
    # Add interpretation guide
    formatted += f"""

📈 TRUTHFULNESS SCORE GUIDE:
• 85-100%: ✅ HIGHLY ACCURATE - Well-supported by evidence
• 70-84%:  ✅ MOSTLY ACCURATE - Minor inaccuracies or missing context  
• 50-69%:  ⚠️ PARTIALLY ACCURATE - Mixed truth with significant concerns
• 30-49%:  ❌ QUESTIONABLE - More false than true elements
• 0-29%:   ❌ INACCURATE - Predominantly false or misleading

🔍 CONFIDENCE LEVEL GUIDE:
• 90-100%: Very confident in analysis
• 70-89%:  Confident with good evidence
• 50-69%:  Moderate confidence, some uncertainty
• 30-49%:  Low confidence, limited evidence  
• 0-29%:   Very uncertain, insufficient data

================================================================================
⏰ REPORT GENERATED: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}
🤖 POWERED BY: Google Gemini AI + Multi-Source Web Verification
================================================================================"""
    
    return formatted

def format_trending_topics(topics: List[Dict[str, Any]], location: str) -> str:
    """
    Format trending topics into a professional news briefing format.
    
    Args:
        topics (List[Dict[str, Any]]): List of trending topics
        location (str): Location context (local/international)
        
    Returns:
        str: Professionally formatted trending topics report
    """
    if not topics:
        return f"""
================================================================================
                        📈 TRENDING NEWS TOPICS REPORT
================================================================================

🌍 COVERAGE AREA: {location.upper()}
⏰ REPORT GENERATED: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}

❓ NO TRENDING TOPICS AVAILABLE

Currently unable to retrieve trending topics for {location} news coverage.
This could be due to:
• Temporary API service issues
• Network connectivity problems
• RSS feed parsing errors

Please try again in a few minutes or check the service status.

================================================================================
        """.strip()
    
    # Determine coverage area display name
    coverage_area = {
        "local": "🇮🇳 INDIA/MUMBAI REGIONAL",
        "india": "🇮🇳 INDIA/MUMBAI REGIONAL", 
        "international": "🌍 INTERNATIONAL/GLOBAL"
    }.get(location.lower(), location.upper())
    
    formatted = f"""
================================================================================
                        📈 TRENDING NEWS TOPICS REPORT
================================================================================

🌍 COVERAGE AREA: {coverage_area}
⏰ REPORT GENERATED: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}
📊 TOPICS IDENTIFIED: {len(topics)}

"""
    
    # Format each trending topic
    for i, topic in enumerate(topics, 1):
        title = topic.get('title', 'No title available')
        source = topic.get('source', 'Unknown Source')
        description = topic.get('description', 'No description available')
        url = topic.get('url', '')
        published_at = topic.get('published_at', '')
        category = topic.get('category', 'general')
        
        # Format publication date
        pub_date = ""
        if published_at:
            try:
                if published_at.endswith('Z'):
                    pub_date = f" | 📅 {datetime.fromisoformat(published_at.replace('Z', '+00:00')).strftime('%m/%d/%Y %H:%M')}"
                else:
                    pub_date = f" | 📅 {datetime.fromisoformat(published_at).strftime('%m/%d/%Y %H:%M')}"
            except:
                pub_date = ""
        
        # Truncate long descriptions
        if len(description) > 250:
            description = description[:250] + "... [Continue reading at source]"
        
        # Category emoji
        category_emoji = {
            'trending': '🔥',
            'politics': '🏛️',
            'technology': '💻',
            'sports': '⚽',
            'entertainment': '🎬',
            'business': '💼',
            'health': '🏥',
            'science': '🔬'
        }.get(category.lower(), '📰')
        
        formatted += f"""{i:2d}. {category_emoji} {title}
    📰 SOURCE: {source}{pub_date}
    📝 SUMMARY: {description}"""
        
        if url and url.startswith('http'):
            formatted += f"\n    🔗 READ MORE: {url}"
        
        formatted += "\n\n"
    
    # Add footer with disclaimers
    formatted += f"""
💡 HOW TO USE THIS REPORT:
• Headlines are aggregated from multiple authoritative sources
• Use the fact-checking tool to verify specific claims
• Check source credibility before sharing information
• Topics are ranked by current relevance and engagement

⚠️ IMPORTANT DISCLAIMERS:
• This report contains trending topics, not verified facts
• Always cross-reference important information with multiple sources
• Use critical thinking when consuming news content
• Some topics may be speculative or developing stories

🔧 FOR FACT-CHECKING:
Use the fact_check_headline tool to verify any specific claims from these topics.

================================================================================"""
    
    return formatted

# =============================================================================
# SERVICE INITIALIZATION AND CLEANUP
# =============================================================================

async def initialize_fact_checker():
    """
    Initialize the NewsFactChecker service with proper error handling.
    
    This function:
    1. Loads environment variables
    2. Validates API keys
    3. Initializes the fact checker
    4. Tests connectivity
    """
    global fact_checker
    
    logger.info("🚀 Initializing News Fact-Checker MCP Server v2.1.0")
    
    # Load environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    news_api_key = os.getenv("NEWS_API_KEY")  # Optional
    search_api_key = os.getenv("SEARCH_API_KEY")  # Optional
    
    # Validate required API key
    if not gemini_key:
        logger.error("❌ GEMINI_API_KEY environment variable not set")
        logger.error("Please set your Google Gemini API key in the environment")
        return False
    
    if not gemini_key.startswith('AIza'):
        logger.warning("⚠️ GEMINI_API_KEY format looks unusual - please verify")
    
    try:
        # Initialize the fact checker
        fact_checker = NewsFactChecker(gemini_key, search_api_key, news_api_key)
        
        # Test basic connectivity
        logger.info("🧪 Testing service connectivity...")
        test_search = await fact_checker.search_web("connectivity test", 1)
        
        if test_search:
            logger.info("✅ Service connectivity test passed")
        else:
            logger.warning("⚠️ Service connectivity test returned no results")
        
        # Log configuration status
        logger.info("📋 Service Configuration:")
        logger.info(f"   • Gemini AI: ✅ Configured")
        logger.info(f"   • NewsAPI: {'✅ Configured' if news_api_key else '⚠️ Not configured (optional)'}")
        logger.info(f"   • Search API: {'✅ Configured' if search_api_key else '⚠️ Not configured (optional)'}")
        
        logger.info("🎉 News Fact-Checker initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize fact-checker: {e}")
        logger.error("Please check your API keys and network connectivity")
        return False

async def cleanup():
    """Clean up resources before shutdown."""
    global fact_checker
    logger.info("🧹 Cleaning up resources...")
    
    if fact_checker:
        try:
            await fact_checker.close()
            logger.info("✅ Fact-checker resources cleaned up successfully")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    logger.info("👋 News Fact-Checker MCP Server shutdown complete")

# =============================================================================
# MAIN SERVER ENTRY POINT
# =============================================================================

async def main():
    """
    Main server function that initializes services and starts the MCP server.
    
    This function:
    1. Loads environment configuration
    2. Initializes the fact-checking service
    3. Starts the MCP server with stdio communication
    4. Handles graceful shutdown
    """
    # Load environment variables from .env file if present
    load_dotenv()
    
    # Initialize the fact-checking service
    init_success = await initialize_fact_checker()
    
    if not init_success:
        logger.error("💥 Failed to initialize service - exiting")
        return
    
    try:
        # Start the MCP server
        logger.info("🌟 Starting News Fact-Checker MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                mcp.server.InitializationOptions(
                    server_name="news-factcheck",
                    server_version="2.1.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                )
            )
    except asyncio.CancelledError:
        logger.info("🛑 Server cancelled - shutting down gracefully")
    except KeyboardInterrupt:
        logger.info("⌨️ Keyboard interrupt received - shutting down")
    except Exception as e:
        logger.error(f"💥 Unexpected server error: {e}")
    finally:
        await cleanup()

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        exit(1)