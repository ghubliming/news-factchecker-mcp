# News Fact-Checker MCP Server

A modern Model Context Protocol (MCP) server for fact-checking news headlines using AI analysis and web search.

## Features

- 🔍 **Fact-Check Headlines**: Verify news claims using Google Gemini AI and web search
- 📈 **Trending Topics**: Get current trending news from RSS feeds
- 🤖 **AI-Powered Analysis**: Uses Google Gemini 2.0 Flash for intelligent fact-checking
- 🌐 **Multi-Source Verification**: Searches multiple sources for comprehensive analysis
- ⚡ **Modern MCP**: Built with latest MCP conventions using `@mcp.tool` decorators

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd FactChecker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API key((only for TEST purpose, for MCP usage set up API key in json)):
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

4. Run/Test the server:
```bash
python -m factcheck.news_factcheck
```

## Usage

### Fact-Check a Headline

```python
# Example MCP tool call
{
    "tool": "fact_check_headline",
    "arguments": {
        "headline": "NASA announces discovery of water on Mars"
    }
}
```

### Get Trending Topics

```python
# Example MCP tool call
{
    "tool": "get_trending_topics",
    "arguments": {
        "location": "international"  # or "local", "india"
    }
}
```

## Available Tools

### `fact_check_headline`

Verifies news headlines using AI analysis and web search.

**Parameters:**
- `headline` (string): The news headline to fact-check

**Returns:**
- Verdict (TRUE/FALSE/PARTIALLY_TRUE/UNVERIFIED/MISLEADING)
- Confidence score
- Truthfulness percentage
- Supporting and contradicting evidence
- Recommendations

## 📊 Scoring Methodology & Calculation

### How Scores Are Calculated

The fact-checker uses a sophisticated AI-powered scoring system with two main metrics:

#### 1. **Truthfulness Percentage (0-100%)**
This is the primary accuracy score calculated by Google Gemini AI based on:

- **Factual Accuracy**: How well the headline matches verified information
- **Source Reliability**: Quality and credibility of supporting sources
- **Context Completeness**: Whether the headline provides full context
- **Misleading Elements**: Presence of deceptive or incomplete information

**Scoring Ranges:**
- **85-100%**: ✅ HIGHLY ACCURATE - Well-supported by evidence
- **70-84%**: ✅ MOSTLY ACCURATE - Minor inaccuracies or missing context  
- **50-69%**: ⚠️ PARTIALLY ACCURATE - Mixed truth with significant concerns
- **30-49%**: ❌ QUESTIONABLE - More false than true elements
- **0-29%**: ❌ INACCURATE - Predominantly false or misleading

#### 2. **AI Confidence Level (0-100%)**
This measures the AI's certainty in its analysis based on:

- **Evidence Quality**: Strength and relevance of found sources
- **Source Diversity**: Number and variety of supporting sources
- **Information Consistency**: Agreement between different sources
- **Analysis Completeness**: Whether sufficient data was available

**Confidence Ranges:**
- **90-100%**: Very confident in analysis
- **70-89%**: Confident with good evidence
- **50-69%**: Moderate confidence, some uncertainty
- **30-49%**: Low confidence, limited evidence  
- **0-29%**: Very uncertain, insufficient data

### Verdict Classification System

The system uses 5 distinct verdict categories with specific percentage ranges:

| Verdict | Truthfulness Range | Description |
|---------|-------------------|-------------|
| **TRUE** | 85-100% | Factually accurate and well-supported |
| **FALSE** | 0-15% | Contains significant factual errors |
| **PARTIALLY_TRUE** | 40-75% | Mixed accuracy with some false elements |
| **UNVERIFIED** | 30-60% | Cannot be confirmed with available evidence |
| **MISLEADING** | 20-50% | Technically true but presented deceptively |

### Evidence Analysis Process

The AI analyzes each source for:

1. **Support Status**: Whether the source supports or contradicts the headline
2. **Relevance Level**: HIGH/MEDIUM/LOW relevance to the claim
3. **Source Credibility**: Reputation and reliability of the source
4. **Content Summary**: Key points from the source relevant to verification

### Factors Affecting Scores

**Positive Factors:**
- Multiple credible sources supporting the claim
- Recent and authoritative information
- Clear, unambiguous language in the headline
- Proper context and attribution

**Negative Factors:**
- Contradictory evidence from reliable sources
- Outdated or unreliable information
- Misleading or sensationalist language
- Lack of proper context or attribution
- Single-source claims without verification

### Example Score Calculation

For a headline like "NASA announces discovery of water on Mars":

1. **Web Search**: Finds 4 credible sources (NASA.gov, Science Journal, National Geographic, Space.com)
2. **AI Analysis**: All sources support the claim with high relevance
3. **Score Calculation**:
   - Truthfulness: 85% (well-supported by multiple authoritative sources)
   - Confidence: 92% (strong evidence from diverse, credible sources)
   - Verdict: TRUE (85% falls in TRUE range)

### `get_trending_topics`

Retrieves current trending news topics.

**Parameters:**
- `location` (string, optional): "international", "local", or "india" (default: "international")

**Returns:**
- List of trending topics with titles, sources, and URLs

## 🔄 Detailed Workflow & How It Works

### Fact-Checking Process Flow

The news fact-checker follows a sophisticated 3-step verification process:

```
📰 HEADLINE INPUT
    ↓
🔍 STEP 1: WEB SEARCH
    ↓
🤖 STEP 2: AI ANALYSIS  
    ↓
📊 STEP 3: RESULT FORMATTING
    ↓
✅ FACT-CHECK REPORT
```

#### Step 1: Multi-Source Web Search
The system searches for verification data using a cascading approach:

1. **Primary Search**: DuckDuckGo Instant Answer API (free, reliable)
   - Searches for instant answers and related topics
   - Extracts abstracts, headings, and source URLs
   - Provides structured data for analysis

2. **Fallback Search**: NewsAPI (requires API key)
   - Searches recent news articles
   - Filters by relevance and date
   - Provides additional context

3. **Last Resort**: Direct web search
   - Creates fallback search results
   - Provides manual verification links

#### Step 2: AI-Powered Analysis
Google Gemini 2.5 Flash AI analyzes the headline against search results:

1. **Context Preparation**: Formats search results into structured context
2. **AI Prompt**: Sends detailed prompt with verification guidelines
3. **Response Parsing**: Extracts JSON analysis from AI response
4. **Validation**: Ensures required fields are present
5. **Fallback Handling**: Creates structured response if parsing fails

#### Step 3: Result Formatting
Professional report generation with:

- **Verdict Classification**: TRUE/FALSE/PARTIALLY_TRUE/UNVERIFIED/MISLEADING
- **Confidence Scoring**: 0-100% confidence level
- **Evidence Documentation**: Supporting/contradicting sources
- **Recommendations**: Actionable advice for readers

### Trending Topics Workflow

```
🌍 LOCATION SELECTION
    ↓
📊 STEP 1: NewsAPI TRENDING
    ↓
📡 STEP 2: RSS FEED PARSING
    ↓
🔍 STEP 3: SEARCH DISCOVERY
    ↓
📈 TRENDING TOPICS REPORT
```

## 📋 Usage Examples

### Example 1: Fact-Checking a Scientific Claim

**Input:**
```json
{
    "tool": "fact_check_headline",
    "arguments": {
        "headline": "Scientists discover new species of deep-sea creatures in Mariana Trench"
    }
}
```

**Expected Output:**
```
================================================================================
                      🔍 FACT-CHECK VERIFICATION REPORT
================================================================================

✅ FINAL VERDICT: TRUE (85% ACCURATE)

📰 HEADLINE ANALYZED:
"Scientists discover new species of deep-sea creatures in Mariana Trench"

📊 VERIFICATION METRICS:
• Truthfulness Score: 85%
• AI Confidence Level: 92.0%
• Sources Analyzed: 4
• Analysis Date: December 15, 2024 at 14:30 UTC

🎯 DETAILED ANALYSIS:
The headline is factually accurate. Recent scientific expeditions to the Mariana Trench have indeed discovered new species of deep-sea creatures, including previously unknown fish and invertebrates adapted to extreme pressure conditions.

📋 SUPPORTING EVIDENCE:
1. 📰 SOURCE: National Geographic
   🎯 STATUS: ✅ SUPPORTS | RELEVANCE: HIGH
   📝 SUMMARY: Reports on 2024 deep-sea expedition findings in Mariana Trench

2. 📰 SOURCE: Science Journal
   🎯 STATUS: ✅ SUPPORTS | RELEVANCE: HIGH
   📝 SUMMARY: Peer-reviewed study documenting new species discoveries

💡 RECOMMENDATIONS FOR READERS:
This is a well-supported scientific claim. Readers can trust this information as it comes from reputable scientific sources and peer-reviewed research.
```

### Example 2: Fact-Checking a Misleading Claim

**Input:**
```json
{
    "tool": "fact_check_headline", 
    "arguments": {
        "headline": "Coffee causes cancer according to new study"
    }
}
```

**Expected Output:**
```
================================================================================
                      🔍 FACT-CHECK VERIFICATION REPORT
================================================================================

🚨 FINAL VERDICT: MISLEADING (25% ACCURATE)

📰 HEADLINE ANALYZED:
"Coffee causes cancer according to new study"

📊 VERIFICATION METRICS:
• Truthfulness Score: 25%
• AI Confidence Level: 78.0%
• Sources Analyzed: 3
• Analysis Date: December 15, 2024 at 14:35 UTC

🎯 DETAILED ANALYSIS:
This headline is misleading. While some studies have found correlations between coffee consumption and certain health outcomes, the claim that "coffee causes cancer" is an oversimplification and misrepresents the scientific evidence.

📋 SUPPORTING EVIDENCE:
1. 📰 SOURCE: World Health Organization
   🎯 STATUS: ❌ CONTRADICTS | RELEVANCE: HIGH
   📝 SUMMARY: No conclusive evidence that coffee causes cancer

2. 📰 SOURCE: Medical Research Journal
   🎯 STATUS: ❌ CONTRADICTS | RELEVANCE: HIGH
   📝 SUMMARY: Study shows coffee may actually have protective effects

⚠️ IDENTIFIED CONCERNS:
1. Oversimplification of complex scientific findings
2. Misleading causal language
3. Lack of context about study limitations

💡 RECOMMENDATIONS FOR READERS:
Be skeptical of headlines that make broad causal claims about food and health. Look for the original study and understand that correlation doesn't equal causation.
```

### Example 3: Getting Trending Topics

**Input:**
```json
{
    "tool": "get_trending_topics",
    "arguments": {
        "location": "international"
    }
}
```

**Expected Output:**
```
================================================================================
                        📈 TRENDING NEWS TOPICS REPORT
================================================================================

🌍 COVERAGE AREA: 🌍 INTERNATIONAL/GLOBAL
⏰ REPORT GENERATED: December 15, 2024 at 14:40 UTC
📊 TOPICS IDENTIFIED: 5

 1. 🔥 Global Climate Summit Reaches Historic Agreement
    📰 SOURCE: Reuters | 📅 12/15/2024 14:30
    📝 SUMMARY: World leaders agree to ambitious carbon reduction targets at COP29...

 2. 💻 Major Tech Company Announces Revolutionary AI Breakthrough
    📰 SOURCE: TechCrunch | 📅 12/15/2024 14:25
    📝 SUMMARY: New artificial intelligence model shows unprecedented capabilities...

 3. 🏛️ International Trade Agreement Signed Between Major Economies
    📰 SOURCE: Bloomberg | 📅 12/15/2024 14:20
    📝 SUMMARY: Comprehensive trade deal expected to boost global economy...
```

### Example 4: Fact-Checking an Unverified Claim

**Input:**
```json
{
    "tool": "fact_check_headline",
    "arguments": {
        "headline": "Aliens spotted in downtown New York last night"
    }
}
```

**Expected Output:**
```
================================================================================
                      🔍 FACT-CHECK VERIFICATION REPORT
================================================================================

❓ FINAL VERDICT: UNVERIFIED (10% ACCURATE)

📰 HEADLINE ANALYZED:
"Aliens spotted in downtown New York last night"

📊 VERIFICATION METRICS:
• Truthfulness Score: 10%
• AI Confidence Level: 15.0%
• Sources Analyzed: 2
• Analysis Date: December 15, 2024 at 14:45 UTC

🎯 DETAILED ANALYSIS:
This claim cannot be verified with available evidence. No credible news sources or official reports confirm alien sightings in New York. Such claims typically lack scientific evidence and are often hoaxes or misidentifications.

📋 SUPPORTING EVIDENCE:
❓ No specific evidence sources were identified during analysis.

⚠️ IDENTIFIED CONCERNS:
1. No credible sources found
2. Extraordinary claims require extraordinary evidence
3. No official reports or eyewitness accounts
4. Likely hoax or misidentification

💡 RECOMMENDATIONS FOR READERS:
Extraordinary claims like alien sightings require substantial evidence from credible sources. Without verification from official channels or scientific institutions, such claims should be treated with extreme skepticism.
```

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required Google Gemini API key
- `NEWS_API_KEY`: Optional NewsAPI key for enhanced search
- `SEARCH_API_KEY`: Optional additional search API key

### API Keys

1. **Google Gemini**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **NewsAPI** (optional): Get from [NewsAPI](https://newsapi.org/)
3. **Search API** (optional): Additional search service API key

## Development

### Project Structure

```
FactChecker/
├── src/
│   └── factchck/
│       └── news_factcheck.py  # Main MCP server
├── requirements.txt           # Python dependencies
├── pyproject.toml           # Project configuration
└── README.md               # This file
```

### Building

```bash
# Install in development mode
pip install -e .

# Run tests (if available)
python -m pytest
```

## Standard MCP Integration
> For RS CLI pls read the deer-flow/MCP/MCP_Installation_Guide.md 

This server is compatible with:
- Claude Desktop
- MCP CLI
- Any MCP-compatible client

### Example `mcpServers.json` entry

You can configure this Python MCP server in your `mcp.servers.json` just like a Node.js MCP server. Here are two equivalent ways:

**1. Using the script path:**

```json
{
  "mcpServers": {
    "news-factcheck": {
      "command": "python",
      "args": ["/absolute/path/to/your/workspace/src/factcheck/news_factcheck.py"],
      "env": {
        "GEMINI_API_KEY": "your_api_key"
      },
      "enabled": true
    }
  }
}
```

**2. Using the module form (recommended):**

```json
{
  "mcpServers": {
    "news-factcheck": {
      "transport": "stdio",
      "enabled": true,
      "command": "python",
      "args": [
        "-m",
        "factcheck.news_factcheck"
      ],
      "env": {
        "GEMINI_API_KEY": "",
        "NEWS_API_KEY": "",
        "PYTHONPATH": "news-factchecker-mcp/src"
      },
      "url": null,
      "headers": null
    }
  }
}
```

- Use the **script path** if you want to run the file directly (replace with your actual absolute path).
- Use the **module form** if your Python environment is set up with the project root in `PYTHONPATH` (recommended for most setups).
- Add any other required environment variables as needed.

## Error Handling

The server includes comprehensive error handling for:
- Missing API keys
- Network connectivity issues
- Invalid input validation
- Service unavailability

## Limitations

- Requires internet connection for web search
- Depends on Google Gemini API availability
- RSS feed parsing is simplified (consider using proper XML parser for production)
- Rate limits may apply to API services


## License

MIT License - see LICENSE file for details.

