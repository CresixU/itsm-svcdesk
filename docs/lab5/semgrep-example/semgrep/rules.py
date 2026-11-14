# ai-generated: 0% - the course's example test file for semgrep/rules.yml (CI-SPEC.md P-31)
import asyncio
import time


async def slow_handler(request):
    # ruleid: toy-sleep-in-handler
    time.sleep(1)
    return request


async def fine_handler(request):
    # ok: toy-sleep-in-handler
    await asyncio.sleep(1)
    return request


def batch_job():
    # ok: toy-sleep-in-handler
    time.sleep(1)
