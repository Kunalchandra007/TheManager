"""CloudWatch/X-Ray-friendly tracing with a no-op local fallback."""

from contextlib import contextmanager
from typing import Iterator

try:
    from aws_xray_sdk.core import xray_recorder
except ImportError:  # Local tests do not require the X-Ray SDK.
    xray_recorder = None


@contextmanager
def trace(name: str) -> Iterator[None]:
    if xray_recorder is None:
        yield
        return
    segment = xray_recorder.begin_subsegment(name)
    try:
        yield
    except Exception as error:
        segment.add_exception(error, __import__("traceback").extract_tb(error.__traceback__))
        raise
    finally:
        xray_recorder.end_subsegment()
