from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import asyncio
import json
import re

from dotenv import load_dotenv
from tools.schedule_tool import create_daily_schedule
load_dotenv()

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from typing import List, Dict, Any
from state import TravelState

from langchain.prompts import ChatPromptTemplate
from base_llm import llm

# Import nodes
from nodes.orchestrator import orchestrator_agent
from nodes.places import gather_places_agent, execute_gather_places
from nodes.transport import travel_planner_agent
from nodes.routes import distance_matrix_agent, execute_distance_matrix, route_optimizer_agent
from nodes.scheduler import visit_scheduler_agent
from nodes.synthesizer import synthesizer_agent
from nodes.accomodation import accommodation_agent

# Pydantic models for API
class TravelRequest(BaseModel):
    destination: str
    origin: Optional[str] = None
    days: int = 3
    theme: str = "general"
    start_date: Optional[str] = "September 20 2025"
    end_date: Optional[str] = "September 25 2025"

class TravelResponse(BaseModel):
    success: bool
    itinerary: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

def route_next_step(state: TravelState):
    """Route to the next appropriate step with new agents"""
    next_step = state.get("next_step", "orchestrator")
    
    # Additional validation for new flow
    if next_step == "plan_travel" and not state.get("origin"):
        next_step = "gather_places"
    elif next_step == "gather_places" and not state.get("places"):
        # Normal flow continues
        pass
    elif next_step == "suggest_stays" and not (state.get("places") or state.get("optimal_route")):
        next_step = "gather_places"  # Need places first
    elif next_step == "generate_distance_matrix" and not state.get("places"):
        next_step = "synthesizer"
    elif next_step == "generate_route" and not state.get("places"):
        next_step = "synthesizer"
    elif next_step == "schedule_visits" and not (state.get("optimal_route") or state.get("places")):
        next_step = "synthesizer"
    
    print(f"🧭 Routing to: {next_step}")
    return next_step

def build_multi_agent_graph():
    """Build the multi-agent travel planning graph with new agents"""
    
    workflow = StateGraph(TravelState)
    
    # Add all agent nodes (existing + new)
    workflow.add_node("orchestrator", orchestrator_agent)
    workflow.add_node("plan_travel", travel_planner_agent)  # NEW
    workflow.add_node("gather_places", gather_places_agent)
    workflow.add_node("execute_gather_places", execute_gather_places)
    workflow.add_node("generate_distance_matrix", distance_matrix_agent)
    workflow.add_node("execute_distance_matrix", execute_distance_matrix)
    workflow.add_node("generate_route", route_optimizer_agent)
    workflow.add_node("schedule_visits", visit_scheduler_agent)
    workflow.add_node("suggest_stays", accommodation_agent)  # NEW
    workflow.add_node("synthesizer", synthesizer_agent)
    
    # Start with orchestrator
    workflow.add_edge(START, "orchestrator")
    
    # Add conditional routing from each node
    workflow.add_conditional_edges(
        "orchestrator",
        route_next_step,
        {
            "plan_travel": "plan_travel",  # NEW
            "gather_places": "gather_places",
            "synthesizer": "synthesizer",
            "generate_distance_matrix": "generate_distance_matrix",
            "generate_route": "generate_route",
            "schedule_visits": "schedule_visits",
            "suggest_stays": "suggest_stays"  # NEW
        }
    )
    
    # NEW: Travel planner routing
    workflow.add_conditional_edges(
        "plan_travel",
        route_next_step,
        {
            "gather_places": "gather_places",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "gather_places",
        route_next_step,
        {
            "execute_gather_places": "execute_gather_places",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "execute_gather_places",
        route_next_step,
        {
            "generate_distance_matrix": "generate_distance_matrix",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "generate_distance_matrix", 
        route_next_step,
        {
            "execute_distance_matrix": "execute_distance_matrix",
            "generate_route": "generate_route",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "execute_distance_matrix",
        route_next_step,
        {
            "generate_route": "generate_route",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "generate_route",
        route_next_step,
        {
            "schedule_visits": "schedule_visits",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "schedule_visits",
        route_next_step,
        {
            "suggest_stays": "suggest_stays",  # NEW: After schedule, suggest accommodations
            "synthesizer": "synthesizer"
        }
    )
    
    # NEW: Accommodation agent routing
    workflow.add_conditional_edges(
        "suggest_stays",
        route_next_step,
        {
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "synthesizer",
        route_next_step,
        {
            "END": END
        }
    )
    
    return workflow.compile()

def create_initial_state_from_request(request: TravelRequest):
    """Create initial state from API request"""
    user_query = f"Plan a {request.days}-day {request.theme} trip to {request.destination}"
    if request.origin:
        user_query += f" from {request.origin}"
    
    return {
        "days": request.days,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "destination": request.destination,
        "origin": request.origin,
        "theme": request.theme,
        "user_query": user_query,
        "messages": [],
        "query_type": "",
        "next_step": "orchestrator",
        "places": None,
        "original_places": None,
        "distance_matrix": None,
        "optimal_route": None,
        "daily_schedule": None,
        "travel_info": None,
        "accommodations": None,
        "effective_days": None
    }

def get_node_description(node_name: str) -> str:
    """Get human-readable description for each node"""
    descriptions = {
        "orchestrator": "🎯 Analyzing your request and planning the workflow",
        "plan_travel": "🚗 Planning travel routes and transportation",
        "gather_places": "📍 Discovering amazing places to visit",
        "execute_gather_places": "🔍 Gathering detailed place information",
        "generate_distance_matrix": "📏 Calculating distances between locations", 
        "execute_distance_matrix": "🗺️ Computing optimal travel distances",
        "generate_route": "🛣️ Optimizing your travel route",
        "schedule_visits": "📅 Creating your daily schedule",
        "suggest_stays": "🏨 Finding accommodation options",
        "synthesizer": "✨ Creating your final itinerary"
    }
    return descriptions.get(node_name, f"🔄 Processing {node_name}")

async def stream_travel_planning(request: TravelRequest) -> AsyncGenerator[str, None]:
    """Stream the travel planning process with real-time updates"""
    
    try:
        # Send initial message
        yield f"data: {json.dumps({'type': 'status', 'message': f'🚀 Starting your {request.days}-day trip to {request.destination}...'})}\n\n"
        
        # Create initial state
        initial_state = create_initial_state_from_request(request)
        
        # Initialize the graph
        graph = build_multi_agent_graph()
        
        current_step = ""
        step_count = 0
        
        # Stream events from the graph
        async for event in graph.astream(initial_state):
            step_count += 1
            
            # Extract node information from event
            if isinstance(event, dict):
                for node_name, node_data in event.items():
                    if node_name != current_step:
                        current_step = node_name
                        description = get_node_description(node_name)
                        
                        # Send step update
                        yield f"data: {json.dumps({'type': 'step', 'step': step_count, 'node': node_name, 'description': description})}\n\n"
                        
                        # Send progress update
                        progress = min(step_count * 10, 90)  # Cap at 90% until completion
                        yield f"data: {json.dumps({'type': 'progress', 'percentage': progress})}\n\n"
                    
                    # Check for messages or content in the node data
                    if isinstance(node_data, dict):
                        # Stream any new messages
                        messages = node_data.get('messages', [])
                        if messages and len(messages) > 0:
                            last_message = messages[-1]
                            if hasattr(last_message, 'content') and last_message.content:
                                # Check if this is the final synthesizer content
                                if node_name == "synthesizer" and len(last_message.content) > 100:
                                    yield f"data: {json.dumps({'type': 'partial_content', 'content': last_message.content[:200] + '...'})}\n\n"
                        
                        # Stream key updates
                        if node_data.get('places') and len(node_data['places']) > 0:
                            place_count = len(node_data['places'])
                            yield f"data: {json.dumps({'type': 'update', 'message': f'🎯 Found {place_count} amazing places to visit!'})}\n\n"
                        
                        if node_data.get('optimal_route'):
                            yield f"data: {json.dumps({'type': 'update', 'message': '🛣️ Optimized your travel route!'})}\n\n"
                        
                        if node_data.get('daily_schedule'):
                            yield f"data: {json.dumps({'type': 'update', 'message': '📅 Created your daily schedule!'})}\n\n"
                        
                        if node_data.get('accommodations'):
                            yield f"data: {json.dumps({'type': 'update', 'message': '🏨 Found accommodation suggestions!'})}\n\n"
        
        # Get final result
        yield f"data: {json.dumps({'type': 'status', 'message': '🎉 Finalizing your perfect itinerary...'})}\n\n"
        
        # Execute one final time to get the complete result
        final_result = await graph.ainvoke(initial_state)
        
        # Extract final itinerary
        final_content = ""
        if final_result and "messages" in final_result and final_result["messages"]:
            last_message = final_result["messages"][-1]
            if hasattr(last_message, 'content') and last_message.content:
                final_content = last_message.content
        
        # Send completion
        yield f"data: {json.dumps({'type': 'progress', 'percentage': 100})}\n\n"
        yield f"data: {json.dumps({'type': 'complete', 'itinerary': final_content, 'success': True})}\n\n"
        
    except Exception as e:
        error_msg = f"❌ Error during planning: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg, 'success': False})}\n\n"

# Initialize the graph
graph = build_multi_agent_graph()

# FastAPI app
app = FastAPI(
    title="Streaming Travel Planning API",
    description="AI-powered travel itinerary generator with real-time streaming",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Streaming Travel Planning API is running!"}

@app.post("/plan-trip-stream")
async def plan_trip_stream(request: TravelRequest):
    """
    Stream the trip planning process in real-time.
    Returns Server-Sent Events (SSE) stream.
    """
    return StreamingResponse(
        stream_travel_planning(request),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.post("/plan-trip", response_model=TravelResponse)
async def plan_trip(request: TravelRequest):
    """
    Plan a trip and return the complete result (non-streaming version).
    """
    try:
        print(f"🚀 Planning trip to {request.destination} for {request.days} days")
        
        initial_state = create_initial_state_from_request(request)
        result = await graph.ainvoke(initial_state)
        
        # Extract the itinerary content
        itinerary_content = ""
        if result and "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content') and last_message.content:
                itinerary_content = last_message.content
        
        if not itinerary_content:
            itinerary_content = f"Trip planned for {request.destination} ({request.days} days)"
        
        details = {
            "places_found": len(result.get('places', [])) if result.get('places') else 0,
            "route_optimized": bool(result.get('optimal_route')),
            "schedule_created": bool(result.get('daily_schedule')),
            "accommodations_suggested": bool(result.get('accommodations')),
            "total_messages": len(result.get('messages', []))
        }
        
        return TravelResponse(
            success=True,
            itinerary=itinerary_content,
            details=details
        )
        
    except Exception as e:
        print(f"❌ Error planning trip: {str(e)}")
        return TravelResponse(
            success=False,
            error=f"Failed to plan trip: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "streaming-travel-planner"}

# HTML client for testing the streaming endpoint
@app.get("/test-stream")
async def test_stream_page():
    """Simple HTML page to test the streaming functionality"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Travel Planner Stream Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; }
            .form-group { margin: 10px 0; }
            input, select, button { padding: 8px; margin: 5px; }
            .stream-output { 
                border: 1px solid #ccc; 
                padding: 20px; 
                margin-top: 20px; 
                background: #f9f9f9;
                min-height: 200px;
                font-family: monospace;
            }
            .progress { width: 100%; height: 20px; background: #ddd; margin: 10px 0; }
            .progress-bar { height: 100%; background: #4CAF50; transition: width 0.3s; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Travel Planner Stream Test</h1>
            
            <div class="form-group">
                <label>Destination:</label>
                <input type="text" id="destination" value="Goa" />
            </div>
            
            <div class="form-group">
                <label>Origin:</label>
                <input type="text" id="origin" value="Bangalore" />
            </div>
            
            <div class="form-group">
                <label>Days:</label>
                <input type="number" id="days" value="3" min="1" max="14" />
            </div>
            
            <div class="form-group">
                <label>Start Date:</label>
                <input type="date" id="start_date" />
            </div>
            
            <div class="form-group">
                <label>End Date:</label>
                <input type="date" id="end_date" />
            </div>
            
            <div class="form-group">
                <label>Theme:</label>
                <select id="theme">
                    <option value="general">General</option>
                    <option value="adventure">Adventure</option>
                    <option value="party">Party</option>
                    <option value="nature">Nature</option>
                    <option value="cultural">Cultural</option>
                </select>
            </div>
            
            <button onclick="startStreaming()">Plan My Trip!</button>
            <button onclick="clearOutput()">Clear</button>
            
            <div class="progress">
                <div class="progress-bar" id="progressBar" style="width: 0%"></div>
            </div>
            
            <div class="stream-output" id="output">Ready to plan your trip...</div>
        </div>
        
        <script>
            // Set default dates (today and 3 days from today)
            function setDefaultDates() {
                const today = new Date();
                const endDate = new Date();
                endDate.setDate(today.getDate() + 3);
                
                document.getElementById('start_date').value = today.toISOString().split('T')[0];
                document.getElementById('end_date').value = endDate.toISOString().split('T')[0];
            }
            
            // Auto-update days when dates change
            function updateDays() {
                const startDate = new Date(document.getElementById('start_date').value);
                const endDate = new Date(document.getElementById('end_date').value);
                
                if (startDate && endDate && endDate > startDate) {
                    const diffTime = Math.abs(endDate - startDate);
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    document.getElementById('days').value = diffDays;
                }
            }
            
            // Set default dates on page load
            window.onload = function() {
                setDefaultDates();
            };
            
            // Add event listeners for date changes
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('start_date').addEventListener('change', updateDays);
                document.getElementById('end_date').addEventListener('change', updateDays);
            });
            
            function startStreaming() {
                const output = document.getElementById('output');
                const progressBar = document.getElementById('progressBar');
                
                output.innerHTML = 'Starting trip planning...<br>';
                progressBar.style.width = '0%';
                
                const request = {
                    destination: document.getElementById('destination').value,
                    origin: document.getElementById('origin').value,
                    days: parseInt(document.getElementById('days').value),
                    theme: document.getElementById('theme').value,
                    start_date: document.getElementById('start_date').value,
                    end_date: document.getElementById('end_date').value
                };
                
                fetch('/plan-trip-stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(request)
                }).then(response => {
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    function readStream() {
                        reader.read().then(({ done, value }) => {
                            if (done) return;
                            
                            const chunk = decoder.decode(value);
                            const lines = chunk.split('\\n');
                            
                            lines.forEach(line => {
                                if (line.startsWith('data: ')) {
                                    try {
                                        const data = JSON.parse(line.slice(6));
                                        
                                        if (data.type === 'status' || data.type === 'update') {
                                            output.innerHTML += data.message + '<br>';
                                        } else if (data.type === 'step') {
                                            output.innerHTML += `<b>Step ${data.step}:</b> ${data.description}<br>`;
                                        } else if (data.type === 'progress') {
                                            progressBar.style.width = data.percentage + '%';
                                        } else if (data.type === 'complete') {
                                            output.innerHTML += '<br><b>🎉 Complete!</b><br><pre>' + data.itinerary + '</pre>';
                                        } else if (data.type === 'error') {
                                            output.innerHTML += '<br><b>❌ Error:</b> ' + data.message + '<br>';
                                        }
                                        
                                        output.scrollTop = output.scrollHeight;
                                    } catch (e) {
                                        console.error('Failed to parse JSON:', e);
                                    }
                                }
                            });
                            
                            readStream();
                        });
                    }
                    
                    readStream();
                }).catch(error => {
                    output.innerHTML += '<br><b>Error:</b> ' + error.message + '<br>';
                });
            }
            
            function clearOutput() {
                document.getElementById('output').innerHTML = 'Ready to plan your trip...';
                document.getElementById('progressBar').style.width = '0%';
            }
        </script>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    # To run the FastAPI server, use:
    # uvicorn main:app --reload --host 0.0.0.0 --port 8000
    print("🚀 Starting Streaming Travel Planner...")
    print("📖 Visit http://localhost:8000/docs for API documentation")
    print("🧪 Visit http://localhost:8000/test-stream for stream testing")