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

3. Set up your API key:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

4. Run the server:
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

### `get_trending_topics`

Retrieves current trending news topics.

**Parameters:**
- `location` (string, optional): "international", "local", or "india" (default: "international")

**Returns:**
- List of trending topics with titles, sources, and URLs

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

## MCP Integration

This server is compatible with:
- Claude Desktop
- MCP CLI
- Any MCP-compatible client

### Server Configuration

To use this server with an MCP-compatible client, add the following to your `mcp.servers.json`:

```json
{
  "mcpServers": {
    "news-factcheck": {
      "command": "python",
      "args": ["-m", "factcheck.news_factcheck"],
      "env": {
        "GEMINI_API_KEY": "your_api_key_here"
      },
      "enabled": true
    }
  }
}
```

- Replace `your_api_key_here` with your actual Google Gemini API key.
- You may also set optional `NEWS_API_KEY` and `SEARCH_API_KEY` in the `env` section if you have them.

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
      "command": "python",
      "args": ["-m", "factcheck.news_factcheck"],
      "env": {
        "GEMINI_API_KEY": "your_api_key"
      },
      "enabled": true
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Version History

- **v3.0.0**: Modernized with latest MCP conventions, simplified codebase
- **v2.1.0**: Previous version with complex multi-source search
- **v0.1.0**: Initial release

## Support

For issues and questions:
1. Check the error logs
2. Verify API key configuration
3. Ensure network connectivity
4. Open an issue on GitHub