# System Design Architecture Workflow

Follow this step-by-step workflow when architecting scalable backend systems.

---

## Step 1: Requirements Clarification
1. Identify User Stories and core functional requirements.
2. Define scale targets:
   - Daily Active Users (DAU) & Peak Requests Per Second (RPS)
   - Read to Write ratio
   - Data storage growth rate (GB/TB per month)
   - Target Latency (p95 / p99 under 100ms)
   - Target Availability (99.9% vs 99.99%)

## Step 2: High-Level Architecture Diagram
1. Define the entry point: DNS -> CDN / Edge -> Load Balancer (ALB/Envoy).
2. Define the service layer: Modular monolith or microservices cluster.
3. Define persistence: Primary relational database (Postgres) + Read Replicas.
4. Define caching: Redis cluster for session store and hot data cache.

## Step 3: Data Modeling & Partitioning Strategy
1. Establish relational entity schemas and foreign keys.
2. If data volume exceeds single-node capacity (>5TB or >50k writes/sec), design sharding key strategy (hash-based or range-based).

## Step 4: Asynchronous Processing & Decoupling
1. Identify slow operations (video transcoding, notifications, payments).
2. Wire message broker (RabbitMQ/SQS/Kafka) and worker services.

## Step 5: Failure Mode & Trade-Off Review
1. Review single points of failure (SPOF) across every layer.
2. Define rate limiting, circuit breakers, and database backup / disaster recovery plans.
