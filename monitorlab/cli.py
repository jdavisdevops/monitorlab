"""Main CLI for MonitorLab."""

import asyncio
import sys
import logging
import argparse
import json
from pathlib import Path

from monitorlab.pipelines.pipeline import PipelineRunner
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


async def run_pipeline_command(args):
    """Run a pipeline from file.

    Args:
        args: Command arguments
    """
    settings = get_settings()
    runner = PipelineRunner(settings=settings)

    # Parse variables if provided
    variables = {}
    if args.variables:
        for var in args.variables:
            if "=" in var:
                key, value = var.split("=", 1)
                variables[key] = value

    # Run pipeline
    result = await runner.run_pipeline_file(args.pipeline, variables=variables)

    # Output results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print("\n" + "=" * 80)
        print("PIPELINE RESULTS")
        print("=" * 80)
        print(f"Name: {result['pipeline_name']}")
        print(f"Success: {result['success']}")
        print(f"\nSummary: {result['summary']}")
        print("\nAgent Results:")
        for agent_result in result["agent_results"]:
            print(f"\n  - {agent_result['agent_type']} ({agent_result['status']})")
            print(f"    Execution time: {agent_result['execution_time']:.2f}s")
            if agent_result.get("error"):
                print(f"    Error: {agent_result['error']}")

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


def main():
    """Main entry point for monitorlab-run command."""
    parser = argparse.ArgumentParser(
        description="MonitorLab - AI-Enhanced Website Monitoring System"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run pipeline command
    run_parser = subparsers.add_parser("run", help="Run a testing pipeline")
    run_parser.add_argument("pipeline", help="Path to pipeline YAML file")
    run_parser.add_argument(
        "-v",
        "--variables",
        nargs="+",
        help="Variables to substitute (format: key=value)",
    )
    run_parser.add_argument("-o", "--output", help="Output file for results (JSON)")
    run_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    # For backward compatibility, if no subcommand is provided but --pipeline is there
    parser.add_argument("--pipeline", help="Path to pipeline YAML file (deprecated, use 'run')")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = getattr(args, "log_level", "INFO")
    setup_logging(log_level)

    # Handle commands
    if args.command == "run":
        asyncio.run(run_pipeline_command(args))
    elif args.pipeline:  # Backward compatibility
        # Create a minimal args object
        class MinimalArgs:
            def __init__(self, pipeline):
                self.pipeline = pipeline
                self.variables = None
                self.output = None

        asyncio.run(run_pipeline_command(MinimalArgs(args.pipeline)))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
