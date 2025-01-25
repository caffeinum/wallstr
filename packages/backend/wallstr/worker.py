import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

from wallstr.conf import settings

rabbitmq_broker = RabbitmqBroker(url=settings.RABBITMQ_URL.get_secret_value())  # type: ignore[no-untyped-call]
redis_backend = RedisBackend(url=settings.REDIS_URL.get_secret_value())
rabbitmq_broker.add_middleware(Results(backend=redis_backend, store_results=True))  # type: ignore[no-untyped-call]

dramatiq.set_broker(rabbitmq_broker)


@dramatiq.actor
def add(x: int, y: int) -> int:
    return x + y
