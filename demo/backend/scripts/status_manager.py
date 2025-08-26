from collections import defaultdict
import asyncio

# Unique asyncio.Queue for each Proc_ID
status_queues = defaultdict(asyncio.Queue)

def get_queue(proc_id: str) -> asyncio.Queue:
    return status_queues[proc_id]

async def send_status(proc_id: str, message: str):
    queue = get_queue(proc_id)
    await queue.put(message)

def remove_queue(proc_id: str):
    if proc_id in status_queues:
        del status_queues[proc_id]
