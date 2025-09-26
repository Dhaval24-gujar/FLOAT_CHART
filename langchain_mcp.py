import asyncio

from langchain.agents.structured_output import ToolStrategy
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel , Field
from typing import Optional, List, Literal
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(title="LangChain MCP Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
)



class ChatRequest(BaseModel):
    query: str

class ToolCall(BaseModel):
    name:str=Field(...,description="Name of tool call")
    input: str = Field(..., description="Input given to the tool")
    output: str = Field(..., description="Output returned by the tool")

class Formatted_response(BaseModel):
    response: str = Field(..., description="Full response to the user's query")
    data: Optional[List[float]] = Field(None,description="List of float data points gathered, which can be plotted for user's better understanding ")
    visualization: Optional[Literal[
            "AreaChart",
            "BarChart",
            "LineChart",
            "ComposedChart",
            "PieChart",
            "RadarChart",
            "RadialBarChart",
            "ScatterChart",
            "FunnelChart",
            "Treemap",
            "SankeyChart",
        ]
    ] = Field(
        None,
        description="Type of visualization chart according to data (Recharts supported types)"
    )
    reasons: Optional[str] = Field(None,description="Reasons for the generated response")
    tools_called:Optional[List[ToolCall]] = Field(None,description="List of tools called")

async def chat(query):
    client = MultiServerMCPClient(
        {
            "floatchat-argo": {
                 "transport": "streamable_http",  # HTTP-based remote server
                "url": "http://127.0.0.1:8050/mcp",
            }
        }
    )

    tools = await client.get_tools()
    agent = create_agent(
       llm,
        tools,
        response_format=ToolStrategy(Formatted_response),

        prompt='''
        You are an Ocean Data Analyst AI Agent with MCP tools (run_query, list_tables, get_schema, etc.).
Role:
Explore and analyze oceanographic datasets (floats, BGC, Argo, satellite, ship data).
Use SQL safely and effectively: always check schemas with list_tables / get_schema, never modify data.
Generate optimized queries with joins, filters (time/depth/region), and aggregations.
Outputs:
Show step-by-step reasoning, queries, and clear summaries.
Adapt style:
Scientific: detailed, reproducible.
Decision support: concise, visual.
Exploratory: trends, anomalies, correlations.
Core Skills:
SQL mastery (design + optimization).
Oceanography expertise (temp, salinity, nutrients, currents, etc.).
Time-series, spatial, and statistical analysis.
Results must be scientifically sound and accessible.
'''
    )
   
    float_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": f"{query}"}]},
        return_intermediate_steps=False,

    )
    print("Float response:", float_response.get("structured_response"))
    return float_response.get("structured_response")

@app.post("/chat",response_model=Formatted_response)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint to interact with the LLM using MCP tools
    """
    try:
        response = await chat(request.query)
        print(response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "LangChain MCP Chat API",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Send a chat message to the LLM",
            "GET /": "This endpoint"
        }
    }

@app.get("/health")
async def health():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    # For development - you can run with: python langchain_mcp.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    # Original test code (commented out since we're now running the API server)
    # asyncio.run(chat("Give me the data about floats near bay of bengal"))
