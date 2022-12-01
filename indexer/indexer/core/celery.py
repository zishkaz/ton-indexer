import os
from celery import Celery
from indexer.core.settings import Settings


settings = Settings()

app = Celery('indexer',
             broker=settings.amqp_dsn,
             backend=settings.redis_dsn,
             include=['indexer.core.tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    accept_content=['pickle', 'json'],
    task_serializer='pickle',
    result_serializer='pickle',
    event_serializer='pickle',
    result_expires=3600,
    result_extended=True,
    worker_send_task_events=True,
    task_default_priority=5,
    task_queue_max_priority=10,
    worker_max_tasks_per_child=settings.max_tasks_per_child, # recreate worker process after every max_tasks_per_child tasks
    task_time_limit=settings.task_time_limit,
    task_reject_on_worker_lost=True
)