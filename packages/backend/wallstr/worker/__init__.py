import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import (
    AgeLimit,
    Callbacks,
    CurrentMessage,
    ShutdownNotifications,
    TimeLimit,
)
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

from wallstr.conf import settings

from .middlewares import AsyncSessionMiddleware

rabbitmq_broker = RabbitmqBroker(
    url=settings.RABBITMQ_URL.get_secret_value(),
    middleware=[
        AgeLimit(),  # type: ignore[no-untyped-call]
        TimeLimit(),  # type: ignore[no-untyped-call]
        ShutdownNotifications(),  # type: ignore[no-untyped-call]
        Callbacks(),
        AsyncSessionMiddleware(),
        CurrentMessage(),
    ],
)  # type: ignore[no-untyped-call]
redis_backend = RedisBackend(url=settings.REDIS_URL.get_secret_value())

# middlewares
rabbitmq_broker.add_middleware(Results(backend=redis_backend, store_results=True))  # type: ignore[no-untyped-call]

dramatiq.set_broker(rabbitmq_broker)

__all__ = ["dramatiq"]
