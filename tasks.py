from your_module import app
from celery import Celery

celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['app.py']
)

if __name__ == "__main__":
    celery.start()
