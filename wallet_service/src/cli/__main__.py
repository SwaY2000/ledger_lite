"""Command line interface of the wallet service.

Usage:
    python -m src.cli create-account --name alice
    python -m src.cli reconcile --older-than-minutes 15 --limit 100
"""

import argparse
import asyncio
import json
import logging

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import Any

from src.containers import bootstrap
from src.use_cases.dtos import CreateAccountInput, ReconcileDepositsInput


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog='python -m src.cli', description='LedgerLite wallet service CLI')
    commands = parser.add_subparsers(dest='command', required=True)

    create_account = commands.add_parser('create-account', help='Create an account and print its API key once')
    create_account.add_argument('--name', required=True, help='Account name')

    reconcile = commands.add_parser('reconcile', help='Reconcile stale pending deposits with the provider')
    reconcile.add_argument('--older-than-minutes', type=int, default=None, help='Age threshold in minutes')
    reconcile.add_argument('--limit', type=int, default=None, help='Maximum deposits per run')

    return parser.parse_args()


async def _run(command: Callable[[Any], Awaitable[Any]]) -> None:
    """Run a command inside an initialized container."""
    container: Any = bootstrap('base')
    await container.init_resources()
    try:
        result = await command(container)
        print(json.dumps(asdict(result), indent=2, default=str))
    finally:
        await container.shutdown_resources()


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    args = _parse_args()

    if args.command == 'create-account':

        async def command(container: Any) -> Any:
            return await container.create_account_use_case()(CreateAccountInput(name=args.name))

    else:

        async def command(container: Any) -> Any:
            config = container.config
            older_than_minutes = args.older_than_minutes
            if older_than_minutes is None:
                older_than_minutes = config.reconcile_older_than_minutes()
            limit = args.limit if args.limit is not None else config.reconcile_batch_size()
            return await container.reconcile_deposits_use_case()(
                ReconcileDepositsInput(older_than_minutes=older_than_minutes, limit=limit),
            )

    asyncio.run(_run(command))


if __name__ == '__main__':
    main()
