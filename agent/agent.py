"""The ONE agent: an ADK LlmAgent that consumes the local MCP server via McpToolset.

IMPORTANT: this is a skeleton. Verify ADK class names / signatures against the CURRENT
ADK docs — the API moves. The point is the SHAPE: a real LlmAgent + a real McpToolset
+ the loop actually running. Importing ADK without instantiating it (the NutriGuard
mistake) does not count.
"""
import os
from .instructions import SYSTEM_INSTRUCTION

# from google.adk.agents import LlmAgent
# from google.adk.tools.mcp_tool import McpToolset, StdioServerParameters   # verify names

def build_agent():
    """Wire the agent to the stdio MCP server and return it.

    Collaborator learning goals:
      - McpToolset(StdioServerParameters(command="python", args=["-m","mcp_server.server"]))
        spawns our server and auto-exposes its 3 tools to the agent.
      - LlmAgent(model="gemini-...", instruction=SYSTEM_INSTRUCTION, tools=[toolset])
      - Then run it with the ADK runner so the model drives the decide/observe loop.
    """
    raise NotImplementedError("Build per current ADK docs — see docs/WORKPLAN.md arc 2-3.")


if __name__ == "__main__":
    assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in your environment (see .env.example)"
    build_agent()
