"""
Queue Monitor - RQ Integration Example

This example shows how to integrate Queue Monitor with Python RQ
to get alerted when queues back up, jobs fail, or workers go down.

Installation:
    pip install rq redis

Usage:
    # In a separate terminal, start a worker:
    python worker.py

    # Then enqueue jobs:
    python enqueue.py

    # Queue Monitor will alert you when:
    # - Queue depth exceeds threshold
    # - Jobs fail repeatedly
    # - Workers stop heartbeating
"""

import os
import redis
from rq import Queue
from rq.worker import Worker
import requests
import json
from datetime import datetime, timedelta
from typing import Optional


class QueueMonitor:
    """
    Monitor RQ queues and send alerts when thresholds are exceeded.

    This is a reference implementation. Queue Monitor will provide
    a hosted service with Slack, email, and webhook notifications.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        alert_webhook: Optional[str] = None,
        queue_depth_threshold: int = 1000,
        check_interval: int = 60,
    ):
        self.redis = redis.from_url(redis_url)
        self.alert_webhook = alert_webhook or os.getenv("QUEUE_MONITOR_WEBHOOK")
        self.queue_depth_threshold = queue_depth_threshold
        self.check_interval = check_interval
        self.last_alert = {}  # Track last alert time per queue

    def check_queue_depth(self, queue_name: str) -> dict:
        """Check if queue depth exceeds threshold."""
        key = f"rq:queue:{queue_name}"
        length = self.redis.llen(key)

        status = {
            "queue": queue_name,
            "depth": length,
            "threshold": self.queue_depth_threshold,
            "status": "ok" if length < self.queue_depth_threshold else "alert",
            "timestamp": datetime.utcnow().isoformat(),
        }

        if status["status"] == "alert":
            # Check if we already alerted recently (avoid spam)
            last_alert_time = self.last_alert.get(f"{queue_name}:depth")
            if not last_alert_time or datetime.utcnow() - last_alert_time > timedelta(minutes=15):
                self.send_alert(status)
                self.last_alert[f"{queue_name}:depth"] = datetime.utcnow()

        return status

    def check_failed_jobs(self, queue_name: str) -> dict:
        """Check for failed jobs."""
        failed_key = f"rq:queue:{queue_name}:failed"
        failed_count = self.redis.scard(failed_key)

        status = {
            "queue": queue_name,
            "failed_count": failed_count,
            "status": "ok" if failed_count == 0 else "warning",
            "timestamp": datetime.utcnow().isoformat(),
        }

        if failed_count > 0:
            last_alert_time = self.last_alert.get(f"{queue_name}:failed")
            if not last_alert_time or datetime.utcnow() - last_alert_time > timedelta(minutes=30):
                self.send_alert(status)
                self.last_alert[f"{queue_name}:failed"] = datetime.utcnow()

        return status

    def check_workers(self, queue_name: str) -> dict:
        """Check if workers are alive."""
        workers = Worker.all(queue=Queue(queue_name, connection=self.redis), connection=self.redis)
        alive_workers = [w for w in workers if w.state != "stopped"]

        status = {
            "queue": queue_name,
            "workers": len(alive_workers),
            "status": "ok" if len(alive_workers) > 0 else "critical",
            "timestamp": datetime.utcnow().isoformat(),
        }

        if status["status"] == "critical":
            last_alert_time = self.last_alert.get(f"{queue_name}:workers")
            if not last_alert_time or datetime.utcnow() - last_alert_time > timedelta(minutes=5):
                self.send_alert(status)
                self.last_alert[f"{queue_name}:workers"] = datetime.utcnow()

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
        elif "failed_count" in status:
            return f"⚠️ Queue '{status['queue']}' has {status['failed_count']} failed jobs"
        elif "workers" in status:
            return f"🔴 Queue '{status['queue']}' has no active workers!"
        return str(status)

    def monitor(self, queue_names: list[str]) -> None:
        """Continuously monitor queues."""
        print(f"Monitoring queues: {', '.join(queue_names)}")
        print(f"Depth threshold: {self.queue_depth_threshold}")
        print(f"Check interval: {self.check_interval}s")
        print("-" * 50)

        while True:
            import time

            for queue_name in queue_names:
                self.check_queue_depth(queue_name)
                self.check_failed_jobs(queue_name)
                self.check_workers(queue_name)

            time.sleep(self.check_interval)


# Example usage
if __name__ == "__main__":
    import sys

    # Get queue names from command line or use default
    queues = sys.argv[1:] if len(sys.argv) > 1 else ["default", "high", "low"]

    monitor = QueueMonitor(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        queue_depth_threshold=500,
        check_interval=60,
    )

    try:
        monitor.monitor(queues)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
