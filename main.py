#!/usr/bin/env python3
import asyncio
from demo_cli import main as cli_main


def main():
    asyncio.run(cli_main())


if __name__ == "__main__":
    main()

