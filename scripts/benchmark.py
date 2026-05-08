from __future__ import annotations

import argparse
import asyncio
import time

import httpx


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:18080/health")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    semaphore = asyncio.Semaphore(args.concurrency)
    started = time.perf_counter()

    async def one() -> int:
        async with semaphore:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(args.url)
                return response.status_code

    statuses = await asyncio.gather(*(one() for _ in range(args.requests)))
    elapsed = time.perf_counter() - started
    ok = sum(1 for status in statuses if 200 <= status < 300)
    print(f"requests={args.requests} ok={ok} elapsed={elapsed:.2f}s rps={args.requests / elapsed:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
