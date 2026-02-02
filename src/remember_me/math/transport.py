import torch
import torch.nn.functional as F

class WassersteinMetric:
    """
    Implements Entropy-Regularized Optimal Transport (Sinkhorn Algorithm).

    Unlike Cosine Similarity (which measures angles), Wasserstein measures the
    'Work' required to transform the Memory Distribution into the Query Distribution.

    This allows us to quantify the 'Information Mass' of a memory fragment.
    """

    def __init__(self, epsilon: float = 0.1, max_iter: int = 100, tol: float = 1e-6):
        self.epsilon = epsilon # Entropic regularization (smoothness)
        self.max_iter = max_iter
        self.tol = tol

    def compute_cost_matrix(self, x: torch.Tensor, y: torch.Tensor, x_norm: torch.Tensor = None, y_norm: torch.Tensor = None) -> torch.Tensor:
        """
        Computes squared Euclidean distance cost matrix.
        C_ij = ||x_i - y_j||^2
        """
        # x: [N, D], y: [M, D] -> Cost: [N, M]
        # ⚡ Bolt: Use pre-computed x_norm if provided
        if x_norm is None:
            x_norm = (x**2).sum(1).view(-1, 1)

        # ⚡ Bolt: Use pre-computed y_norm if provided (Optimization for normalized queries)
        if y_norm is None:
            y_norm = (y**2).sum(1).view(1, -1)

        # ||x - y||^2 = ||x||^2 + ||y||^2 - 2<x, y>
        # ⚡ Bolt: Zero-Allocation Optimization
        # 1. Broadcast add allocates the 'cost' buffer [N, M]
        cost = x_norm + y_norm

        # 2. In-place addmm: cost = 1*cost - 2*(x @ y.t())
        # Eliminates intermediate tensors for matrix multiplication and subtraction
        cost.addmm_(x, y.t(), beta=1.0, alpha=-2.0)

        # 3. In-place clamp
        return cost.clamp_(min=0.0)

    def compute_transport_mass(self,
                             query_state: torch.Tensor,
                             memory_bank: torch.Tensor,
                             x_norms: torch.Tensor = None,
                             y_norms: torch.Tensor = None) -> torch.Tensor:
        """
        Computes the Optimal Transport Plan to determine how much 'mass'
        each memory contributes to the current query state.

        Args:
            query_state: [1, D] The current Coherent State vector.
            memory_bank: [N, D] The buffer of memory vectors.
            x_norms: [N, 1] Optional pre-computed norms for memory_bank.

        Returns:
            mass_scores: [N] Relevance score for each memory.
        """
        device = query_state.device
        N = memory_bank.size(0)
        M = query_state.size(0) # Usually 1

        if N == 0:
            return torch.tensor([])

        # Cost Matrix C [N, M]
        C = self.compute_cost_matrix(memory_bank, query_state, x_norm=x_norms, y_norm=y_norms)

        # OPTIMIZATION: If M=1 (Single Query), Sinkhorn degenerates to Softmax.
        # This is 5x faster and avoids numerical underflow in high dimensions.
        if M == 1:
            # We want mass distribution over N memories.
            # C is [N, 1]. -C/epsilon -> scaled logits.
            # ⚡ Bolt: In-place division to save allocation
            C.div_(-self.epsilon)
            # Softmax over dim=0 ensures sum(mass_scores) = 1.0
            return F.softmax(C, dim=0).flatten()

        # Gibbs Kernel K = exp(-C / epsilon)
        K = torch.exp(-C / self.epsilon)

        # Sinkhorn Iterations (Fixed Point)
        # Initialize marginals (uniform assumption)
        u = torch.ones(N, 1, device=device) / N
        v = torch.ones(M, 1, device=device) / M

        # Pre-compute transpose to avoid view creation in loop
        Kt = K.t()

        for _ in range(self.max_iter):
            u_prev = u.clone()

            # v = 1 / (K^T @ u)
            v = 1.0 / (torch.mm(Kt, u) + 1e-9)

            # u = 1 / (K @ v)
            u = 1.0 / (torch.mm(K, v) + 1e-9)

            if torch.max(torch.abs(u - u_prev)) < self.tol:
                break

        # Transport Plan Gamma = diag(u) @ K @ diag(v)
        # Gamma_i = u_i * (K @ v)_i
        Gamma = u * (K * v.t())

        # Sum mass transported FROM each memory index (row sum)
        mass_scores = Gamma.sum(dim=1)
        return mass_scores
