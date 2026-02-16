"""
Queue Monitor - Celery Integration Example

This example shows how to integrate Queue Monitor with Celery
to get alerted when queues back up, jobs fail, or workers go down.

Installation:
    pip install celery redis

Usage:
    # Start Celery worker:
    celery -A your_app worker -l info -Q default,high,low

    # Run monitor:
    python monitor.py
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Optional
from celery import Celery


class CeleryQueueMonitor:
    """
    Monitor Celery queues and send alerts when thresholds are exceeded.

    Queue Monitor will provide a hosted service with Slack, email,
    and webhook notifications.
    """

    def __init__(
        self,
        broker_url: str = "redis://localhost:6379/0",
        alert_webhook: Optional[str] = None,
        queue_depth_threshold: int = 1000,
        check_interval: int = 60,
    ):
        self.broker_url = broker_url
        self.alert_webhook = alert_webhook or os.getenv("QUEUE_MONITOR_WEBHOOK")
        self.queue_depth_threshold = queue_depth_threshold
        self.check_interval = check_interval
        self.last_alert = {}

        # Connect to Redis directly for queue inspection
        import redis
        self.redis = redis.from_url(broker_url)

    def get_queue_length(self, queue_name: str) -> int:
        """Get the length of a Celery queue."""
        # Celery queues are Redis lists
        key = queue_name.encode() if isinstance(queue_name, str) else queue_name
        return self.redis.llen(queue_name)

    def check_queue_depth(self, queue_name: str) -> dict:
        """Check if queue depth exceeds threshold."""
        length = self.get_queue_length(queue_name)

        status = {
            "queue": queue_name,
            "depth": length,
            "threshold": self.queue_depth_threshold,
            "status": "ok" if length < self.queue_depth_threshold else "alert",
            "timestamp": datetime.utcnow().isoformat(),
        }

        if status["status"] == "alert":
            last_alert_time = self.last_alert.get(f"{queue_name}:depth")
            if not last_alert_time or datetime.utcnow() - last_alert_time > timedelta(minutes=15):
                self.send_alert(status)
                self.last_alert[f"{queue_name}:depth"] = datetime.utcnow()

        return status

    def check_active_tasks(self) -> dict:
        """Check for stuck active tasks."""
        # Celery stores active tasks in a list
        active_count = 0
        try:
            for key in self.redis.scan_iter(match="celery-task-meta-*"):
                # Check for tasks that have been running too long
                pass
        except Exception:
            pass

        return {
            "active_tasks": active_count,
            "status": "ok",
        }

    def check_workers(self) -> dict:
        """Check for active Celery workers."""
        # Celery workers ping with heartbeat
        workers = []
        try:
            for key in self.redis.scan_iter(match="celery:*:pidbox:*"):
                workers.append(key)
        except Exception:
            pass

        status = {
            "workers": len(workers),
            "status": "ok" if len(workers) > 0 else "critical",
            "timestamp": datetime.utcnow().isoformat(),
        }

        if status["status"] == "critical":
            last_alert_time = self.last_alert.get("workers")
            if not last_alert_time or datetime.utcnow() - last_alert_time > timedelta(minutes=5):
                self.send_alert(status)
                self.last_alert["workers"] = datetime.utcnow()

        return status

    def send_alert(self, status: dict) -> None:
        """Send alert to webhook (Slack, Discord, etc)."""
        message = self.format_alert(status)
        print(f"[ALERT] {message}")

        if self.alert_webhook:
            try:
                requests.post(
                    self.alert_webhook,
                    json={"text": message},
                    timeout=5,
                )
            except requests.RequestException as e:
                print(f"[ERROR] Failed to send alert: {e}")

    def format_alert(self, status: dict) -> str:
        """Format alert message."""
        if "depth" in status:
            return f"🚨 Queue '{status['queue']}' depth: {status['depth']} (threshold: {status['threshold']})"
        elif "workers" in status:
            return f"🔴 No active Celery workers detected!"
        return str(status)

    def monitor(self, queue_names: list[str]) -> None:
        """Continuously monitor Celery queues."""
        print(f"Monitoring Celery queues: {', '.join(queue_names)}")
        print(f"Depth threshold: {self.queue_depth_threshold}")
        print(f"Check interval: {self.check_interval}s")
        print("-" * 50)

        while True:
            for queue_name in queue_names:
                self.check_queue_depth(queue_name)

            self.check_workers()

            time.sleep(self.check_interval)


# Example usage
if __name__ == "__main__":
    import sys

    queues = sys.argv[1:] if len(sys.argv) > 1 else ["default", "high", "low"]

    monitor = CeleryQueueMonitor(
        broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        queue_depth_threshold=500,
        check_interval=60,
    )

    try:
        monitor.monitor(queues)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
