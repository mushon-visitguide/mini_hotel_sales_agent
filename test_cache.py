#!/usr/bin/env python3
"""Test the holiday caching mechanism"""
import time
from agent.tools.calendar.holiday_resolver import get_all_holidays_cached, _holidays_cache

print("Testing holiday cache with 24h TTL...\n")

# First call - should fetch from API
print("1️⃣  First call (cache MISS - fetching from API)...")
start = time.time()
result1 = get_all_holidays_cached()
duration1 = time.time() - start
print(f"   ✓ Took {duration1:.2f}s")
print(f"   Cache timestamp: {_holidays_cache['timestamp']}")
print(f"   Got {len(result1.split(chr(10)))} holidays")
print()

# Second call - should use cache
print("2️⃣  Second call (cache HIT - using cached data)...")
start = time.time()
result2 = get_all_holidays_cached()
duration2 = time.time() - start
print(f"   ✓ Took {duration2:.2f}s")
print(f"   Cache timestamp: {_holidays_cache['timestamp']}")
print()

# Verify cache is working
if duration2 < duration1 / 10:  # Should be at least 10x faster
    print("✅ Cache is working! Second call was much faster")
else:
    print("⚠️  Cache might not be working - second call wasn't significantly faster")

print()
print(f"Cache will expire in {_holidays_cache['ttl_hours']} hours")
print()

# Show sample of cached holidays
print("Sample holidays:")
for line in result1.split('\n')[:5]:
    print(f"  {line}")
