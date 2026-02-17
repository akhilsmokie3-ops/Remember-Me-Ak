import multiprocessing
import multiprocessing.connection
import sys
import io
import traceback
import time
from typing import Dict, Any, Set, Optional

def _worker(conn: multiprocessing.connection.Connection, allowed_imports: Set[str]):
    """
    Persistent Worker process for executing code in a REPL-like environment.
    Maintains state (variables) across executions until reset.
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
        # Allow submodules of allowed packages (e.g., 'os.path' if 'os' was allowed, though it isn't here)
        base_name = name.split('.')[0]
        if base_name in allowed_imports:
             return __import__(name, globals, locals, fromlist, level)
        raise ImportError(f"Import of '{name}' is forbidden by the Sovereign Kernel.")

    safe_builtins["__import__"] = safe_import

    # Initialize Execution Context
    exec_globals = {"__builtins__": safe_builtins}

    while True:
        try:
            if not conn.poll(timeout=None): # Block until data is available
                continue

            msg = conn.recv()

            # Control Signals
            if msg == "STOP":
                break

            if msg == "RESET":
                exec_globals = {"__builtins__": safe_builtins}
                conn.send({"status": "RESET_OK"})
                continue

            # Execution Logic
            code = msg.get("code", "")
            if not code:
                conn.send({"status": "ERROR", "output": "Empty Code Block"})
                continue

            # Capture stdout
            old_stdout = sys.stdout
            redirected_output = sys.stdout = io.StringIO()

            try:
                # Compile first to catch syntax errors early
                compiled_code = compile(code, "<sandbox>", "exec")
                exec(compiled_code, exec_globals)

                output = redirected_output.getvalue()
                conn.send({"status": "OK", "output": output if output else "[No Output]"})

            except Exception:
                # Capture traceback
                conn.send({"status": "ERROR", "output": traceback.format_exc()})

            finally:
                sys.stdout = old_stdout

        except EOFError:
            break
        except Exception as e:
            # Fatal error in the loop (e.g. pipe broken)
            try:
                conn.send({"status": "FATAL", "output": str(e)})
            except:
                pass
            break

class SecurePythonSandbox:
    """
    A persistent, sandboxed Python execution environment (REPL).
    Uses multiprocessing.Pipe for communication and maintains state.
    """
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        # Whitelisted modules
        self.allowed_imports = {
            "math", "random", "datetime", "re", "collections",
            "itertools", "functools", "json", "statistics",
            "numpy", "pandas" # Allowed if installed, logic handles availability
        }

        self.process: Optional[multiprocessing.Process] = None
        self.parent_conn: Optional[multiprocessing.connection.Connection] = None
        self._start_worker()

    def _start_worker(self):
        """Starts the persistent worker process."""
        if self.process and self.process.is_alive():
            return

        self.parent_conn, child_conn = multiprocessing.Pipe()
        self.process = multiprocessing.Process(
            target=_worker,
            args=(child_conn, self.allowed_imports)
        )
        self.process.daemon = True # Kill if parent dies
        self.process.start()

    def execute(self, code: str) -> str:
        """
        Executes code in the persistent session.
        Returns stdout or error message.
        """
        if not self.process or not self.process.is_alive():
            self._start_worker()

        try:
            self.parent_conn.send({"code": code})

            if self.parent_conn.poll(self.timeout):
                result = self.parent_conn.recv()

                if result["status"] == "OK":
                    return result["output"]
                elif result["status"] == "RESET_OK":
                     return "State Reset."
                else: # ERROR or FATAL
                    return f"❌ Execution Error:\n{result.get('output', 'Unknown Error')}"
            else:
                # Timeout
                self._restart_worker()
                return "❌ Execution Timed Out (Process Restarted)."

        except (BrokenPipeError, EOFError):
            self._restart_worker()
            return "❌ Connection Lost (Process Restarted)."
        except Exception as e:
            self._restart_worker()
            return f"❌ System Error: {e}"

    def reset(self):
        """Clears the session state (variables)."""
        if not self.process or not self.process.is_alive():
             self._start_worker()
             return

        try:
            self.parent_conn.send("RESET")
            if self.parent_conn.poll(self.timeout):
                self.parent_conn.recv() # Wait for ack
        except:
            self._restart_worker()

    def _restart_worker(self):
        """Kills and restarts the worker process."""
        if self.process:
            self.process.terminate()
            self.process.join()
        self._start_worker()

    def shutdown(self):
        """Cleanly shuts down the worker."""
        if self.process and self.process.is_alive():
            try:
                self.parent_conn.send("STOP")
                self.process.join(1)
            except:
                pass
            if self.process.is_alive():
                self.process.terminate()
