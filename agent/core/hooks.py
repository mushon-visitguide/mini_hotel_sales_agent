"""Pre-built hooks for logging, metrics, and monitoring"""
import logging
from typing import Dict, Any
from agent.core.events import runtime_events, tool_metrics

logger = logging.getLogger(__name__)


class LoggingHooks:
    """
    Logging hooks for runtime events.

    Usage:
        LoggingHooks.setup()  # Register all logging hooks
    """

    @staticmethod
    def setup(verbose: bool = False):
        """
        Setup logging hooks for all runtime events.

        Args:
            verbose: If True, log more detailed information
        """
        if verbose:
            LoggingHooks.setup_verbose()
        else:
            LoggingHooks.setup_standard()

    @staticmethod
    def setup_standard():
        """Standard logging - concise output"""

        def log_tool_start(tool_id: str, tool_name: str, **kwargs):
            logger.info(f"🔧 Starting: {tool_name}")

        def log_tool_complete(tool_id: str, tool_name: str, duration_ms: float, **kwargs):
            logger.info(f"✅ Completed: {tool_name} ({duration_ms:.0f}ms)")

        def log_tool_error(tool_id: str, tool_name: str, error: str, error_type: str, **kwargs):
            logger.error(f"❌ Failed: {tool_name} - {error}")

        def log_wave_start(wave_num: int, total_waves: int, tools: list, **kwargs):
            tool_names = [t.get('tool_name') for t in tools]
            logger.info(f"🌊 Wave {wave_num}/{total_waves}: {len(tools)} tools → {tool_names}")

        def log_wave_complete(wave_num: int, total_waves: int, duration_ms: float, **kwargs):
            logger.info(f"✅ Wave {wave_num}/{total_waves} completed ({duration_ms:.0f}ms)")

        runtime_events.on('tool_start', log_tool_start)
        runtime_events.on('tool_complete', log_tool_complete)
        runtime_events.on('tool_error', log_tool_error)
        runtime_events.on('wave_start', log_wave_start)
        runtime_events.on('wave_complete', log_wave_complete)

        logger.info("📋 Standard logging hooks registered")

    @staticmethod
    def setup_verbose():
        """Verbose logging - detailed output with args and results"""

        def log_tool_start_verbose(tool_id: str, tool_name: str, args: Dict[str, Any], **kwargs):
            logger.info(f"🔧 [Tool Start] {tool_id}: {tool_name}")
            logger.debug(f"   Args: {args}")

        def log_tool_complete_verbose(tool_id: str, tool_name: str, duration_ms: float, **kwargs):
            logger.info(f"✅ [Tool Complete] {tool_id}: {tool_name} ({duration_ms:.0f}ms)")

        def log_tool_error_verbose(tool_id: str, tool_name: str, error: str, error_type: str, duration_ms: float, **kwargs):
            logger.error(f"❌ [Tool Error] {tool_id}: {tool_name}")
            logger.error(f"   Error Type: {error_type}")
            logger.error(f"   Error: {error}")
            logger.error(f"   Duration before failure: {duration_ms:.0f}ms")

        def log_wave_start_verbose(wave_num: int, total_waves: int, tools: list, **kwargs):
            logger.info(f"🌊 [Wave {wave_num}/{total_waves}] Starting parallel execution")
            for tool in tools:
                logger.info(f"   - {tool['tool_id']}: {tool['tool_name']}")

        def log_wave_complete_verbose(wave_num: int, total_waves: int, duration_ms: float, tool_count: int, **kwargs):
            logger.info(f"✅ [Wave {wave_num}/{total_waves}] Completed {tool_count} tools in {duration_ms:.0f}ms")
            logger.info(f"   Average per tool: {duration_ms/tool_count:.0f}ms")

        runtime_events.on('tool_start', log_tool_start_verbose)
        runtime_events.on('tool_complete', log_tool_complete_verbose)
        runtime_events.on('tool_error', log_tool_error_verbose)
        runtime_events.on('wave_start', log_wave_start_verbose)
        runtime_events.on('wave_complete', log_wave_complete_verbose)

        logger.info("📋 Verbose logging hooks registered")


class MetricsHooks:
    """
    Metrics tracking hooks.

    Usage:
        MetricsHooks.setup()  # Register metrics tracking
        MetricsHooks.print_stats()  # View statistics
    """

    @staticmethod
    def setup():
        """Setup metrics tracking hooks"""

        def track_tool_success(tool_name: str, duration_ms: float, **kwargs):
            tool_metrics.record_execution(tool_name, duration_ms, success=True)

        def track_tool_error(tool_name: str, duration_ms: float, **kwargs):
            tool_metrics.record_execution(tool_name, duration_ms, success=False)

        runtime_events.on('tool_complete', track_tool_success)
        runtime_events.on('tool_error', track_tool_error)

        logger.info("📈 Metrics tracking hooks registered")

    @staticmethod
    def print_stats(tool_name: str = None):
        """Print statistics for a specific tool or all tools"""
        if tool_name:
            stats = tool_metrics.get_stats(tool_name)
            print(f"\n📊 Metrics for {tool_name}:")
            print(f"  Total calls: {stats['total_calls']}")
            print(f"  Errors: {stats['total_errors']}")
            print(f"  Avg duration: {stats['avg_duration_ms']:.0f}ms")
            print(f"  Min duration: {stats['min_duration_ms']:.0f}ms")
            print(f"  Max duration: {stats['max_duration_ms']:.0f}ms")
        else:
            stats = tool_metrics.get_stats()
            print(f"\n📊 Overall Metrics:")
            print(f"  Total executions: {stats['total_executions']}")
            print(f"  Total errors: {stats['total_errors']}")
            print(f"  Success rate: {stats['success_rate']:.1f}%")
            print(f"  Avg duration: {stats['avg_duration_ms']:.0f}ms")
            print(f"  Tools used: {', '.join(stats['tools'])}")

    @staticmethod
    def get_stats(tool_name: str = None) -> Dict[str, Any]:
        """Get statistics programmatically"""
        return tool_metrics.get_stats(tool_name)

    @staticmethod
    def reset():
        """Reset all metrics"""
        tool_metrics.reset()
        logger.info("📈 Metrics reset")


class PerformanceHooks:
    """
    Performance monitoring hooks with warnings for slow operations.
    """

    def __init__(self, slow_tool_threshold_ms: float = 5000, slow_wave_threshold_ms: float = 10000):
        """
        Initialize performance monitoring.

        Args:
            slow_tool_threshold_ms: Warn if tool takes longer than this (default 5s)
            slow_wave_threshold_ms: Warn if wave takes longer than this (default 10s)
        """
        self.slow_tool_threshold = slow_tool_threshold_ms
        self.slow_wave_threshold = slow_wave_threshold_ms

    def setup(self):
        """Setup performance monitoring hooks"""

        def check_slow_tool(tool_name: str, duration_ms: float, **kwargs):
            if duration_ms > self.slow_tool_threshold:
                logger.warning(
                    f"⚠️ Slow tool detected: {tool_name} took {duration_ms:.0f}ms "
                    f"(threshold: {self.slow_tool_threshold:.0f}ms)"
                )

        def check_slow_wave(wave_num: int, duration_ms: float, **kwargs):
            if duration_ms > self.slow_wave_threshold:
                logger.warning(
                    f"⚠️ Slow wave detected: Wave {wave_num} took {duration_ms:.0f}ms "
                    f"(threshold: {self.slow_wave_threshold:.0f}ms)"
                )

        runtime_events.on('tool_complete', check_slow_tool)
        runtime_events.on('wave_complete', check_slow_wave)

        logger.info(
            f"⚡ Performance monitoring enabled "
            f"(tool: {self.slow_tool_threshold}ms, wave: {self.slow_wave_threshold}ms)"
        )


class DebugHooks:
    """
    Debug hooks for development - prints detailed execution information.
    """

    @staticmethod
    def setup():
        """Setup debug hooks (very verbose)"""

        def debug_tool_start(tool_id: str, tool_name: str, args: Dict[str, Any], **kwargs):
            print(f"\n🔧 [DEBUG] Tool Starting:")
            print(f"   ID: {tool_id}")
            print(f"   Name: {tool_name}")
            print(f"   Args: {args}")

        def debug_tool_complete(tool_id: str, tool_name: str, duration_ms: float, **kwargs):
            print(f"\n✅ [DEBUG] Tool Completed:")
            print(f"   ID: {tool_id}")
            print(f"   Name: {tool_name}")
            print(f"   Duration: {duration_ms:.2f}ms")

        def debug_tool_error(tool_id: str, tool_name: str, error: str, error_type: str, **kwargs):
            print(f"\n❌ [DEBUG] Tool Failed:")
            print(f"   ID: {tool_id}")
            print(f"   Name: {tool_name}")
            print(f"   Error Type: {error_type}")
            print(f"   Error: {error}")

        def debug_wave_start(wave_num: int, total_waves: int, tools: list, **kwargs):
            print(f"\n🌊 [DEBUG] Wave {wave_num}/{total_waves} Starting:")
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool['tool_id']}: {tool['tool_name']}")

        def debug_wave_complete(wave_num: int, total_waves: int, duration_ms: float, tool_count: int, **kwargs):
            print(f"\n✅ [DEBUG] Wave {wave_num}/{total_waves} Completed:")
            print(f"   Tools: {tool_count}")
            print(f"   Duration: {duration_ms:.2f}ms")
            print(f"   Avg per tool: {duration_ms/tool_count:.2f}ms")

        runtime_events.on('tool_start', debug_tool_start)
        runtime_events.on('tool_complete', debug_tool_complete)
        runtime_events.on('tool_error', debug_tool_error)
        runtime_events.on('wave_start', debug_wave_start)
        runtime_events.on('wave_complete', debug_wave_complete)

        print("🐛 [DEBUG] Debug hooks registered")


def setup_all_hooks(verbose: bool = False, enable_performance_monitoring: bool = True):
    """
    Convenience function to setup all recommended hooks.

    Args:
        verbose: Enable verbose logging
        enable_performance_monitoring: Enable slow operation warnings
    """
    # Setup logging
    LoggingHooks.setup(verbose=verbose)

    # Setup metrics
    MetricsHooks.setup()

    # Setup performance monitoring
    if enable_performance_monitoring:
        perf = PerformanceHooks()
        perf.setup()

    logger.info("✅ All hooks registered and ready")
