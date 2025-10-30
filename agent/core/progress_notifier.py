"""Progress notifications for WhatsApp/external messaging"""
import asyncio
import time
from typing import Optional, Callable, Awaitable, Set
from agent.core.events import runtime_events


class ProgressNotifier:
    """
    Sends smart progress updates to user with WhatsApp-optimized throttling.

    Features:
    - Max 2 progress messages per request (avoids spam)
    - Only sends if operation takes > 4 seconds
    - Sends mid-way update if operation > 10 seconds
    - Prioritizes known slow tools (calendar, availability)

    Perfect for WhatsApp where each message triggers a notification.

    Usage:
        notifier = ProgressNotifier(send_message_func)
        notifier.setup()
        notifier.start_request()  # Call at start of each request

        # User gets at most 2 updates:
        # "🗓️ Checking dates..." (when calendar starts)
        # "🔄 Still working, almost done..." (if >10s total)
    """

    # Configuration
    MAX_MESSAGES = 2  # Hard limit per request
    SLOW_OPERATION_THRESHOLD = 4  # seconds - send progress if operation takes longer
    LONG_OPERATION_THRESHOLD = 10  # seconds - send mid-way update

    # Known slow tools that always trigger progress
    SLOW_TOOLS = {
        'calendar.resolve_date_hint',  # ~6 seconds
        'pms.get_availability_and_pricing',  # ~3-5 seconds
    }

    def __init__(
        self,
        send_message: Optional[Callable[[str], Awaitable[None]]] = None,
        enabled: bool = True,
        max_messages: int = 2,
        slow_threshold_sec: float = 4.0,
        long_threshold_sec: float = 10.0
    ):
        """
        Initialize progress notifier.

        Args:
            send_message: Async function to send message to user
                         Example: async def send(msg): await whatsapp.send(user_id, msg)
            enabled: Whether to send notifications (disable for testing)
            max_messages: Maximum progress messages per request (default 2)
            slow_threshold_sec: Send progress if operation takes longer (default 4s)
            long_threshold_sec: Send mid-way update threshold (default 10s)
        """
        self.send_message = send_message
        self.enabled = enabled
        self.MAX_MESSAGES = max_messages
        self.SLOW_OPERATION_THRESHOLD = slow_threshold_sec
        self.LONG_OPERATION_THRESHOLD = long_threshold_sec

        # Request state
        self.messages_sent = 0
        self.start_time: Optional[float] = None
        self.first_slow_tool_seen = False
        self.tools_seen: Set[str] = set()
        self.sent_midway_update = False

        # Tool-specific messages
        self.tool_messages = {
            'calendar.resolve_date_hint': '🗓️ Checking dates...',
            'pms.get_availability_and_pricing': '🔍 Searching for available rooms...',
            'faq.get_rooms_info': '📋 Getting room information...',
            'faq.get_hotel_all_info': '🏨 Getting hotel information...',
            'guest.get_guest_info': '👤 Looking up your reservation...',
        }

        # Phase messages
        self.phase_messages = {
            'planning': '🤔 Planning your request...',
            'wave_start': '⚙️ Processing...',
            'adaptation': '🔄 Finding alternatives...',
            'midway': '🔄 Still working, almost done...',
        }

    def setup(self):
        """Register hooks to send smart progress updates"""
        if not self.enabled or not self.send_message:
            return

        # Hook into tool start events
        runtime_events.on('tool_start', self._on_tool_start)

        # Hook into wave events
        runtime_events.on('wave_start', self._on_wave_start)

        # Hook into execution_complete to stop timing
        runtime_events.on('execution_complete', self._on_execution_complete)

    def start_request(self):
        """
        Start timing for a new request.
        Call this at the beginning of each user request.
        """
        self.messages_sent = 0
        self.start_time = time.time()
        self.first_slow_tool_seen = False
        self.tools_seen.clear()
        self.sent_midway_update = False

    def reset(self):
        """Reset state (alias for start_request)"""
        self.start_request()

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since request start"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def _should_send_message(self) -> bool:
        """Check if we can send another message (under limit)"""
        return self.messages_sent < self.MAX_MESSAGES

    def _is_slow_tool(self, tool_name: str) -> bool:
        """Check if tool is known to be slow"""
        return tool_name in self.SLOW_TOOLS

    async def _send_progress(self, message: str):
        """
        Send a progress message if under limit.

        Args:
            message: Progress message to send
        """
        if not self.enabled or not self.send_message:
            return

        if not self._should_send_message():
            # Already at message limit
            return

        try:
            await self.send_message(message)
            self.messages_sent += 1

            # Emit event for monitoring
            await runtime_events.emit(
                'progress_notification_sent',
                message=message,
                messages_sent=self.messages_sent,
                elapsed_time=self.elapsed_time
            )

        except Exception as e:
            # Don't let notification errors break execution
            print(f"Error sending progress notification: {e}")

    async def _on_tool_start(self, tool_name: str, **kwargs):
        """Send message when slow tool starts"""
        if not self.enabled or not self.send_message:
            return

        # Track tools we've seen
        self.tools_seen.add(tool_name)

        # Only send progress for first slow tool encountered
        if self._is_slow_tool(tool_name) and not self.first_slow_tool_seen:
            self.first_slow_tool_seen = True

            # Get friendly message for this tool
            message = self.tool_messages.get(tool_name, f"⚙️ Running {tool_name}...")

            await self._send_progress(message)

    async def _on_wave_start(self, wave_num: int, total_waves: int, tools: list, **kwargs):
        """
        Check elapsed time and send mid-way update if needed.

        This is called before each wave, giving us a chance to check
        if operation is taking too long.
        """
        if not self.enabled or not self.send_message:
            return

        # Check if we should send mid-way update
        if (
            self.elapsed_time > self.LONG_OPERATION_THRESHOLD
            and not self.sent_midway_update
            and self._should_send_message()
        ):
            self.sent_midway_update = True
            await self._send_progress(self.phase_messages['midway'])

    async def _on_execution_complete(self, **kwargs):
        """Mark execution as complete"""
        # Could log final timing here if needed
        pass

    async def notify_planning(self):
        """
        Notify that planning is happening.
        Usually not needed as execution starts quickly.
        """
        # Don't send planning notification - save message budget for execution
        pass

    async def notify_adaptation(self, reason: str = None):
        """
        Notify that adaptation/retry is happening.
        Only sends if under message limit.
        """
        if not self.enabled or not self.send_message:
            return

        if self._should_send_message():
            message = self.phase_messages['adaptation']
            if reason:
                message += f" ({reason})"
            await self._send_progress(message)

    async def notify_complete(self):
        """
        Notify that processing is complete.
        Usually not needed as final response arrives immediately after.
        """
        # Don't send completion notification - final response is the completion signal
        pass


# Example WhatsApp integration
class WhatsAppProgressNotifier(ProgressNotifier):
    """
    WhatsApp-specific progress notifier.

    Usage:
        notifier = WhatsAppProgressNotifier(
            whatsapp_client=client,
            user_phone="+1234567890"
        )
        notifier.setup()
    """

    def __init__(self, whatsapp_client, user_phone: str, enabled: bool = True):
        """
        Args:
            whatsapp_client: WhatsApp API client
            user_phone: User's phone number
            enabled: Whether to send notifications
        """
        self.whatsapp_client = whatsapp_client
        self.user_phone = user_phone

        async def send_whatsapp_message(message: str):
            """Send message via WhatsApp"""
            await self.whatsapp_client.send_message(
                to=self.user_phone,
                body=message
            )

        super().__init__(send_message=send_whatsapp_message, enabled=enabled)
