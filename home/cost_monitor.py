from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CostMonitor:
    """Monitor and control API costs with cache tracking"""
    
    def __init__(self):
        self.daily_limit = 100
        self.cost_per_openai_call = 0.002
        self.cost_per_gmaps_call = 0.005
        self.cache_hit_key = "cache_monitor_hits"
        self.cache_miss_key = "cache_monitor_misses"

    def _get_today_key(self, service):
        """Get cache key for today's usage"""
        today = timezone.now().date()
        return f"cost_monitor_{service}_{today}"

    def track_api_call(self, service, cost=None):
        """Track an API call and its cost"""
        today_key = self._get_today_key(service)
        current_count = cache.get(today_key, 0) + 1
        
        tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        seconds_until_tomorrow = (tomorrow - timezone.now()).total_seconds()
        
        cache.set(today_key, current_count, int(seconds_until_tomorrow))
        
        # Also track hourly usage for charts
        self._track_hourly_usage(service)
        
        estimated_cost = cost or (self.cost_per_openai_call if service == 'openai' else self.cost_per_gmaps_call)
        logger.info(f"API call tracked - Service: {service}, Count: {current_count}, Est. Cost: ${estimated_cost:.4f}")
        
        return current_count

    def _track_hourly_usage(self, service):
        """Track hourly usage for dashboard charts"""
        now = timezone.now()
        hour_key = f"hourly_{service}_{now.strftime('%Y%m%d_%H')}"
        
        try:
            cache.incr(hour_key)
        except ValueError:
            # Key doesn't exist, initialize it (expire in 25 hours)
            cache.set(hour_key, 1, timeout=25 * 3600)

    def get_hourly_usage(self, hours_back=6):
        """Get hourly usage data for the last N hours"""
        now = timezone.now()
        hourly_data = {'openai': [], 'google_maps': [], 'labels': []}
        
        for i in range(hours_back, -1, -1):
            hour_time = now - timedelta(hours=i)
            hour_key_openai = f"hourly_openai_{hour_time.strftime('%Y%m%d_%H')}"
            hour_key_gmaps = f"hourly_google_maps_{hour_time.strftime('%Y%m%d_%H')}"
            
            openai_count = cache.get(hour_key_openai, 0)
            gmaps_count = cache.get(hour_key_gmaps, 0)
            
            hourly_data['openai'].append(openai_count)
            hourly_data['google_maps'].append(gmaps_count)
            
            if i == 0:
                hourly_data['labels'].append('Now')
            else:
                hourly_data['labels'].append(f'{i}h ago')
        
        return hourly_data

    def track_cache_hit(self):
        """Tracks a cache hit."""
        try:
            cache.incr(self.cache_hit_key)
        except ValueError:
            # Key doesn't exist, initialize it
            cache.set(self.cache_hit_key, 1, timeout=86400)

    def track_cache_miss(self):
        """Tracks a cache miss."""
        try:
            cache.incr(self.cache_miss_key)
        except ValueError:
            # Key doesn't exist, initialize it
            cache.set(self.cache_miss_key, 1, timeout=86400)

    def get_cache_stats(self):
        """Returns a dictionary with cache hits, misses, and hit rate."""
        hits = cache.get(self.cache_hit_key, 0)
        misses = cache.get(self.cache_miss_key, 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        return {"hits": hits, "misses": misses, "hit_rate": hit_rate}

    def should_allow_api_call(self, service):
        """Check if we should allow another API call today"""
        current_count = cache.get(self._get_today_key(service), 0)
        if current_count >= self.daily_limit:
            logger.warning(f"Daily API limit reached for {service}: {current_count}/{self.daily_limit}")
            return False
        return True

    def get_daily_usage(self, service=None):
        """Get today's usage statistics including cache stats"""
        services = [service] if service else ['openai', 'google_maps', 'google_places']
        usage = {}
        total_cost = 0
        
        for svc in services:
            count = cache.get(self._get_today_key(svc), 0)
            cost_per_call = self.cost_per_openai_call if svc == 'openai' else self.cost_per_gmaps_call
            service_cost = count * cost_per_call
            usage[svc] = {'calls': count, 'cost': service_cost, 'limit': self.daily_limit}
            total_cost += service_cost
            
        usage['total_cost'] = total_cost
        usage['cache_stats'] = self.get_cache_stats()
        return usage
    
    def get_cost_recommendation(self):
        """Get cost optimization recommendations"""
        usage = self.get_daily_usage()
        recommendations = []
        
        if usage['total_cost'] > 1.0:  # $1 per day
            recommendations.append("Consider enabling more aggressive caching")
            recommendations.append("Use template-based responses for common queries")
        
        if usage.get('openai', {}).get('calls', 0) > 50:
            recommendations.append("Switch to GPT-4o-mini for cost savings")
            recommendations.append("Reduce token limits in prompts")
        
        if usage.get('google_maps', {}).get('calls', 0) > 50:
            recommendations.append("Implement more aggressive Google Maps caching")
            recommendations.append("Use simple Google Maps links instead of API calls")
        
        return recommendations

# Global cost monitor instance
cost_monitor = CostMonitor()
