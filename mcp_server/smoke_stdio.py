"""Manual end-to-end smoke test for the stdio MCP server.

Spawns server.py as a real subprocess and talks MCP over stdin/stdout — the same way the
ADK agent will. Proves the protocol layer (not just the lookups) works: initialize ->
list_tools -> call both tools -> confirm out-of-range refuses to guess.

Run from the repo root:   python -m mcp_server.smoke_stdio
(Unit tests live in mcp_server/tests/ and run under pytest; this one needs a live subprocess,
so it's a script you run by hand or in the demo, not a pytest case.)
"""
import asyncio
import json

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main() -> None:
    params = StdioServerParameters(command="python3", args=["-m", "mcp_server.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print("Tools advertised:", names)

            nap = json.loads((await session.call_tool(
                "get_nap_guidance", {"age_months": 10})).content[0].text)
            ms = json.loads((await session.call_tool(
                "get_milestone_checkin", {"age_months": 9})).content[0].text)
            oor = json.loads((await session.call_tool(
                "get_nap_guidance", {"age_months": 999})).content[0].text)

            print(f"  nap(10):        {nap['typical_naps']} naps · source {nap['source']} · tier {nap['tier']}")
            print(f"  milestone(9):   {ms['age_label']} · {len(ms['milestones'])} domains")
            print(f"  nap(999):       out_of_range={oor.get('out_of_range')} (no source: {'source' not in oor})")

            assert set(names) == {"get_nap_guidance", "get_milestone_checkin"}
            assert nap["source"] and nap["tier"]
            assert all(ms["milestones"].values())
            assert oor.get("out_of_range") is True and "source" not in oor
            print("\nOK — stdio handshake, tool listing, both calls, and no-guess all verified.")


if __name__ == "__main__":
    asyncio.run(main())
