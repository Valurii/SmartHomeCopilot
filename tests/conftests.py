# tests/conftest.py
try:
    # ab Python 3.12
    import importlib.metadata as _md
except ImportError:
    # Backport
    import importlib_metadata as _md

# Wenn der ThreadPoolExecutor schon existiert: runterfahren und löschen
if hasattr(_md, "_thread_executor"):
    _md._thread_executor.shutdown(wait=False)
    delattr(_md, "_thread_executor")
