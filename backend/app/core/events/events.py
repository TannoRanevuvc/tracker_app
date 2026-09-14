# core — инфраструктурный модуль; не публикует и не подписывается на продуктовые события.
# EventBus и реестр модулей — его контракт, описанный в specs/core.md §5–6.

PUBLISHES: list[str] = []
SUBSCRIBES_TO: dict[str, object] = {}
