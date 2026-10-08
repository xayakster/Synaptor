# System Design & Scalability Principles

## 1. Simplicity First Principle
- Never start with complex microservices or multi-region distributed databases for an unproven MVP or low-traffic application.
- Start with a clean, modular monolith with a robust relational database (e.g., PostgreSQL), adding caching (Redis) and queues (RabbitMQ/SQS) as measurable bottlenecks appear.

## 2. Eliminate Single Points of Failure (SPOFs)
- Deploy application instances across multiple availability zones behind a load balancer.
- Configure primary-replica database topologies with automated failover.

## 3. Stateless Application Tier
- Keep web application servers stateless. Store sessions in Redis or encrypted JWT tokens.
- This allows horizontal autoscaling (Scale-Out) without session loss.

## 4. Cache Deliberately
- Apply cache-aside patterns to read-heavy, low-mutability queries.
- Always attach TTLs (Time-To-Live) and define explicit cache invalidation strategies on mutation.

## 5. Asynchronous Offloading
- Long-running operations (email sending, image processing, report generation, webhook dispatch) must never block the HTTP request-response cycle. Offload them to background worker queues.
