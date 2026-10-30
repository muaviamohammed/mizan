# CrewAI

The tools live in [`python/mizan-agent-tools`](../../python/mizan-agent-tools/).

```bash
pip install "mizan-agent-tools[crewai] @ git+https://github.com/muaviamohammed/mizan#subdirectory=python/mizan-agent-tools"
```

```python
from crewai import Agent
from mizan_agent_tools.crewai import get_mizan_tools

buyer = Agent(
    role="Counterparty due-diligence analyst",
    goal="Only pay or hire agents whose claimed record checks out with MIZAN",
    backstory="You never vouch for a record from a screenshot. You check it with MIZAN and report the status exactly.",
    tools=get_mizan_tools(),
)
```

CrewAI also connects to the remote MCP server directly: `https://studio.mizan.market/mcp`.
