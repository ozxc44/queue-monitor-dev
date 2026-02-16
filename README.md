# Queue Monitor - Queue Alerting, Not Monitoring

**Status**: 🧪 Validating Demand | **Launch**: [queue-monitor.dev](https://ozxc44.github.io/queue-monitor-dev/)

---

## The Problem

You deploy at 5pm. Everything looks great.

At 11pm, your email queue starts backing up. A worker crashes, memory leaks, and the queue silently dies.

You don't know. You're asleep.

At 8am, your inbox is full of "where's my confirmation email?" messages. You spend 2 hours firefighting and looking like an amateur.

**The problem isn't that you lack monitoring.** You have Flower running. The problem is that **monitoring doesn't wake you up.**

---

## The Solution

**Queue Monitor** - A service that alerts you when something goes wrong:

- 🔔 **Queue Depth Alerts** - Know when queues back up before it's too late
- ❌ **Failed Job Tracking** - Aggregate and alert on repeated failures
- 💓 **Worker Heartbeat** - Get notified when workers go down
- ⚡ **Simple Setup** - 5 lines of code, no complex agents

At 11:15pm, you get a Slack alert: `"email_queue depth > 1000 (threshold: 500)"`. You check the dashboard, fix the issue, and go back to sleep. No users affected. No fires to fight.

---

## How We're Different

| | Flower / Horizon / Bull Board | Queue Monitor |
|---|---|---|
| Great Dashboard | ✅ | ✅ |
| Proactive Alerts | ❌ | ✅ |
| Wakes you up at 3am | ❌ | ✅ |

---

## Pricing

Starting at **$9/mo** - Less than an hour of your time is worth.

| Plan | Queues | Alerts | Price |
|------|--------|--------|-------|
| Free | 1 | Email only | $0 |
| Pro | 5 | Email + Slack | $9/mo |
| Team | Unlimited | Email + Slack + Webhook | $30/mo |

**Bundle Deal**: Get Cron Monitor + Queue Monitor for $20/mo.

---

## Supported Technologies

Launching with SDKs for:

- **Python**: RQ, Celery
- **Node.js**: BullMQ, Bull
- **Ruby**: Sidekiq
- **PHP**: Laravel Queue

---

## Get Early Access

We're launching soon. Join the waitlist for **50% off** lifetime pricing.

👉 **[queue-monitor.dev](https://ozxc44.github.io/queue-monitor-dev/)**

---

## Validation Status

Before building the full MVP, we're validating demand:

- **Goal**: 50+ email signups to proceed with development
- **Current**: [![Waitlist](https://img.shields.io/badge/waitlist-0%20%2F%2050-red)](https://ozxc44.github.io/queue-monitor-dev/)

### Help us validate!

1. Is queue alerting a problem you actually have?
2. Would you pay $9/mo for peace of mind?
3. What's your current setup for queue alerts?

**Join the waitlist and let us know!**

---

## Why Not Just Use APM?

AppSignal ($23/mo) and DataDog ($15+/host) include queue monitoring. But:

1. They're overkill if you just want queue alerts
2. Small teams don't want another complex tool
3. $9/mo is easier to justify than $23+

---

## Roadmap

### If validation succeeds (>50 signups):

**Week 1-2**: Build MVP (Python RQ only)
**Week 3**: Beta testing with waitlist
**Week 4**: Public launch

### If validation fails:

- Analyze feedback
- Consider pivot to "Developer Alerting Platform"
- Or return to candidate list

---

## License

MIT - Self-hosted version will be open source.

---

**Queue Monitor** - Because monitoring dashboards don't send 3am texts.
