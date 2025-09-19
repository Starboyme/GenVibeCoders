# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
import asyncio

# from backend.types.decision_request import DecisionRequest
from nodes.routes import run

# app = FastAPI()

# async def stream_langgraph_response(request: DecisionRequest):
#     graph = get_graph()
#     async for event in graph.stream(request):
#         kind = event["event"]
#         if kind == "on_chat_model_stream":
#             chunk = event["data"]["chunk"]
#             if chunk.content:
#                 yield chunk.content

# @app.post("/")
# async def stream_response(request: DecisionRequest):
#     return StreamingResponse(stream_response())

if __name__ == "__main__":
    asyncio.run(run())