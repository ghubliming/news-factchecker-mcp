#!/usr/bin/env python3
"""
News Fact-Checker MCP Server
A Model Context Protocol server that fact-checks news headlines using web search and Gemini 2.5 Flash
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("news-factcheck-mcp")

class NewsFactChecker:
    def __init__(self, gemini_api_key: str, search_api_key: Optional[str] = None):
        """Initialize the fact checker with API keys"""
        self.gemini_api_key = gemini_api_key
        self.search_api_key = search_api_key
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # HTTP client for web requests
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web for information about the headline"""
        try:
            # Using DuckDuckGo Instant Answer API (free)
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
            
            # Get instant answer if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'Instant Answer'),
                    'snippet': data.get('Abstract'),
                    'url': data.get('AbstractURL', ''),
                    'source': data.get('AbstractSource', 'DuckDuckGo')
                })
            
            # Get related topics
            for topic in data.get('RelatedTopics', [])[:num_results-1]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('FirstURL', '').split('/')[-1] if topic.get('FirstURL') else 'Related Topic',
                        'snippet': topic.get('Text'),
                        'url': topic.get('FirstURL', ''),
                        'source': 'DuckDuckGo'
                    })
            
            # Fallback: Use a news API or web scraping service
            if not results:
                # Try NewsAPI (requires API key but has free tier)
                await self._search_news_api(query, results)
            
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    async def _search_news_api(self, query: str, results: List[Dict]) -> None:
        """Fallback search using NewsAPI"""
        try:
            if not self.search_api_key:
                return
                
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'apiKey': self.search_api_key,
                'sortBy': 'relevancy',
                'pageSize': 5,
                'language': 'en'
            }
            
            response = await self.http_client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for article in data.get('articles', []):
                    results.append({
                        'title': article.get('title', ''),
                        'snippet': article.get('description', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'Unknown')
                    })
        except Exception as e:
            logger.error(f"NewsAPI search error: {e}")
    
    async def analyze_with_gemini(self, headline: str, search_results: List[Dict]) -> Dict[str, Any]:
        """Use Gemini to analyze the headline against search results"""
        try:
            # Prepare context from search results
            context = "Search Results:\n"
            for i, result in enumerate(search_results, 1):
                context += f"{i}. Title: {result['title']}\n"
                context += f"   Source: {result['source']}\n"
                context += f"   Content: {result['snippet']}\n"
                context += f"   URL: {result['url']}\n\n"
            
            prompt = f"""You are a fact-checking expert. Analyze the following news headline against the provided search results.

HEADLINE TO FACT-CHECK: "{headline}"

{context}

Please provide a comprehensive fact-check analysis in the following JSON format:

{{
    "verdict": "TRUE" | "FALSE" | "PARTIALLY_TRUE" | "UNVERIFIED" | "MISLEADING",
    "confidence": 0.0-1.0,
    "explanation": "Detailed explanation of your analysis",
    "evidence": [
        {{
            "source": "source name",
            "supports": true/false,
            "relevance": "high/medium/low",
            "summary": "brief summary of what this source says"
        }}
    ],
    "concerns": ["list of any concerns or red flags"],
    "recommendations": "What readers should know or do"
}}

Guidelines:
- TRUE: The headline is factually accurate and well-supported
- FALSE: The headline contains significant factual errors
- PARTIALLY_TRUE: Some elements are true, others are false or misleading
- UNVERIFIED: Cannot be confirmed with available evidence
- MISLEADING: Technically true but presented in a way that misleads

Be thorough but concise. Focus on factual accuracy, not opinions."""
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # Extract JSON from response
            response_text = response.text
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    analysis = json.loads(json_match.group())
                    return analysis
                except json.JSONDecodeError:
                    pass
            
            # Fallback: create structured response from text
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.5,
                "explanation": response_text,
                "evidence": [],
                "concerns": ["Could not parse structured analysis"],
                "recommendations": "Manual verification recommended"
            }
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "explanation": f"Analysis failed: {str(e)}",
                "evidence": [],
                "concerns": ["Analysis service unavailable"],
                "recommendations": "Try again later or verify manually"
            }
    
    async def fact_check_headline(self, headline: str) -> Dict[str, Any]:
        """Main fact-checking function"""
        logger.info(f"Fact-checking headline: {headline}")
        
        # Search for information about the headline
        search_results = await self.search_web(headline)
        
        if not search_results:
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "explanation": "No search results found to verify this headline",
                "evidence": [],
                "concerns": ["No verifiable sources found"],
                "recommendations": "Seek additional sources before sharing"
            }
        
        # Analyze with Gemini
        analysis = await self.analyze_with_gemini(headline, search_results)
        
        # Add metadata
        analysis["headline"] = headline
        analysis["search_results_count"] = len(search_results)
        analysis["timestamp"] = datetime.now().isoformat()
        
        return analysis
    
    async def close(self):
        """Clean up resources"""
        await self.http_client.aclose()

# Global fact checker instance
fact_checker: Optional[NewsFactChecker] = None

# Create MCP server app
app = mcp.server.Server("news-factcheck")

@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="fact_check_headline",
            description="Fact-check a news headline using web search and AI analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "headline": {
                        "type": "string",
                        "description": "The news headline to fact-check"
                    }
                },
                "required": ["headline"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    global fact_checker
    if name == "fact_check_headline":
        if not fact_checker:
            return [TextContent(type="text", text="❌ Error: Fact checker not initialized. Please check your API keys.")]
        headline = arguments.get("headline", "")
        if not headline or not headline.strip():
            return [TextContent(type="text", text="❌ Error: No headline provided")]
        try:
            result = await fact_checker.fact_check_headline(headline.strip())
            return [TextContent(type="text", text=format_fact_check_result(result))]
        except Exception as e:
            logger.error(f"Fact-check error: {e}")
            return [TextContent(type="text", text=f"❌ Error during fact-checking: {str(e)}")]
    return [TextContent(type="text", text="Unknown tool")] 

@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="factcheck://status",
            name="Fact Checker Status",
            description="Current status of the fact-checking service",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    global fact_checker
    if uri == "factcheck://status":
        if fact_checker:
            return "✅ Fact checker is initialized and ready to verify news headlines"
        else:
            return "❌ Fact checker not initialized. Please ensure GEMINI_API_KEY is set in environment variables"
    return "Resource not found"

def format_fact_check_result(result: Dict[str, Any]) -> str:
    """Format the fact-check result for display"""
    verdict = result.get("verdict", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    explanation = result.get("explanation", "No explanation available")
    evidence = result.get("evidence", [])
    concerns = result.get("concerns", [])
    recommendations = result.get("recommendations", "")
    
    # Create verdict emoji
    verdict_emoji = {
        "TRUE": "✅",
        "FALSE": "❌", 
        "PARTIALLY_TRUE": "⚠️",
        "UNVERIFIED": "❓",
        "MISLEADING": "⚠️",
        "ERROR": "💥"
    }.get(verdict, "❓")
    
    formatted = f"""{verdict_emoji} **FACT-CHECK RESULT: {verdict}**
📊 **Confidence:** {confidence:.1%}

📝 **Analysis:**
{explanation}

🔍 **Evidence Summary:**"""
    
    if evidence:
        for i, ev in enumerate(evidence, 1):
            support_icon = "✓" if ev.get("supports") else "✗"
            formatted += f"\n{i}. {support_icon} {ev.get('source', 'Unknown')}: {ev.get('summary', 'No summary')}"
    else:
        formatted += "\nNo specific evidence sources available"
    
    if concerns:
        formatted += f"\n\n⚠️ **Concerns:**"
        for concern in concerns:
            formatted += f"\n• {concern}"
    
    if recommendations:
        formatted += f"\n\n💡 **Recommendations:**\n{recommendations}"
    
    formatted += f"\n\n⏰ **Checked:** {result.get('timestamp', 'Unknown time')}"
    
    return formatted

async def initialize_fact_checker():
    """Initialize the fact checker"""
    global fact_checker
    
    # Get API keys from environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    news_api_key = os.getenv("NEWS_API_KEY")  # Optional
    
    if not gemini_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        return
    
    try:
        fact_checker = NewsFactChecker(gemini_key, news_api_key)
        logger.info("News fact-checker initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize fact-checker: {e}")

async def cleanup():
    """Clean up resources"""
    global fact_checker
    if fact_checker:
        await fact_checker.close()

async def main():
    """Main server function"""
    load_dotenv()
    await initialize_fact_checker()
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                mcp.server.InitializationOptions(
                    server_name="news-factcheck",
                    server_version="1.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                )
            )
    except asyncio.CancelledError:
        pass
    finally:
        await cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass