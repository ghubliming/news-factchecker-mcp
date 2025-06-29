{
  "mcpServers": {
    "google-map": {
      "transport": "stdio",
      "enabled": false,
      "command": "node",
      "args": [
        "/home/liu/Documents/mcp-google-map/dist/index.cjs"
      ],
      "env": {
        "GOOGLE_MAPS_API_KEY": ""
      },
      "url": null,
      "headers": null
    }
  }
}

{
  "mcpServers": {
    "website-verifier": {
      "transport": "stdio",
      "enabled": false,
      "command": "node",
      "args": [
        "/home/liu/Documents/MCP_Website_Verification/dist/index.cjs"
      ],
      "env": {},
      "url": null,
      "headers": null
    }
  }
}


{
  "mcpServers": {
    "wolfram-alpha": {
      "transport": "stdio",
      "enabled": false,
      "command": "python",
      "args": [
        "-m",
        "mcp_wolfram_alpha"
      ],
      "env": {
        "WOLFRAM_API_KEY": "-",
        "PYTHONPATH": "/home/liu/Documents/MCP-wolfram-alpha/src"
      },
      "url": null,
      "headers": null
    }
  }
}

pip install -r requirements.txt
pip

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
        "PYTHONPATH": "/home/liu/Documents/news-factchecker-mcp/src"
      },
      "url": null,
      "headers": null
    }
  }
}