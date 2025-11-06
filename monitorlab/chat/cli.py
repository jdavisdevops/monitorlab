"""CLI entry point for chat interface."""

import asyncio
import sys
import logging

from monitorlab.chat.interface import ChatInterface


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("monitorlab.log"), logging.StreamHandler(sys.stdout)],
    )


def main():
    """Main entry point for monitorlab-chat command."""
    setup_logging()

    try:
        interface = ChatInterface()
        asyncio.run(interface.start())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        logging.exception("Chat interface error")
        sys.exit(1)


if __name__ == "__main__":
    main()
