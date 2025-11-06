"""CLI entry point for MonitorLab."""

import asyncio
import sys
import logging
import argparse
from monitorlab.ui import launch_ui
from monitorlab.config.settings import get_settings


def setup_logging(log_level: str):
    """Setup logging configuration.

    Args:
        log_level: Logging level
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("monitorlab.log"), logging.StreamHandler(sys.stdout)],
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MonitorLab - AI-Enhanced Website Monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  monitorlab                    # Launch Gradio UI
  monitorlab --port 8080        # Launch UI on specific port
  monitorlab --share            # Create public share link

For more information, visit: https://github.com/yourusername/monitorlab
""",
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Port for Gradio server (default from settings)",
    )

    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public share link",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Launch UI
    try:
        print("🔬 MonitorLab v0.2.0")
        print("=" * 50)
        print("Starting Gradio interface...")
        print("\nMake sure:")
        print("  ✅ LM Studio is running")
        print("  ✅ Qwen2-VL-4B model is loaded")
        print("  ✅ Local Server is started (port 1234)")
        print("=" * 50)

        launch_ui(share=args.share, server_port=args.port)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.exception("CLI error")
        sys.exit(1)


if __name__ == "__main__":
    main()
