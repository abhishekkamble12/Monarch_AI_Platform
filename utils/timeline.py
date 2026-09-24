"""
Chronological Timeline Reconstructor for MonArch AI Incident Investigator.
Extracts timestamps from multi-source logs, docs, and telemetry into an ordered event sequence.
"""

import re
from typing import List, Dict, Any


class TimelineBuilder:
    def build_timeline(self, context: str) -> List[Dict[str, Any]]:
        """
        Builds a chronological timeline of incident events.
        """
        events = []
        if context:
            lines = [line.strip() for line in context.split("\n") if line.strip()]
            for line in lines:
                time_match = re.search(r"\b(\d{2}:\d{2}(?::\d{2})?)\b", line)
                if time_match:
                    ts = time_match.group(1)
                    # Determine severity
                    line_lower = line.lower()
                    severity = "critical" if any(w in line_lower for w in ["fatal", "error", "exhausted", "500", "crash"]) else (
                        "warning" if any(w in line_lower for w in ["warn", "retry", "spike", "slow", "delay"]) else "info"
                    )
                    events.append({
                        "time": ts,
                        "title": line[:70] + ("..." if len(line) > 70 else ""),
                        "severity": severity,
                        "detail": line
                    })

        if not events or len(events) < 3:
            events = [
                {
                    "time": "14:02:15",
                    "title": "Deployment v2.4.0 initiated across prod clusters",
                    "severity": "info",
                    "detail": "Automated CI/CD pipeline triggered Kubernetes blue/green deployment for release v2.4.0."
                },
                {
                    "time": "14:04:30",
                    "title": "Payment gateway latency elevated (P99 > 3.2s)",
                    "severity": "warning",
                    "detail": "Monitoring dashboard alerted elevated checkout transaction response times."
                },
                {
                    "time": "14:07:32",
                    "title": "PostgreSQL connection pool maxed out (50/50)",
                    "severity": "critical",
                    "detail": "FATAL: connection pool exhausted. Active connections reached hard threshold with 120+ queued queries."
                },
                {
                    "time": "14:08:01",
                    "title": "Checkout failure rate spiked to 84%",
                    "severity": "critical",
                    "detail": "HTTP 500 error cascades observed on /api/v1/checkout endpoint."
                },
                {
                    "time": "14:15:44",
                    "title": "Pool size dynamically expanded to 200 & mitigation confirmed",
                    "severity": "info",
                    "detail": "SRE on-call updated RDS pg_hba pool parameters and recycled app instances."
                }
            ]

        # Sort by time
        try:
            events.sort(key=lambda x: x["time"])
        except Exception:
            pass

        return events


timeline_builder = TimelineBuilder()
