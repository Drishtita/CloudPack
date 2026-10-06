from typing import Any


class MemoryStore:
    """
    Stores active trip information for the Smart Packing Agent.

    This first version stores data in the service's memory.
    Redis can be added later as the persistent backend.
    """

    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}

    def start_trip(
        self,
        session_id: str,
        destination: str,
        days: int,
        trip_type: str
    ) -> dict:

        existing = self.sessions.get(session_id)

        # If the same destination already exists,
        # update the trip without deleting existing items.
        if (
            existing is not None
            and existing["destination"].lower() == destination.lower()
        ):
            existing["days"] = days
            existing["trip_type"] = trip_type

            return {
                "message": "Existing trip updated",
                "trip": existing
            }

        # Otherwise create a new trip.
        trip = {
            "destination": destination,
            "days": days,
            "trip_type": trip_type,
            "weather": None,
            "items": []
        }

        self.sessions[session_id] = trip

        return {
            "message": "New trip started",
            "trip": trip
        }

    def store_weather(
        self,
        session_id: str,
        weather: dict
    ) -> dict:

        if session_id not in self.sessions:
            raise ValueError("No active trip for this session")

        self.sessions[session_id]["weather"] = weather

        return {
            "message": "Weather stored",
            "weather": weather
        }

    def add_item(
        self,
        session_id: str,
        item: str,
        reason: str = ""
    ) -> dict:

        if session_id not in self.sessions:
            raise ValueError("No active trip for this session")

        entry = {
            "item": item,
            "reason": reason
        }

        self.sessions[session_id]["items"].append(entry)

        return {
            "message": f"Added '{item}' to packing list",
            "item": entry
        }

    def get_trip(self, session_id: str) -> dict | None:
        return self.sessions.get(session_id)

    def end_trip(self, session_id: str) -> dict:

        if session_id not in self.sessions:
            raise ValueError("No active trip for this session")

        trip = self.sessions.pop(session_id)

        return {
            "message": "Trip ended",
            "trip": trip
        }

    def clear(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


# One memory store for this service process
memory_store = MemoryStore()