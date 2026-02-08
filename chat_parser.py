import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a single chat message"""
    timestamp: datetime
    user: str
    text: str
    raw_line: str


class ChatParser:
    """Parser for WhatsApp chat export files"""

    # Pattern for WhatsApp messages
    # Matches formats like: [26.01.24, 05:47:03] chanti 🎀: message text
    # or: 25.02.24, 01:28:34 chanti 🎀: message text
    MESSAGE_PATTERN = re.compile(
        r'[\[]?(\d{2}\.\d{2}\.\d{2}),\s*(\d{2}:\d{2}:\d{2})[\]]?\s*([^:]+):\s*(.+)'
    )

    def __init__(self):
        pass

    def parse_line(self, line: str) -> Optional[Message]:
        """
        Parse a single line from the chat file.

        Args:
            line: A line from the chat file

        Returns:
            Message object if the line is a valid message, None otherwise
        """
        match = self.MESSAGE_PATTERN.match(line)
        if not match:
            return None

        date_str, time_str, user, text = match.groups()

        try:
            # Parse date: DD.MM.YY format
            timestamp = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%y %H:%M:%S")
        except ValueError:
            return None

        # Clean up user name (remove emoji and extra spaces)
        user = user.strip()

        # Clean up text
        text = text.strip()

        return Message(
            timestamp=timestamp,
            user=user,
            text=text,
            raw_line=line
        )

    def parse_file(self, file_path: str) -> List[Message]:
        """
        Parse an entire chat file.

        Args:
            file_path: Path to the chat file

        Returns:
            List of Message objects
        """
        messages = []

        with open(file_path, 'r', encoding='utf-8') as f:
            current_message = None

            for line in f:
                line = line.rstrip('\n')

                # Try to parse as a new message
                parsed = self.parse_line(line)

                if parsed:
                    # Save previous message if exists
                    if current_message:
                        messages.append(current_message)
                    current_message = parsed
                elif current_message:
                    # This is a continuation of the previous message (multiline)
                    current_message.text += "\n" + line
                    current_message.raw_line += "\n" + line

            # Don't forget the last message
            if current_message:
                messages.append(current_message)

        return messages

    def filter_system_messages(self, messages: List[Message]) -> List[Message]:
        """
        Filter out system messages (like encryption notices, media omitted, etc.)

        Args:
            messages: List of messages

        Returns:
            Filtered list of messages
        """
        system_keywords = [
            "Nachrichten und Anrufe sind Ende-zu-Ende-verschlüsselt",
            "‎Audio weggelassen",
            "‎Video weggelassen",
            "‎Bild weggelassen",
            "‎Sticker weggelassen",
            "‎Dokument weggelassen",
            "‎GIF weggelassen",
            "‎Kontakt weggelassen",
            "Diese Nachricht wurde gelöscht",
            "‎<Diese Nachricht wurde bearbeitet.>"
        ]

        filtered = []
        for msg in messages:
            # Skip if text starts with system marker or contains system keywords
            if msg.text.startswith('‎'):
                continue

            is_system = any(keyword in msg.text for keyword in system_keywords)
            if not is_system:
                filtered.append(msg)

        return filtered
