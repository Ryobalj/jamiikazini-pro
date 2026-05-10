# jamiitasks/tasks/test_tasks.py
from jamiikazini.celery import app

@app.task(bind=True)
def fail_test_task(self):
    raise Exception("Simulated failure for DLQ test")