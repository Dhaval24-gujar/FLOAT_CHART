import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI


from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
)   

async def main():
    client = MultiServerMCPClient(
        {
            "floatchat-argo": {
                "command": "python",
                "args": ["floatchat_fastmcp_server.py"],
                "cwd": ".",
                "transport": "stdio",
            }
        }
    )

    tools = await client.get_tools()
    agent = create_agent(
       llm,
        tools,
        prompt="You are a helpful assistant."
    )
    float_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "What is the latest float entry?Give me the temperature of it.Generate and execute queries for that."}]}
    )
    print("Float response:", float_response.get("messages",[0]))


if __name__ == "__main__":
    asyncio.run(main())
