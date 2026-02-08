import os
import tempfile
import zipfile
from typing import List
from pathlib import Path
from chat_parser import ChatParser, Message


class ArchiveProcessor:
    """Handles extraction and processing of WhatsApp chat archives"""

    def __init__(self):
        self.parser = ChatParser()

    def extract_archive(self, archive_path: str, temp_dir: str) -> str:
        """
        Extract a zip archive to a temporary directory.

        Args:
            archive_path: Path to the zip file
            temp_dir: Temporary directory to extract to

        Returns:
            Path to the extracted directory
        """
        extract_path = os.path.join(temp_dir, Path(archive_path).stem)
        os.makedirs(extract_path, exist_ok=True)

        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        return extract_path

    def find_chat_file(self, directory: str) -> str:
        """
        Find the _chat.txt file in the extracted directory.

        Args:
            directory: Directory to search in

        Returns:
            Path to the _chat.txt file

        Raises:
            FileNotFoundError: If _chat.txt is not found
        """
        chat_file = os.path.join(directory, "_chat.txt")
        if not os.path.exists(chat_file):
            raise FileNotFoundError(f"_chat.txt not found in {directory}")
        return chat_file

    def process_archive(self, archive_path: str) -> List[Message]:
        """
        Process a single archive file: extract, parse, and return messages.

        Args:
            archive_path: Path to the WhatsApp chat archive (.zip)

        Returns:
            List of parsed Message objects
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive
            extract_path = self.extract_archive(archive_path, temp_dir)

            # Find chat file
            chat_file = self.find_chat_file(extract_path)

            # Parse messages
            messages = self.parser.parse_file(chat_file)

            # Filter system messages
            messages = self.parser.filter_system_messages(messages)

            return messages

    def process_all_archives(self, data_dir: str) -> List[Message]:
        """
        Process all zip archives in the data directory.

        Args:
            data_dir: Directory containing WhatsApp chat archives

        Returns:
            Combined list of all messages from all archives
        """
        all_messages = []

        # Find all .zip files
        zip_files = list(Path(data_dir).glob("*.zip"))

        print(f"Found {len(zip_files)} archive(s) to process")

        for zip_file in zip_files:
            print(f"Processing: {zip_file.name}")
            try:
                messages = self.process_archive(str(zip_file))
                all_messages.extend(messages)
                print(f"  -> Extracted {len(messages)} messages")
            except Exception as e:
                print(f"  -> Error processing {zip_file.name}: {e}")

        # Also process standalone _chat.txt if it exists
        standalone_chat = os.path.join(data_dir, "_chat.txt")
        if os.path.exists(standalone_chat):
            print(f"Processing standalone: _chat.txt")
            try:
                messages = self.parser.parse_file(standalone_chat)
                messages = self.parser.filter_system_messages(messages)
                all_messages.extend(messages)
                print(f"  -> Extracted {len(messages)} messages")
            except Exception as e:
                print(f"  -> Error processing _chat.txt: {e}")

        # Sort all messages by timestamp
        all_messages.sort(key=lambda m: m.timestamp)

        print(f"\nTotal messages: {len(all_messages)}")

        return all_messages
