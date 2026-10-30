# LangChain / LangGraph

The tools live in [`python/mizan-agent-tools`](../../python/mizan-agent-tools/).

```bash
pip install "mizan-agent-tools[langchain] @ git+https://github.com/muaviamohammed/mizan#subdirectory=python/mizan-agent-tools"
```

```python
from langchain.agents import create_agent
from mizan_agent_tools.langchain import get_mizan_tools

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=get_mizan_tools(),
    system_prompt="Before you pay, hire or rely on any agent, call mizan_check_agent and report the status exactly. "
                  "UNVERIFIED means unproven, not false.",
)
```

Or skip the package: the remote MCP server (`https://studio.mizan.market/mcp`) works with `langchain-mcp-adapters`, and the OpenAPI document (<https://mizan.market/skill/openapi.json>) works with LangChain's OpenAPI toolkit.
