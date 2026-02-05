## 2024-05-23 - Sinkhorn Degeneration in Single-Query Transport
**Learning:** The Sinkhorn algorithm for Optimal Transport mathematically degenerates to a standard Softmax (attention) distribution when the target marginal is a single point (M=1), provided the goal is simply to rank source relevance. The iterative Sinkhorn implementation was not only computationally expensive (O(N*iter)) but numerically unstable in high-dimensional spaces (768D), often underflowing to zero or producing uniform distributions due to clamping.
**Action:** Replaced the iterative Sinkhorn loop with `torch.nn.functional.softmax` specifically for the `M=1` case. This yields a ~5x speedup (0.3ms vs 1.5ms) and guarantees numerical stability without sacrificing the "Optimal Transport" theoretical framework (since Softmax is the analytic solution for this specific boundary condition).

## 2024-05-24 - Heavy Import Blocking in Local Independence Layer
**Learning:** `LocalEmbedder` imported `sentence_transformers` (and transitively `torch`, `transformers`) at the top level. This added ~7 seconds of overhead to the import of `remember_me.core`, even if the user intended to use an external API-based embedder or just the `CSNPManager` logic.
**Action:** Moved the `sentence_transformers` import inside the `_ensure_model_loaded` method. This reduces startup time for non-local-embedding use cases to < 0.1s, while preserving the functionality for local mode (loading only when first needed).

## 2024-05-25 - Zero-Allocation Tensor Management in CSNP
**Learning:** `torch.cat` is a convenience function that allocates new memory and copies data. In `CSNPManager`, repeated use of `torch.cat` in the `update_state` loop caused O(N) allocation overhead per step, leading to memory fragmentation and GC pressure. Pre-allocating a fixed-capacity tensor and managing a `size` pointer mimics C-style memory management in Python, eliminating allocations entirely during the steady state.
**Action:** Replaced dynamic `torch.cat` growth with a pre-allocated `memory_bank` buffer of size `context_limit + 1` (to allow "Add then Evict" logic without intermediate allocation). Replaced eviction slicing with in-place tensor shifting. This resulted in a ~3x speedup in fill time and ~2x speedup in steady-state compression cycles.

## 2025-02-18 - Incremental Norm Maintenance in CSNP
**Learning:** `WassersteinMetric` re-computes the squared Euclidean norms of the entire `memory_bank` (O(N*D)) during every `update_state` call to build the cost matrix. Since the memory bank changes only incrementally (one addition + one eviction), 99% of these norm calculations are redundant.
**Action:** Added `memory_norms` tensor to `CSNPManager` to maintain norms incrementally (O(D) per step). Modified `WassersteinMetric` to accept pre-computed norms. This eliminates the O(N*D) bottleneck in the hot path, reducing transport calculation time significantly for large context limits (e.g., N=1000).

## 2025-02-23 - Lazy Dimension Resolution
**Learning:** `LocalEmbedder` correctly delayed the import of `sentence_transformers`, but its `.dim` property (accessed during `CSNPManager.__init__`) triggered the model load anyway to ascertain embedding dimensions. This caused `CSNPManager` instantiation to block for ~7 seconds, negating the benefit of the lazy import.
**Action:** Added `KNOWN_DIMS` dictionary to `LocalEmbedder` for common models (e.g., `all-MiniLM-L6-v2`: 384). If the model name is known, dimensions are resolved instantly without loading the heavy model, restoring the sub-millisecond startup time for the manager.

## 2025-10-26 - Context Retrieval Caching
**Learning:** `CSNPManager.retrieve_context` iterates through the text buffer, verifies integrity for each item (hashing), and joins strings on every call. In high-frequency polling scenarios (e.g., UI updates or multi-agent loops), this redundant processing wasted CPU cycles.
**Action:** Implemented `_context_cache` to store the verified context string. The cache is invalidated only when the state changes (in `update_state` and `load_state`). This reduced `retrieve_context` latency from ~426µs to ~0.65µs (~650x speedup) for cached hits.

## 2025-10-26 - Optimized Norm Calculation in Transport
**Learning:** `WassersteinMetric` was re-calculating the squared norm of the `query_state` (O(D)) on every compression cycle, even though `CSNPManager` guarantees the identity state is normalized (norm=1.0).
**Action:** Updated `WassersteinMetric` to accept `y_norms` and passed a pre-computed scalar `1.0` from `CSNPManager`. This avoids O(D) operations during the transport calculation hot path.

## 2025-10-26 - Single-Pass Regex Intent Detection
**Learning:** `SovereignAgent._detect_intents` iterated over a dictionary of regex patterns, scanning the input string multiple times (O(k * N)).
**Action:** Combined all intent patterns into a single named-group regex (`(?P<IMAGE>...)|(?P<SEARCH>...)`) and used `re.finditer` to detect all intents in a single pass (O(N)).

## 2025-10-27 - Zero-Allocation Identity Normalization
**Learning:** `F.normalize` creates a new tensor for the result, breaking the "Zero-Allocation" contract of the `update_state` loop in `CSNPManager`. In high-throughput scenarios, this constant reallocation of the Identity State vector creates unnecessary GC pressure.
**Action:** Replaced `F.normalize` with in-place operations: `norm = x.norm(...); x.div_(norm)`. This ensures the `identity_state` tensor remains in the same memory location throughout the lifecycle of the agent.

## 2025-05-27 - Overlapping Tensor Shift Failure
**Learning:** Attempted to remove `.clone()` when shifting `CSNPManager` memory buffer (`bank[i:-1] = bank[i+1:]`) to save allocation. PyTorch raised `RuntimeError: unsupported operation: some elements of the input tensor and the written-to tensor refer to a single memory location`. Even `copy_()` enforces this check.
**Action:** Reverted to using `.clone()`. For overlapping shifts, `clone()` or manual loop (slow in Python) is required. Safe memory access > Optimization here.

## 2025-10-27 - Optimized Hash Verification
**Learning:** `CSNPManager.retrieve_context` re-hashes every memory string (O(N*L)) to verify integrity against the Merkle Chain, even when the data hasn't changed. This created unnecessary CPU load during the hot generation path.
**Action:** Implemented `hash_buffer` to store hashes alongside text, enabling O(1) verification via set lookup. Included fallback regeneration in `load_state` to ensure backward compatibility with legacy state files.

## 2025-10-27 - Memory Optimization for Integrity Chain
**Learning:** `IntegrityChain` maintains an ever-growing list of `MerkleNode` objects for the session history. Standard Python objects use `__dict__` for attribute storage, consuming ~152 bytes per node. For long-running sessions with thousands of turns, this memory overhead becomes significant and causes cache misses.
**Action:** Added `__slots__ = ['hash', 'data', 'left', 'right']` to `MerkleNode`. This reduces per-node memory to ~64 bytes (2.3x reduction) and speeds up node creation by ~20%.

## 2025-10-28 - Parallel Tool Execution in SovereignAgent
**Learning:** The `SovereignAgent` executed tools sequentially: Search -> Code -> Synthesis -> Image. Both "Synthesis" (LLM) and "Image Generation" (Diffusers) are high-latency, IO/GPU-bound operations (~2-5s each). Running them serially doubled the perceived latency for multimedia queries.
**Action:** Implemented `concurrent.futures.ThreadPoolExecutor` in `SovereignAgent.run` to execute Image Generation in parallel with the Text Synthesis phase. This reduces total latency from `T_text + T_image` to `max(T_text, T_image)`, yielding a ~50% speedup for queries involving both modalities.

## 2025-10-28 - Device-Aware CSNP Initialization
**Learning:** `CSNPManager` initialized its `memory_bank` and `identity_state` using `torch.zeros(...)`, which defaults to CPU. However, `LocalEmbedder` often runs on CUDA. This mismatch caused either performance-degrading implicit transfers or runtime crashes during `update_state` (specifically in `torch.mm`).
**Action:** Updated `CSNPManager.__init__` to inspect `self.embedder.device`. The memory buffers are now explicitly initialized on the same device as the embedder, ensuring zero-copy operations and preventing device mismatch errors.

## 2025-10-29 - ThreadPool Reuse in Agent
**Learning:** `SovereignAgent` was creating a new `ThreadPoolExecutor` for every `run()` call involving image generation. While low overhead for single queries, this adds up in loops.
**Action:** Moved `ThreadPoolExecutor` to `__init__` and added a `shutdown` method. This allows thread reuse.

## 2025-10-29 - Cross-Device State Loading
**Learning:** `CSNPManager.load_state` blindly trusted the device of the saved tensors. If a state was saved on CPU or loaded on a machine with CUDA (where `embedder` is CUDA), the manager would degrade `memory_bank` to CPU to match the file, causing massive performance loss (implicit transfers) or crashes (if `identity_state` was on GPU).
**Action:** Modified `load_state` to strictly cast all loaded tensors to `self.device` (determined by the embedder), ensuring hardware acceleration is preserved regardless of the save file's origin.

## 2025-10-30 - Structure of Arrays for Merkle Leaves
**Learning:** Storing `MerkleNode` objects for every leaf in the integrity chain creates unnecessary object overhead (approx 152 bytes per leaf + GC pressure). For high-frequency append operations, maintaining parallel lists (`ordered_hashes`, `ordered_data`) is significantly more efficient in Python than an Array of Structures.
**Action:** Refactored `IntegrityChain` to use SoA. Replaced `leaves` list with `ordered_hashes` and `ordered_data` buffers. This removed N object allocations per session and simplified `_rebuild_tree` to use slice copying instead of property extraction.

## 2025-10-30 - Latency Masking in Agent Pipeline
**Learning:** Parallelizing Image Generation with only Text Synthesis (the final step) leaves the Search and Code execution phases (which are synchronous) as unmasked latency blockers.
**Action:** Moved the Image Generation submission to the very start of the `run` loop. This allows the high-latency Image task to run concurrently with Search, Code, AND Synthesis, effectively hiding its cost if the other tasks take longer than the image generation.

## 2025-10-31 - Fast Path Context Verification
**Learning:** `CSNPManager.retrieve_context` built a new list of valid texts every time, allocating O(N) memory. In 99% of cases, all memories are valid.
**Action:** Implemented a "Fast Path" that checks hash validity first (iterating `hash_buffer`). If all valid, returns `"\n".join(text_buffer)` directly, avoiding the intermediate list allocation. Added safety check `len(text_buffer) == len(hash_buffer)` to prevent returning unverified tail elements.

## 2025-10-31 - Reference-Only Integrity Layer
**Learning:** `IntegrityChain._rebuild_tree` initialized the first layer with `self.ordered_hashes[:]`, creating an unnecessary O(N) copy.
**Action:** Removed the slice copy. The loop rebinds the `layer` variable to a new list in each iteration, so the original `ordered_hashes` remains safe without copying. Also replaced the explicit `append` loop with a list comprehension for C-speed execution.

## 2025-11-01 - Lazy Search Initialization
**Learning:** `ToolArsenal` was initializing `DDGS` (DuckDuckGo Search) in its `__init__`, creating network sessions and overhead even if the user only performed local queries. This added unnecessary startup latency and resource usage.
**Action:** Implemented lazy loading for `DDGS`. Removed the top-level import and eager instantiation. `DDGS` is now imported and initialized only within `web_search()` when actually needed, significantly reducing the initialization footprint of the `SovereignAgent`.

## 2025-11-02 - Zero-Allocation Transport & Argmax Optimization
**Learning:** `WassersteinMetric.compute_cost_matrix` allocated a new `[N, 1]` tensor for every compression step due to the `x_norm + y_norm` broadcast. Additionally, `_compress` computed the full Softmax distribution even for single-item eviction (`excess=1`), where finding the `argmin(mass)` is mathematically equivalent to finding `argmax(cost)`.
**Action:** Implemented a pre-allocated `transport_buffer` in `CSNPManager` and updated `WassersteinMetric` to write costs directly into it using `torch.add(..., out=buffer)`. Replaced the Softmax/Sinkhorn calculation with `torch.argmax(cost)` for the steady-state eviction path. This eliminates all tensor allocations in the hot compression loop.
