from fastapi import HTTPException
from scripts.cancel_state import cancel_flags

def check_cancellation(proc_id: str):
    if cancel_flags.get(proc_id):
        return True
    return False