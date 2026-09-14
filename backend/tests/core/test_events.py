"""
Контрактные тесты EventBus (app.core.events.bus).

core — инфраструктурный модуль без продуктовых PUBLISHES/SUBSCRIBES_TO.
Контракт здесь — гарантии поведения самой шины, заявленные в specs/core.md §5.

AC#7: два обработчика, один бросает исключение → второй всё равно выполняется,
      publish() не выбрасывает исключение наружу.
"""
import pytest

from app.core.events.bus import EventBus


class TestEventBusIsolation:
    """AC#7 — изоляция ошибок обработчиков."""

    async def test_second_handler_runs_when_first_raises(self):
        bus = EventBus()
        executed = []

        async def failing_handler(payload: dict) -> None:
            raise RuntimeError("намеренная ошибка первого обработчика")

        async def succeeding_handler(payload: dict) -> None:
            executed.append(payload)

        bus.subscribe("test.event", failing_handler)
        bus.subscribe("test.event", succeeding_handler)

        await bus.publish("test.event", {"key": "value"})

        assert executed == [{"key": "value"}]

    async def test_publish_does_not_raise_when_handler_raises(self):
        bus = EventBus()

        async def failing_handler(payload: dict) -> None:
            raise RuntimeError("намеренная ошибка")

        bus.subscribe("test.event", failing_handler)

        # publish() не должен выбрасывать исключение наружу
        await bus.publish("test.event", {"key": "value"})

    async def test_error_in_first_handler_does_not_skip_remaining(self):
        """Все последующие обработчики вызываются, несмотря на ошибку в предыдущем."""
        bus = EventBus()
        executed = []

        async def handler_a(payload: dict) -> None:
            raise ValueError("ошибка в A")

        async def handler_b(payload: dict) -> None:
            executed.append("B")

        async def handler_c(payload: dict) -> None:
            executed.append("C")

        bus.subscribe("test.event", handler_a)
        bus.subscribe("test.event", handler_b)
        bus.subscribe("test.event", handler_c)

        await bus.publish("test.event", {})

        assert executed == ["B", "C"]


class TestEventBusOrder:
    """Порядок вызова обработчиков — порядок регистрации (specs/core.md §5)."""

    async def test_handlers_called_in_registration_order(self):
        bus = EventBus()
        order = []

        async def first(payload: dict) -> None:
            order.append("first")

        async def second(payload: dict) -> None:
            order.append("second")

        async def third(payload: dict) -> None:
            order.append("third")

        bus.subscribe("test.event", first)
        bus.subscribe("test.event", second)
        bus.subscribe("test.event", third)

        await bus.publish("test.event", {})

        assert order == ["first", "second", "third"]


class TestEventBusSynchronous:
    """publish() дожидается завершения всех обработчиков до возврата (specs/core.md §5)."""

    async def test_publish_awaits_all_handlers_before_returning(self):
        bus = EventBus()
        completed = []

        async def async_handler(payload: dict) -> None:
            # имитируем async-работу без реального sleep
            completed.append("done")

        bus.subscribe("test.event", async_handler)
        await bus.publish("test.event", {})

        assert completed == ["done"]

    async def test_no_handlers_publish_completes_without_error(self):
        bus = EventBus()
        await bus.publish("event.without.subscribers", {"data": 1})


class TestEventBusPayload:
    """Payload передаётся в обработчики без изменений."""

    async def test_payload_passed_to_handler_unchanged(self):
        bus = EventBus()
        received = []

        async def handler(payload: dict) -> None:
            received.append(payload)

        bus.subscribe("test.event", handler)
        payload = {"user_id": "abc", "score": 42, "nested": {"x": 1}}
        await bus.publish("test.event", payload)

        assert received == [payload]
