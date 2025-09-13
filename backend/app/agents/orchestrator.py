# orchestrator.py
import asyncio
from app.models.plan_trip_llm_request import PlanTripLLMRequest
from app.services.ai_agents import AiAgentService


class TripOrchestrator:
    def __init__(self):
        # Create one shared agent service instance
        self.agent_service = AiAgentService()

    async def plan_trip(self, request: PlanTripLLMRequest):
        print("Entered TripOrchestrator.plan_trip with request", request)
        trip_dict = request.trip.dict(by_alias=True)
        print("Trip Dict after validating:", trip_dict)

        # Delegate to AI agent service
        result = await self.agent_service.plan_trip_agents(trip_dict)

        print("Final Itenerary:", result)
        return result
