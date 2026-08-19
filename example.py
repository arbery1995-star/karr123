"""Minimal example for using ScrapeGraphAI's SmartScraperGraph.

Requires an OPENAI_API_KEY (or another supported LLM provider) set as an
environment variable. See https://github.com/ScrapeGraphAI/Scrapegraph-ai
for the full list of supported models and configuration options.
"""

import os

from scrapegraphai.graphs import SmartScraperGraph

graph_config = {
    "llm": {
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "model": "openai/gpt-4o-mini",
    },
    "verbose": True,
    "headless": True,
}

smart_scraper_graph = SmartScraperGraph(
    prompt="List me all the articles",
    source="https://perinim.github.io/projects/",
    config=graph_config,
)

if __name__ == "__main__":
    result = smart_scraper_graph.run()
    print(result)
