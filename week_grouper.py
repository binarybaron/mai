from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
from chat_parser import Message
from config import TARGET_USER


class WeekGrouper:
    """Groups messages by week and extracts conversations involving the target user"""

    def __init__(self, target_user: str = TARGET_USER):
        self.target_user = target_user

    def get_week_key(self, dt: datetime) -> str:
        """
        Get the week key for a datetime (ISO week format: YYYY-WXX).

        Args:
            dt: Datetime object

        Returns:
            Week key string (e.g., "2024-W04")
        """
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"

    def get_week_range(self, dt: datetime) -> tuple[datetime, datetime]:
        """
        Get the start and end datetime for the week containing dt.

        Args:
            dt: Datetime object

        Returns:
            Tuple of (week_start, week_end)
        """
        # Get ISO week info
        year, week, weekday = dt.isocalendar()

        # Get first day of the week (Monday)
        week_start = datetime.strptime(f"{year}-W{week:02d}-1", "%Y-W%W-%w")

        # Get last day of the week (Sunday)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        return week_start, week_end

    def group_by_week(self, messages: List[Message]) -> Dict[str, List[Message]]:
        """
        Group messages by week.

        Args:
            messages: List of Message objects

        Returns:
            Dictionary mapping week keys to lists of messages
        """
        weeks = defaultdict(list)

        for msg in messages:
            week_key = self.get_week_key(msg.timestamp)
            weeks[week_key].append(msg)

        return dict(weeks)

    def extract_context_window(self, messages: List[Message], target_index: int, context_size: int = 5) -> List[Message]:
        """
        Extract a context window around a target user's message.

        Args:
            messages: List of messages
            target_index: Index of the target message
            context_size: Number of messages before and after to include

        Returns:
            List of messages in the context window
        """
        start = max(0, target_index - context_size)
        end = min(len(messages), target_index + context_size + 1)
        return messages[start:end]

    def extract_conversations(self, messages: List[Message], context_size: int = 5) -> List[List[Message]]:
        """
        Extract conversation snippets that include the target user.

        Args:
            messages: List of messages
            context_size: Number of messages before and after target user's messages

        Returns:
            List of conversation snippets (each snippet is a list of messages)
        """
        conversations = []
        used_indices = set()

        for i, msg in enumerate(messages):
            if msg.user == self.target_user and i not in used_indices:
                # Extract context window
                context = self.extract_context_window(messages, i, context_size)

                # Mark these indices as used
                start_idx = max(0, i - context_size)
                end_idx = min(len(messages), i + context_size + 1)
                for idx in range(start_idx, end_idx):
                    used_indices.add(idx)

                conversations.append(context)

        return conversations

    def format_conversation(self, messages: List[Message]) -> str:
        """
        Format a conversation snippet as text.

        Args:
            messages: List of messages in the conversation

        Returns:
            Formatted conversation string
        """
        lines = []
        for msg in messages:
            date_str = msg.timestamp.strftime("%d.%m.%y, %H:%M:%S")
            lines.append(f"[{date_str}] {msg.user}: {msg.text}")
        return "\n".join(lines)

    def get_weekly_summaries(self, messages: List[Message]) -> Dict[str, Dict]:
        """
        Group messages by week and extract conversation summaries for each week.

        Args:
            messages: List of all messages

        Returns:
            Dictionary mapping week keys to week data including:
            - week_key: ISO week identifier
            - week_start: Start datetime of the week
            - week_end: End datetime of the week
            - conversations: List of formatted conversation strings
            - target_message_count: Number of messages from target user
            - total_message_count: Total messages in the week
        """
        weeks_data = {}
        weeks = self.group_by_week(messages)

        for week_key in sorted(weeks.keys()):
            week_messages = weeks[week_key]

            # Get week date range
            first_msg = week_messages[0]
            week_start, week_end = self.get_week_range(first_msg.timestamp)

            # Extract conversations
            conversations = self.extract_conversations(week_messages)
            formatted_conversations = [self.format_conversation(conv) for conv in conversations]

            # Count target user messages
            target_count = sum(1 for msg in week_messages if msg.user == self.target_user)

            weeks_data[week_key] = {
                "week_key": week_key,
                "week_start": week_start,
                "week_end": week_end,
                "conversations": formatted_conversations,
                "target_message_count": target_count,
                "total_message_count": len(week_messages)
            }

        return weeks_data
