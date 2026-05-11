## Reddit Signal Report: r/Observability

### Top recurring complaints
- **Observability is infrastructure-focused, not business-logic-focused**: "all my observability is pointed at infrastructure. i know when cpu spikes, when memory climbs, when error rates m[ove]… but not doing what it's supposed to do. wrong calculations, unexpected branching, edge cases hitting paths that should never get hit." Users consistently feel their tooling catches infra problems but misses behavioral/code-level issues.
- **Log indexing costs explode at scale**: "indexing cost seems to explode with volume" — users running >100GB/day find index-first systems economically painful and are actively looking for alternatives.
- **Signal correlation is still manual**: "jumping between tools, correlating signals manually, guessing where to look next" — even with logs, metrics, and traces, root cause analysis remains a fragmented, time-consuming process.
- **Splunk cost concerns**: Directly called out — "what do you guys think of splunk costs?" — indicating pricing is a known community pain point.
- **Silent production regressions from dependency changes**: "Bumped three dependencies… p95 latency starts climbing… no errors, no exceptions, nothing obviously wrong in the logs." The inability to catch subtle performance degradations from clean deploys is a recurring frustration.
- **Staging doesn't catch prod problems**: "ci passed, staging clean, diff looked reasonable. prod holds for a bit then something starts behaving wrong" — a repeated pattern where pre-production environments provide false confidence.

### Top recurring praise
- **OpenTelemetry (OTel) is the de facto standard**: Recommended repeatedly for instrumentation — "Instrument with OTEL" and "I'd check out OpenTelemetry if you haven't" appear as go-to advice.
- **Loki praised for index-free log management**: "We've had Loki for many years now that doesn't index any log content (only the labels) and at the right scale can be very performant and will soon have columnar storage."
- **Grafana ecosystem widely trusted**: Grafana + Prometheus is the first recommendation for dashboarding and alerting; Grafana Cloud's AI features generate genuine curiosity and engagement.
- **Always-on continuous profiling valued**: "The only way to get ahead of it is to have some lightweight, always-on profiler running on prod" — users who've adopted continuous profiling see it as transformative.
- **Feature flags with audit trails**: Praised as a debugging superpower — "Sometimes just knowing which feature is toggled and what path got hit makes debugging way less of a guessing game."
- **Coralogix's index-less architecture**: Cited as proven at "100s of PBs and thousands of customers" for cost-effective observability.

### Exact Reddit language
- "Observability gives us data… but not answers"
- "jumping between tools, correlating signals manually, guessing where to look next"
- "playing whack-a-mole with this stuff every few months"
- "not crashing, not throwing errors, just not doing what it's supposed to do"
- "all my observability is pointed at infrastructure"
- "indexing cost seems to explode with volume"
- "ClickHouse is a beast for observability"
- "data swamp"
- "If your observability doesn't provide you answers then your observing wrong"
- "Platform-centric metrics are great to scale workloads and measure capacity, but are generally not helpful for Devs/SREs to troubleshoot code"
- "deploy goes out. ci passed, staging clean, diff looked reasonable. prod holds for a bit then something starts behaving wrong"
- "Deployed clean but prod broke"
- "guessing where to look next"
- "p95 latency starts climbing… not dramatic but consistent and getting worse"

### Questions nobody is answering well
- **How to observe business logic correctness, not just infrastructure health**: Multiple posts describe behavioral bugs (wrong calculations, unexpected branching) that no one offers a concrete, proven solution for beyond "add more OTel traces."
- **At what exact scale does indexing become the bottleneck?**: The original poster asked for specific thresholds — only vendor responses appeared; no independent practitioner shared concrete numbers.
- **How to attribute latency regressions to specific dependency changes**: The dependency bump post got sympathy but no one suggested specific tooling or methodology beyond "bisect and reprofile."
- **How does Grafana AI Assistant compare to Dynatrace Davis, Splunk AI, Datadog Bits AI in measurable outcomes?**: Asked directly in the AMA with no visible answer.
- **What does a mature "AI SRE" workflow actually look like end-to-end?**: Multiple references to "AI SRE" and "AI RCA" but no one describes a working, production-validated implementation.
- **How to bridge the gap between "crash-free rate" and true mobile app health**: The Google metrics post implies standard mobile metrics are insufficient, but the community hasn't converged on what "good" looks like.

### Emerging themes
- **AI SRE / AI-driven root cause analysis**: Significant buzz around LLM-powered investigation agents, MCP integrations (SigNoz MCP + Claude Code), and Grafana Assistant. The term "AI SRE" is becoming a recognized category label.
- **Index-less / scan-based log architectures**: Growing interest in alternatives to traditional indexing — time partitioning, columnar storage, and scan-first approaches as cost-saving strategies.
- **Observability for GenAI/LLM applications**: IBM Instana AMA on monitoring GenAI apps, research recruitment for LangGraph multi-agent observability — this is a brand-new surface area the community is just starting to explore.
- **Shift from infra-centric to code/behavior-centric observability**: A clear frustration pattern is driving demand for observability that understands application semantics, not just system metrics.
- **MCP (Model Context Protocol) as an observability interface**: Emerging as a way to connect observability data to AI coding agents — SigNoz already shipping this.
- **Mobile observability gaining attention**: Posts about mobile-specific tooling (bitdrift, crash-free rate limitations) suggest mobile is an underserved segment growing in visibility.
- **OpenTelemetry Collector patterns maturing**: Agent + gateway patterns for Kubernetes indicate the community is moving past "should we use OTel?" to "how do we architect OTel at scale?"

### PMM action items
1. **Lead with the "data but not answers" pain point in messaging**: This exact phrase resonates deeply. Position your product as the bridge from "observability data" to "incident answers" — use their language verbatim in headlines and landing pages.
2. **Create content around "Deployed clean but prod broke" scenarios**: This is an underserved, emotionally charged use case. Build case studies, demo videos, or blog posts showing how your product catches silent regressions that pass CI/staging but degrade prod.
3. **Publish a concrete "indexing cost threshold" guide**: No one is providing independent, vendor-neutral data on when indexing becomes the bottleneck. A well-researched piece with real numbers (GB/day breakpoints, cost curves) would earn massive community trust and SEO value.
4. **Position against "infrastructure-only observability"**: The community explicitly articulates that "platform-centric metrics are not helpful for Devs/SREs to troubleshoot code." If your product offers code-level or business-logic observability, make this the core differentiator.
5. **Develop an "AI SRE" competitive comparison page**: The Grafana AMA question about comparing AI assistants across vendors went unanswered. Be the first to publish an honest, detailed comparison — this will capture high-intent search traffic and establish thought leadership.
6. **Target the GenAI/multi-agent observability whitespace**: This is early-stage but accelerating. If you have any capability here, publish a definitive guide on "observability for LLM-powered applications" before the market gets crowded.
7. **Use "whack-a-mole" and "guessing game" as anti-pattern language in competitive positioning**: These metaphors perfectly describe the status quo frustration. Mirror them in ad copy and landing pages, then contrast with your product's systematic approach.
8. **Build an OTel architecture guide for Kubernetes (agent + gateway pattern)**: High engagement on this topic signals demand for practical, hands-on content. Pair it with your product's OTel integration story.
9. **Address Splunk cost fatigue explicitly**: "What do you guys think of splunk costs?" is an opening. Create a migration guide or TCO calculator targeting Splunk users — this is a warm audience ready to switch.
10. **Invest in mobile observability messaging if applicable**: The community is signaling that "crash-free rate isn't enough" and mobile is underserved. Early positioning here could capture a growing segment before it matures.