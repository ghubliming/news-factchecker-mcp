# News Fact-Checker MCP Server

A Model Context Protocol (MCP) server for automated fact-checking of news headlines and retrieving trending news topics using web search and Google Gemini AI. This project exposes tools for verifying the factual accuracy of news claims and for aggregating trending topics, suitable for integration with Claude Desktop, the MCP CLI, and other MCP-compatible clients.

---

## Features

- **Fact-check news headlines** using real-time web search and Gemini AI analysis
- **Trending topics aggregation**: Get the latest trending news by region (local/India/international)
- **Structured verdicts**: TRUE, FALSE, PARTIALLY_TRUE, UNVERIFIED, MISLEADING
- **Evidence summary** and confidence score
- **Professional, detailed reporting**
- **Easy integration** with Claude Desktop, MCP CLI, and other clients

---

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/adityapawar327/news-factchecker-mcp.git
   cd news-factchecker-mcp
   ```

2. **Create and activate a virtual environment (recommended):**
   ```sh
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

---

## Configuration

This server requires API keys for Google Gemini and (optionally) NewsAPI for enhanced news search and trending topics.

1. **Create a `.env` file in the project root:**
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   NEWS_API_KEY=your_newsapi_key_here  # Optional
   ```

2. **Do NOT commit your `.env` file or API keys to public repositories.**

---

## MCP Server Configuration for Claude Desktop

To use this server with Claude Desktop, add the following to your Claude MCP server config file:

```json
{
  "mcpServers": {
    "news-factcheck": {
      "command": "python",
      "args": [
        "src/factchck/news_factcheck.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "NEWS_API_KEY": "your_newsapi_key_here"
      }
    }
  }
}
```

- On Windows: Save as `%APPDATA%/Claude/claude_desktop_config.json`
- On macOS: Save as `~/Library/Application Support/Claude/claude_desktop_config.json`
- Replace the API keys with your own.
- Adjust the path in `args` if your project is in a different location.
- Restart Claude Desktop after saving.

---

## Usage

### Run the MCP Server

```sh
python src/factchck/news_factcheck.py
```

The server will start and expose its tools over MCP stdio.

---

### Using with Claude Desktop

1. Open Claude Desktop settings and add a new MCP server:
   - **Command:** `python`
   - **Arguments:** `src/factchck/news_factcheck.py`
   - (Set environment variables for API keys as needed)
2. Restart Claude Desktop. The "Fact Check Headline" and "Get Trending Topics" tools will appear in the tool menu.

---

### Using with MCP CLI

List available tools:
```sh
mcp tool list --server-stdio "python src/factchck/news_factcheck.py"
```

Call the fact-check tool:
```sh
mcp tool call --server-stdio "python src/factchck/news_factcheck.py" --tool fact_check_headline --args '{"headline": "NASA finds water on the Moon"}'
```

Call the trending topics tool:
```sh
mcp tool call --server-stdio "python src/factchck/news_factcheck.py" --tool get_trending_topics --args '{"location": "international"}'
```

---

## Example Output

### Fact-Check Headline

```
✅ FINAL VERDICT: TRUE (98% ACCURATE)
📰 HEADLINE ANALYZED:
"NASA finds water on the Moon"

📊 VERIFICATION METRICS:
• Truthfulness Score: 98%
• AI Confidence Level: 98.0%
• Sources Analyzed: 3
• Analysis Date: 2025-06-24

🎯 DETAILED ANALYSIS:
The claim is supported by multiple reputable sources...

📋 SUPPORTING EVIDENCE:
1. 📰 SOURCE: NASA
   🎯 STATUS: ✅ SUPPORTS | RELEVANCE: HIGH
   📝 SUMMARY: NASA confirms water molecules on the sunlit surface of the Moon...

💡 RECOMMENDATIONS FOR READERS:
Share with confidence, but always check for updates on scientific findings.

⏰ REPORT GENERATED: 2025-06-24
```

### Get Trending Topics

```
================================================================================
                        📈 TRENDING NEWS TOPICS REPORT
================================================================================

🌍 COVERAGE AREA: INTERNATIONAL/GLOBAL
⏰ REPORT GENERATED: 2025-06-24
📊 TOPICS IDENTIFIED: 10

 1. 🔥 Global Markets Rally Amid Economic Recovery
    📰 SOURCE: Reuters | 📅 06/24/2025 10:00
    📝 SUMMARY: Stock markets worldwide surged today as...
    🔗 READ MORE: https://reuters.com/example-article

 2. 🏥 COVID-19 Cases Decline in India
    📰 SOURCE: Times of India | 📅 06/24/2025 09:30
    📝 SUMMARY: The number of new COVID-19 cases in India has dropped...
    🔗 READ MORE: https://timesofindia.indiatimes.com/example-article

... (more topics)

================================================================================
```

---

## Contributing

Contributions are welcome! Please open issues or pull requests for improvements, bug fixes, or new features.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Security

- **Never commit your API keys or secrets.**
- Review all code and dependencies before deploying in production environments.

---

## Acknowledgments

- [Model Context Protocol (MCP)](https://github.com/modelcontext/mcp)
- [Google Gemini](https://ai.google.dev/gemini-api/docs)
- [DuckDuckGo Instant Answer API](https://duckduckgo.com/api)