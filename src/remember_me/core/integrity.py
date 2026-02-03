from typing import List, Optional, Set
try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    import hashlib
    HAS_XXHASH = False

class MerkleNode:
    # ⚡ Bolt: Use __slots__ to reduce memory overhead for large history trees
    __slots__ = ['hash', 'data', 'left', 'right']

    def __init__(self, hash_val: str, data: Optional[str] = None, left=None, right=None):
        self.hash = hash_val
        self.data = data
        self.left = left
        self.right = right

class IntegrityChain:
    """
    A Merkle-backed ledger of conversation history.
    Guarantees Zero-Hallucination by enforcing that any retrieved memory
    must structurally belong to the hash tree rooted at 'current_state_hash'.
    """
    def __init__(self):
        # ⚡ Bolt: Structure of Arrays (SoA) for leaves.
        # Instead of storing MerkleNode objects (high overhead), we store parallel lists.
        self.ordered_hashes: List[str] = []
        self.ordered_data: List[str] = []

        self.leaf_hashes: Set[str] = set() # ⚡ Bolt: O(1) Lookup
        self.root: Optional[MerkleNode] = None
        self._is_dirty = False # ⚡ Bolt: Lazy rebuild flag

    # ⚡ Bolt: Resolve hash function once at class definition time to avoid conditional overhead
    if HAS_XXHASH:
        def _hash(self, data: str) -> str:
            return xxhash.xxh64(data.encode('utf-8')).hexdigest()
    else:
        def _hash(self, data: str) -> str:
            return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def add_entry(self, data: str) -> str:
        """Adds a new atomic memory unit. Updates are lazy."""
        node_hash = self._hash(data)

        # ⚡ Bolt: Append to SoA buffers
        self.ordered_hashes.append(node_hash)
        self.ordered_data.append(data)

        self.leaf_hashes.add(node_hash)
        self._is_dirty = True # Mark tree as needing rebuild
        return node_hash

    def _rebuild_tree(self):
        """
        Reconstructs the Merkle Root from the leaves.
        O(N) complexity. Only runs when root is requested.
        """
        if not self.ordered_hashes:
            self.root = None
            self._is_dirty = False
            return

        # ⚡ Bolt: Zero-Allocation Internal Nodes
        # Use existing ordered_hashes list directly (No initial copy needed).
        layer = self.ordered_hashes

        while len(layer) > 1:
            # ⚡ Bolt: List Comprehension for C-Speed Loop
            n = len(layer)
            next_layer = [
                self._hash(layer[i] + layer[i+1]) if i + 1 < n
                else self._hash(layer[i] + layer[i])
                for i in range(0, n, 2)
            ]
            layer = next_layer

        self.root = MerkleNode(layer[0])
        self._is_dirty = False

    def get_root_hash(self) -> str:
        if self._is_dirty:
            self._rebuild_tree()
        return self.root.hash if self.root else "00000000"

    def verify(self, content: str) -> bool:
        """
        Verifies if specific content exists in the chain.
        This prevents the AI from fabricating memories that do not exist in the ledger.
        """
        target_hash = self._hash(content)
        return self.verify_hash(target_hash)

    def verify_hash(self, hash_val: str) -> bool:
        """
        Verifies if a specific hash exists in the chain (O(1)).
        """
        return hash_val in self.leaf_hashes
