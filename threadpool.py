from concurrent.futures import ThreadPoolExecutor
from logconfig import logger

# global threadpools

threadpool = ThreadPoolExecutor()

cacherpool = ThreadPoolExecutor()

def run_on_threadpool(func, *args, **kwargs):
    try:
        logger.debug(
            f"Submitting {func.__name__} to threadpool"
        )
        return threadpool.submit(func, *args, **kwargs)
    except Exception as e:
        logger.error(f"Failed to submit {func.__name__} to threadpool: {e}", exc_info=True)
        return None

def run_on_cacherpool(func, *args, **kwargs):
    try:
        logger.debug(
            f"Submitting {func.__name__} to cacherpool"
        )
        return cacherpool.submit(func, *args, **kwargs)
    except Exception as e:
        logger.error(f"Failed to submit {func.__name__} to cacherpool: {e}", exc_info=True)
        return None