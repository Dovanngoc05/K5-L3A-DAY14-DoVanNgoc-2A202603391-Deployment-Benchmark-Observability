# Benchmark & Observability Report — Day 14

**Run date:** 2026-11-26  
**Environment:** Windows with Docker Desktop, WSL2, local Docker Compose stack. Exact CPU/RAM allocation was not recorded.  
**Agent:** Mock LLM; agent v2 unless otherwise stated.

## 1. SLOs

| SLI | SLO | Result |
|---|---:|---|
| `/ask` p95 latency | ≤ 500 ms | Met at concurrency 1, 10, and 50; missed at 100. |
| Request error rate | ≤ 2% | Met in all four develop load runs. |
| Golden dataset accuracy | ≥ 100% for final v2 | Met: 23/23. |

## 2. Develop load test — v2

Source reports: `reports/load_v2_c*.json` (copied from the develop run directory for submission).

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Errors | SLO |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 4.43 | 189.1 | 219.2 | 1680.1 | 1.00% | Pass |
| 10 | 35.52 | 189.9 | 219.0 | 1701.6 | 1.00% | Pass |
| 50 | 87.12 | 209.2 | 311.0 | 1726.3 | 0.00% | Pass |
| 100 | 59.99 | 331.9 | 1567.4 | 2688.0 | 0.50% | Fail: p95 |

Throughput rose through concurrency 50, then fell at 100 while p95 rose above the 500 ms objective. This indicates that the test machine or agent became saturated at the highest load. The large p99 values at lower concurrency are consistent with the mock's injected slow requests; average latency alone would hide those tails.

## 3. Quality evaluation

Source reports: `reports/eval_v1.json`, `eval_v2.json`, and `eval_v2_fixed.json`.

| Version | Accuracy | p95 (ms) | Avg tokens/question | Total cost | Gate |
|---|---:|---:|---:|---:|---|
| v1 baseline | 4.3% (1/23) | 190.0 | 57.7 | $0.000412 | Fail |
| v2 initial | 91.3% (21/23) | 214.5 | 109.1 | $0.000762 | Pass at 80%; +20 improved, 0 regression |
| v2 after knowledge base fix | 100% (23/23) | 214.9 | 115.5 | $0.000806 | Pass at 100%; +22 improved, 0 regression |

The two initial misses concerned JWT versus API key and Kubernetes HPA. Adding targeted knowledge base entries raised v2 to 23/23. Quality improved substantially with higher token use, cost, and modestly higher p95 latency.

## 4. Observability findings

- Grafana showed active traffic and populated latency, request, error, in-flight, instance, and cost panels.
- Prometheus target health showed both agent instances and Prometheus itself `UP` (2/2 agents).
- `AgentHighErrorRate` fired during the 20% error injection and returned inactive after restoring the normal error rate.
- `AgentHighLatencyP95` fired during the 30% slow-request injection.
- `LLMCostBurnRateHigh` fired while `mock-llm-large` was serving Locust traffic; the alert screenshot was shared in the conversation.
- `AgentInstanceDown` fired after one agent was paused; Prometheus showed `up{job="agent"} == 0`, the 30 s pending period, and an active-since value of about 39.7 s in the screenshot.
- Slow trace: total duration 1.7 s; retrieval span 21.5 ms; nearly all remaining time was in `chat mock-llm-small`.
- Error trace: total duration 89.5 ms; `chat mock-llm-small` span 68.6 ms; attribute `error.type=upstream_unavailable`; exception reported mock upstream HTTP 503.
- Trace screenshots: `screenshots/jaeger-slow-trace.png`, `screenshots/jaeger-error-trace-detail.png`.
- Exact alert firing times and full trace IDs were not recorded.

## 5. Production scaling load test

These are from the submitted Locust CSVs `benchmark-results/scale_1_stats.csv` and `benchmark-results/scale_3_stats.csv` (clean runs). Both had zero failed requests. Values below use the aggregated row; `/ask` p95 is listed separately because it is the main workload.

| Agent instances | Requests | Aggregate RPS | Aggregate p95 (ms) | `/ask` p95 (ms) | Aggregate p99 (ms) | Failures |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7902 | 66.16 | 220 | 230 | 1700 | 0 |
| 3 | 7917 | 66.29 | 220 | 220 | 1700 | 0 |

Scaling from one to three instances did not materially improve total throughput on this test setup. The Locust generator, Nginx, host CPU limits, or the mock workload may be the bottleneck; the measured results do not identify which one. The earlier non-clean run had many 502s during replica changes and about 1% injected 503s, so it was excluded from this comparison.

## 6. Evidence and remaining work

- [x] Load-test JSON reports for v2 at concurrency 1, 10, 50, and 100.
- [x] Eval reports for v1, v2, and fixed v2.
- [x] Version/quality comparison: v1 reached 4.3% accuracy; fixed v2 reached 100% with no regression. This establishes the quality change for experiment E; no infrastructure alert is expected for quality regression.
- [x] Grafana and Prometheus screenshots saved at `screenshots/grafana-dashboard.png` and `screenshots/prometheus-targets.png`.
- [x] Alert screenshots saved for error, latency, cost, and instance-down at `screenshots/alert-high-error-rate.png`, `screenshots/alert-high-latency-p95.png`, `screenshots/alert-cost-burn-rate.png`, and `screenshots/alert-instance-down.png`.
- [x] Jaeger slow and error trace screenshots saved at `screenshots/jaeger-slow-trace.png` and `screenshots/jaeger-error-trace-detail.png`.
- [x] Large-model cost alert (C) fired with Locust traffic.
- [x] Clean Locust CSVs for one and three instances.
- [x] Pause one agent and record `AgentInstanceDown` firing (D).
- [ ] Record the alert detection times and full trace IDs if required by the submission rubric.

## 7. Conclusions

1. Tail latency matters: a small proportion of slow mock calls made p99 exceed 1.6 s even when p95 remained near 220 ms at lower concurrency.
2. Retrieval improved answer quality from 4.3% to 100% on the supplied 23-question dataset, with additional token and cost overhead.
3. Three agent replicas did not increase throughput under this particular local test. Further profiling of the host, Locust, Nginx, and container CPU limits is needed before attributing the bottleneck.
