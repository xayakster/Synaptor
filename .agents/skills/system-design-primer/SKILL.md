---
name: system-design-primer
description: System design, scalability, and distributed systems architecture guide (horizontal scaling, load balancing, caching tiers, SQL vs NoSQL, database sharding, message queues, CAP theorem, and resilience patterns).
---

# System Design & Scalability Architecture Guide

This guide establishes principles and patterns from the **System Design Primer** for architecting reliable, scalable, and high-performance production systems.

---

## 1. System Design Reasoning Framework

When designing any system architecture, evaluate the problem in a structured sequence:

```text
1. Scope & Requirements
   ├── Functional Requirements (What features must the system deliver?)
   └── Non-Functional Requirements (Scale, Latency, Availability, Consistency)
2. Capacity & Scale Estimation
   ├── Traffic (QPS/RPS, Read/Write Ratio, Peak Multiplier)
   ├── Storage (Daily volume, 5-year retention, Media vs Text)
   └── Bandwidth (Ingress and Egress bandwidth requirements)
3. High-Level Architecture
   ├── Client -> CDN / DNS -> Load Balancer -> Application Cluster -> Cache -> Database
4. Deep Dive & Bottleneck Resolution
   ├── Caching Strategy (Redis, Cache-aside, Invalidation)
   ├── Database Scaling (Read Replicas, Partitioning/Sharding, Indexes)
   └── Asynchronous Processing (Message Queues, Background Workers)
5. Trade-off Analysis & Failure Modes
   ├── CAP Theorem Trade-offs (CP vs AP)
   └── Redundancy, Failover, Circuit Breakers, Rate Limiting
```

---

## 2. Core Scalability & Performance Patterns

### 1. Scaling Up vs. Scaling Out
- **Vertical Scaling (Scaling Up)**: Increasing CPU/RAM on a single machine. Limited by hardware caps and single point of failure (SPOF).
- **Horizontal Scaling (Scaling Out)**: Adding stateless application instances behind a load balancer. Preferred for high availability and elastic cloud workloads.

### 2. Load Balancing (L4 vs. L7)
- **Layer 4 (Transport / TCP)**: Fast, routes based on IP and port without inspecting HTTP payload (e.g., AWS NLB).
- **Layer 7 (Application / HTTP)**: Intelligent, routes based on HTTP headers, cookies, URL paths, SSL termination (e.g., NGINX, Envoy, AWS ALB).
- **Algorithms**: Round-robin, Least Connections, IP Hash (sticky sessions), Weighted.

### 3. Caching Strategies (Redis / Memcached)
- **Cache-Aside (Lazy Loading)**: Application queries cache; on miss, queries DB and populates cache. (Best for read-heavy workloads with tolerable staleness).
- **Write-Through**: Application writes to cache and DB simultaneously. (Guarantees fresh data, slight write latency).
- **Write-Back (Write-Behind)**: Writes to cache immediately; cache asynchronously writes to DB in batches. (Extremely fast writes, risk of data loss on cache crash).
- **Eviction Policies**: LRU (Least Recently Used), LFU (Least Frequently Used), TTL expiry.

### 4. Database Selection: SQL vs. NoSQL
| Dimension | Relational (SQL - Postgres, MySQL) | Document / Key-Value (NoSQL - MongoDB, DynamoDB, Redis) |
|---|---|---|
| **Data Schema** | Structured, normalized, relational ACID | Flexible, schema-less, nested JSON |
| **Scaling** | Vertical + Read Replicas + Sharding | Horizontal partitioning built-in |
| **Transactions** | Complex multi-table ACID transactions | Eventual consistency / Single-item ACID |
| **Best For** | Financial, CRM, E-commerce orders, relational graphs | High-throughput telemetry, sessions, chat, catalogs |

### 5. Asynchronous Decoupling (Message Queues & Event Streams)
- **Message Queues (RabbitMQ, AWS SQS)**: Point-to-point task queues, worker pools, retries, dead-letter queues (DLQs).
- **Event Streaming (Apache Kafka, AWS Kinesis)**: Distributed, ordered commit log for event-driven microservices and high-throughput real-time stream processing.

### 6. CAP Theorem & Consistency Models
- In the presence of a **Network Partition (P)**, a distributed system must choose between:
  - **Consistency (C)**: Every read receives the most recent write or an error (CP systems, e.g., HBase, Spanner, Zookeeper).
  - **Availability (A)**: Every request receives a non-error response without guarantee of latest data (AP systems, e.g., Cassandra, DynamoDB, CouchDB).

---

## 3. Resilience & Anti-Fragility Checklist

- [ ] **No Single Point of Failure (SPOF)**: Every tier (LB, App, Cache, DB) has redundancy/failover.
- [ ] **Rate Limiting**: Protect endpoints from traffic spikes and DoS (Token bucket, Leaky bucket).
- [ ] **Circuit Breakers**: Prevent cascading failures across downstream microservices (e.g., Resilience4j, Polly).
- [ ] **Graceful Degradation**: Fall back to cached or default responses when external services degrade.
- [ ] **Observability**: Metrics (Prometheus/Grafana), Centralized Logging (ELK/OpenSearch), Distributed Tracing (OpenTelemetry/Jaeger).
