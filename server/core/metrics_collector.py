"""
Metrics Collector
Handles collection of proxy usage metrics
"""

from typing import Dict, List
from statistics import mean

class MetricsCollector:
    """Collects and provides access to proxy usage metrics"""

    def __init__(self):
        self.usage_count: Dict[str, int] = {}  # proxy_url -> number of times used
        self.success_count: Dict[str, int] = {}  # proxy_url -> number of successful requests
        self.response_times: Dict[str, List[float]] = {}  # proxy_url -> list of response times
        self.rate_limit_count: Dict[str, int] = {}  # proxy_url -> number of rate limits encountered

    def record_proxy_usage(self, proxy_url: str):
        """Record usage of a proxy"""
        self.usage_count[proxy_url] = self.usage_count.get(proxy_url, 0) + 1

    def record_proxy_success(self, proxy_url: str):
        """Record successful use of a proxy"""
        self.success_count[proxy_url] = self.success_count.get(proxy_url, 0) + 1

    def record_response_time(self, proxy_url: str, response_time: float):
        """Record response time for a proxy"""
        if proxy_url not in self.response_times:
            self.response_times[proxy_url] = []
        self.response_times[proxy_url].append(response_time)

    def record_rate_limit(self, proxy_url: str):
        """Record rate limit encounter for a proxy"""
        self.rate_limit_count[proxy_url] = self.rate_limit_count.get(proxy_url, 0) + 1

    def get_proxy_metrics(self, proxy_url: str) -> Dict[str, float]:
        """Get metrics for a specific proxy"""
        usage = self.usage_count.get(proxy_url, 0)
        success = self.success_count.get(proxy_url, 0)
        avg_response_time = mean(self.response_times.get(proxy_url, [0]))
        rate_limits = self.rate_limit_count.get(proxy_url, 0)

        success_rate = (success / usage) * 100 if usage > 0 else 0

        return {
            'usage_count': usage,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'rate_limit_count': rate_limits
        }

    def get_all_proxy_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get metrics for all proxies"""
        return {proxy_url: self.get_proxy_metrics(proxy_url) for proxy_url in self.usage_count.keys()}
