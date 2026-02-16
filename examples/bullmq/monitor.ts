/*
 * Queue Monitor - BullMQ Integration Example
 *
 * This example shows how to integrate Queue Monitor with BullMQ
 * to get alerted when queues back up, jobs fail, or workers go down.
 *
 * Installation:
 *   npm install bullmq ioredis
 *
 * Usage:
 *   # Run monitor
 *   ts-node monitor.ts
 *
 *   # Queue Monitor will alert you when:
 *   # - Queue depth exceeds threshold
 *   # - Jobs fail repeatedly
 *   # - Workers stop processing
 */

import { Queue, Worker, Job } from 'bullmq';
import Redis from 'ioredis';

interface AlertStatus {
  queue: string;
  status: 'ok' | 'warning' | 'critical';
  timestamp: string;
  [key: string]: any;
}

interface MonitorConfig {
  redisUrl?: string;
  alertWebhook?: string;
  queueDepthThreshold?: number;
  checkInterval?: number;
}

class BullMQMonitor {
  private connection: Redis;
  private alertWebhook: string | undefined;
  private queueDepthThreshold: number;
  private checkInterval: number;
  private lastAlerts: Map<string, Date> = new Map();
  private queues: Map<string, Queue> = new Map();

  constructor(config: MonitorConfig = {}) {
    this.connection = new Redis(config.redisUrl || 'localhost:6379');
    this.alertWebhook = config.alertWebhook || process.env.QUEUE_MONITOR_WEBHOOK;
    this.queueDepthThreshold = config.queueDepthThreshold || 1000;
    this.checkInterval = config.checkInterval || 60000;
  }

  async getQueue(queueName: string): Promise<Queue> {
    if (!this.queues.has(queueName)) {
      this.queues.set(queueName, new Queue(queueName, { connection: this.connection }));
    }
    return this.queues.get(queueName)!;
  }

  async checkQueueDepth(queueName: string): Promise<AlertStatus> {
    const queue = await this.getQueue(queueName);
    const waiting = await queue.getWaitingCount();
    const active = await queue.getActiveCount();
    const delayed = await queue.getDelayedCount();
    const failed = await queue.getFailedCount();

    const totalDepth = waiting + active + delayed;

    const status: AlertStatus = {
      queue: queueName,
      depth: totalDepth,
      waiting,
      active,
      delayed,
      failed,
      threshold: this.queueDepthThreshold,
      status: totalDepth > this.queueDepthThreshold ? 'alert' : 'ok',
      timestamp: new Date().toISOString(),
    };

    if (status.status === 'alert') {
      const lastAlert = this.lastAlerts.get(`${queueName}:depth`);
      if (!lastAlert || Date.now() - lastAlert.getTime() > 15 * 60 * 1000) {
        await this.sendAlert(status);
        this.lastAlerts.set(`${queueName}:depth`, new Date());
      }
    }

    return status;
  }

  async checkFailedJobs(queueName: string): Promise<AlertStatus> {
    const queue = await this.getQueue(queueName);
    const failed = await queue.getFailedCount();

    const status: AlertStatus = {
      queue: queueName,
      failedCount: failed,
      status: failed > 0 ? 'warning' : 'ok',
      timestamp: new Date().toISOString(),
    };

    if (failed > 0) {
      const lastAlert = this.lastAlerts.get(`${queueName}:failed`);
      if (!lastAlert || Date.now() - lastAlert.getTime() > 30 * 60 * 1000) {
        await this.sendAlert(status);
        this.lastAlerts.set(`${queueName}:failed`, new Date());
      }
    }

    return status;
  }

  async checkWorkers(queueName: string): Promise<AlertStatus> {
    const queue = await this.getQueue(queueName);
    const workers = await queue.getWorkers();

    const status: AlertStatus = {
      queue: queueName,
      workers: workers.length,
      status: workers.length > 0 ? 'ok' : 'critical',
      timestamp: new Date().toISOString(),
    };

    if (status.status === 'critical') {
      const lastAlert = this.lastAlerts.get(`${queueName}:workers`);
      if (!lastAlert || Date.now() - lastAlert.getTime() > 5 * 60 * 1000) {
        await this.sendAlert(status);
        this.lastAlerts.set(`${queueName}:workers`, new Date());
      }
    }

    return status;
  }

  async sendAlert(status: AlertStatus): Promise<void> {
    const message = this.formatAlert(status);
    console.log(`[ALERT] ${message}`);

    if (this.alertWebhook) {
      try {
        await fetch(this.alertWebhook, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: message }),
        });
      } catch (error) {
        console.error(`[ERROR] Failed to send alert:`, error);
      }
    }
  }

  formatAlert(status: AlertStatus): string {
    if ('depth' in status) {
      return `🚨 Queue '${status.queue}' depth: ${status.depth} (threshold: ${status.threshold})`;
    }
    if ('failedCount' in status) {
      return `⚠️ Queue '${status.queue}' has ${status.failedCount} failed jobs`;
    }
    if ('workers' in status) {
      return `🔴 Queue '${status.queue}' has no active workers!`;
    }
    return JSON.stringify(status);
  }

  async monitor(queueNames: string[]): Promise<never> {
    console.log(`Monitoring BullMQ queues: ${queueNames.join(', ')}`);
    console.log(`Depth threshold: ${this.queueDepthThreshold}`);
    console.log(`Check interval: ${this.checkInterval}ms`);
    console.log('-'.repeat(50));

    while (true) {
      for (const queueName of queueNames) {
        await this.checkQueueDepth(queueName);
        await this.checkFailedJobs(queueName);
        await this.checkWorkers(queueName);
      }

      await new Promise(resolve => setTimeout(resolve, this.checkInterval));
    }
  }

  async close(): Promise<void> {
    for (const queue of this.queues.values()) {
      await queue.close();
    }
    this.connection.quit();
  }
}

// Example usage
async function main() {
  const queueNames = process.argv.slice(2);
  const queuesToMonitor = queueNames.length > 0 ? queueNames : ['default', 'high', 'low'];

  const monitor = new BullMQMonitor({
    redisUrl: process.env.REDIS_URL || 'localhost:6379',
    queueDepthThreshold: 500,
    checkInterval: 60000,
  });

  try {
    await monitor.monitor(queuesToMonitor);
  } catch (error) {
    console.error('Monitor error:', error);
    await monitor.close();
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export { BullMQMonitor, AlertStatus, MonitorConfig };
