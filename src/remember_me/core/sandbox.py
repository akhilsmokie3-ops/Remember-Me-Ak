import multiprocessing
import time
import sys
import io
import traceback
from typing import Dict, Any, List

def _worker(code: str, result_queue: multiprocessing.Queue, allowed_imports: set):
    """
    Worker process for executing code.
    Runs in a separate process to allow termination on timeout and stricter isolation.
    """
    # Restrict builtins to a safe subset
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "ascii": ascii, "bin": bin,
        "bool": bool, "bytearray": bytearray, "bytes": bytes, "callable": callable,
        "chr": chr, "classmethod": classmethod, "complex": complex, "dict": dict,
        "dir": dir, "divmod": divmod, "enumerate": enumerate, "filter": filter,
        "float": float, "format": format, "frozenset": frozenset, "getattr": getattr,
        "hasattr": hasattr, "hash": hash, "help": help, "hex": hex, "id": id,
        "int": int, "isinstance": isinstance, "issubclass": issubclass, "iter": iter,
        "len": len, "list": list, "map": map, "max": max, "min": min,
        "next": next, "object": object, "oct": oct, "ord": ord, "pow": pow,
        "print": print, "property": property, "range": range, "repr": repr,
        "reversed": reversed, "round": round, "set": set, "setattr": setattr,
        "slice": slice, "sorted": sorted, "staticmethod": staticmethod, "str": str,
        "sum": sum, "super": super, "tuple": tuple, "type": type, "zip": zip,
    }

    # Custom __import__ to whitelist allowed modules
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in allowed_imports:
            return __import__(name, globals, locals, fromlist, level)
        raise ImportError(f"Import of '{name}' is forbidden by the Sovereign Kernel.")

    safe_builtins["__import__"] = safe_import

    # Execution Context
    exec_globals = {"__builtins__": safe_builtins}

    # Capture stdout
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()

    try:
        exec(code, exec_globals)
        result_queue.put({"success": True, "output": redirected_output.getvalue()})
    except Exception:
        # Capture full traceback for debugging (the user sees this as 'Error')
        result_queue.put({"success": False, "output": traceback.format_exc()})
    finally:
        sys.stdout = old_stdout

class SecurePythonSandbox:
    """
    A sandboxed Python execution environment.
    Uses multiprocessing to enforce timeouts and memory isolation.
    """
    def __init__(self, timeout: int = 2):
        self.timeout = timeout
        # Whitelisted modules that are generally safe for math/logic
        self.allowed_imports = {
            "math", "random", "datetime", "re", "collections",
            "itertools", "functools", "json", "statistics"
        }

    def execute(self, code: str) -> str:
        """
        Executes code in a separate process with a timeout.
        Returns the stdout or error message.
        """
        # Create a queue to get results back from the worker
        queue = multiprocessing.Queue()

        # Spawn the worker process
        process = multiprocessing.Process(
            target=_worker,
            args=(code, queue, self.allowed_imports)
        )
        process.start()

        # Wait for the process to finish or timeout
        process.join(self.timeout)

        if process.is_alive():
            # If still running after timeout, kill it
            process.terminate()
            process.join()
            return "❌ Execution Timed Out (Process terminated to prevent freeze)."

        # Check results
        if not queue.empty():
            result = queue.get()
            if result["success"]:
                output = result["output"]
                return output if output else "[No Output]"
            else:
                return f"❌ Execution Error:\n{result['output']}"
        else:
            # This happens if the process crashed without putting anything in queue
            return "❌ Execution Failed (Worker Process Crash)."
