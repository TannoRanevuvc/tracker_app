import logging
from collections import defaultdict
from typing import Callable

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable) -> None:
        self._subscribers[event_name].append(handler)

    async def publish(self, event_name: str, payload: dict) -> None:
        for handler in self._subscribers[event_name]:
            try:
                await handler(payload)
            except Exception:
                logger.exception(
                    "EventBus handler %s failed for event %s", handler, event_name
                )


bus = EventBus()
