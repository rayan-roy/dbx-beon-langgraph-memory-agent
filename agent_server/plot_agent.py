"""Plot generation agent for CSV data visualization.

This module creates chart specifications from agent responses by analyzing CSV data
and generating JSON specs compatible with the frontend Chart renderer.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional

from databricks_langchain import ChatDatabricks, AsyncDatabricksStore
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.store.base import BaseStore

from agent_server.csv_tools import csv_tools
from agent_server.utils import ensure_lakebase_instance

logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1024"))
LAKEBASE_INSTANCE_NAME = ensure_lakebase_instance(os.getenv("LAKEBASE_INSTANCE_NAME", ""))

# System prompt for the plot generation agent
PLOT_SYSTEM_PROMPT = """You are a data visualization agent for a CSV data analysis platform.

You will receive the text of an agent response about CSV data analysis.
Your job is to determine if the response contains data that can be plotted, and if so,
use the CSV tools to get precise data and return a chart specification.

Available tools:
- describe_uploaded_csvs: Get metadata about uploaded CSV files (columns, row counts)  
- get_all_csv_data: Get complete dataset for comprehensive analysis
- search_uploaded_csv: Search for specific data rows using natural language

Your goal is to:
1. Analyze the agent response to understand what data visualization would be helpful
2. Use the CSV tools to get the actual data needed for the chart
3. Process and structure the data appropriately for visualization
4. Return a JSON chart specification

IMPORTANT: Do NOT include any import statements or code execution in your response. 
Only return the final JSON chart specification.

Return ONLY a JSON object (no markdown, no extra text) in this exact format:

If data IS suitable for plotting:
{"type": "bar"|"line"|"pie"|"area", "title": "Chart Title", "data": [{"name": "Label", "value": 123}, ...], "xKey": "name", "yKeys": ["value"], "text": "Brief one-sentence caption"}

For multi-series data use multiple yKeys:
{"type": "bar", "title": "...", "data": [{"name": "X", "series1": 10, "series2": 20}, ...], "xKey": "name", "yKeys": ["series1", "series2"], "text": "..."}

If data is NOT suitable for plotting:
{"no_data": true, "reason": "Brief explanation why"}

Rules:
- Always use the CSV tools to get actual data -- do not invent data
- Choose the chart type that best represents the data (bar for comparisons, line for time series, pie for proportions)
- Keep data arrays to 20 items or fewer. Aggregate or sample if needed
- Ensure all data values are numbers (not strings) for proper chart rendering
- Return ONLY the JSON object, nothing else
- Do NOT include any Python code, imports, or code blocks in your response
"""


async def create_plot_spec(content: str, history: Optional[List[Dict]] = None, thread_id: Optional[str] = None) -> Dict:
    """Generate a chart specification from agent response content.
    
    Args:
        content: The agent response text to analyze for plotting opportunities
        history: Previous conversation messages for context
        thread_id: Thread ID to access CSV data
    
    Returns:
        Dict containing chart specification or error information
    """
    try:
        # Initialize LLM
        llm = ChatDatabricks(endpoint="databricks-claude-sonnet-4-5", max_tokens=4000)
        
        # Build context from the content (limit to avoid token issues)
        context = f"Agent response to visualize:\n\n{content[:1500]}"
        
        if history:
            # Only use last message and truncate to avoid token limits
            recent = history[-1:] if len(history) > 0 else []
            history_text = "\n".join([
                f"{m.get('role', 'unknown')}: {str(m.get('content', ''))[:400]}" 
                for m in recent if isinstance(m, dict)
            ])
            context = f"Previous message:\n{history_text}\n\nAgent response to visualize:\n\n{content[:1500]}"

        # Try to create a simple chart spec first without using tools if possible
        if thread_id and thread_id != 'current-session':
            # Initialize store for CSV data access
            async with AsyncDatabricksStore(
                instance_name=LAKEBASE_INSTANCE_NAME,
                embedding_endpoint=EMBEDDING_ENDPOINT,
                embedding_dims=EMBEDDING_DIMS,
            ) as store:
                await store.setup()
                
                # Get CSV tools with proper configuration
                tools = csv_tools()
                
                # Create agent with CSV tools
                agent = create_react_agent(llm, tools)
                
                # Configure the agent with thread_id and store for CSV access
                config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "store": store
                    },
                    "recursion_limit": 10  # Limit recursion to prevent infinite loops
                }
                
                # Run the agent asynchronously using streaming to ensure proper tool execution
                try:
                    messages = [SystemMessage(content=PLOT_SYSTEM_PROMPT), HumanMessage(content=context)]
                    
                    final_result = None
                    async for chunk in agent.astream({"messages": messages}, config=config):
                        if "agent" in chunk:
                            final_result = chunk["agent"]
                        elif "messages" in chunk:
                            final_result = {"messages": chunk["messages"]}
                    
                    if final_result and "messages" in final_result:
                        result = final_result
                    else:
                        # Fallback to regular invoke if streaming doesn't work
                        result = await agent.ainvoke({"messages": messages}, config=config)
                
                except Exception as agent_error:
                    logger.error(f"Agent execution error: {agent_error}")
                    # Just return a simple chart based on the content without tools
                    return _create_fallback_chart_spec(content)
        else:
            # No thread_id provided, create a simple fallback chart
            return _create_fallback_chart_spec(content)
            
        # Extract JSON response from the last AI message
        if result and "messages" in result:
            for msg in reversed(result.get("messages", [])):
                if isinstance(msg, AIMessage) and msg.content:
                    text = msg.content.strip()
                    
                    # Clean up any markdown formatting
                    if text.startswith("```"):
                        lines = text.split("\n")
                        text = "\n".join(lines[1:]) if len(lines) > 1 else text[3:]
                        if text.endswith("```"):
                            text = text[:-3].strip()
                    
                    # Try to extract JSON from the response
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        try:
                            parsed_result = json.loads(json_match.group(0))
                            logger.info(f"Successfully parsed plot spec: {parsed_result}")
                            return parsed_result
                        except json.JSONDecodeError:
                            pass
                    
                    # Try parsing the whole text as JSON
                    try:
                        parsed_result = json.loads(text)
                        logger.info(f"Successfully parsed plot spec: {parsed_result}")
                        return parsed_result
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse agent JSON response: {e}")
                        logger.warning(f"Response text: {text}")
                        continue
        
        # Return fallback chart if all else fails
        return _create_fallback_chart_spec(content)
        
    except Exception as e:
        logger.error(f"Plot generation error: {e}", exc_info=True)
        return {
            "no_data": True, 
            "reason": f"Error generating chart: {str(e)}"
        }


def _create_fallback_chart_spec(content: str) -> Dict:
    """Create a simple fallback chart spec when tools fail."""
    # Check if content mentions specific data types
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['trend', 'time', 'month', 'year', 'date']):
        return {
            "type": "line",
            "title": "Data Trend Over Time", 
            "data": [
                {"name": "Jan", "value": 10},
                {"name": "Feb", "value": 15},
                {"name": "Mar", "value": 12},
                {"name": "Apr", "value": 18},
                {"name": "May", "value": 20}
            ],
            "xKey": "name",
            "yKeys": ["value"],
            "text": "Sample trend data - upload CSV data for actual visualization"
        }
    elif any(word in content_lower for word in ['compare', 'top', 'category', 'group']):
        return {
            "type": "bar",
            "title": "Category Comparison",
            "data": [
                {"name": "Category A", "value": 25},
                {"name": "Category B", "value": 30},
                {"name": "Category C", "value": 20},
                {"name": "Category D", "value": 15}
            ],
            "xKey": "name", 
            "yKeys": ["value"],
            "text": "Sample comparison data - upload CSV data for actual visualization"
        }
    else:
        return {
            "no_data": True,
            "reason": "Please upload CSV data first, then ask analytical questions to generate visualizations"
        }


def _parse_csv_data_for_chart(csv_text: str, chart_type: str = "bar") -> List[Dict]:
    """Helper function to parse CSV data text into chart-ready format.
    
    Args:
        csv_text: Raw CSV data as text
        chart_type: Type of chart to optimize for
    
    Returns:
        List of dictionaries suitable for chart rendering
    """
    try:
        lines = csv_text.strip().split('\n')
        if len(lines) < 2:
            return []
        
        # Parse header and data rows
        headers = [h.strip() for h in lines[0].split('|') if h.strip()]
        data_rows = []
        
        for line in lines[1:]:
            if line.strip() and '|' in line:
                values = [v.strip() for v in line.split('|') if v.strip()]
                if len(values) == len(headers):
                    row_dict = {}
                    for i, header in enumerate(headers):
                        value = values[i]
                        # Try to convert to number
                        try:
                            row_dict[header] = float(value) if '.' in value else int(value)
                        except ValueError:
                            row_dict[header] = value
                    data_rows.append(row_dict)
        
        return data_rows[:20]  # Limit to 20 items
        
    except Exception as e:
        logger.error(f"Error parsing CSV data: {e}")
        return []