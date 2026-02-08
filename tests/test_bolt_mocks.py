import unittest
from unittest.mock import MagicMock
import sys
import os

# Mock dependencies
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from remember_me.math.transport import WassersteinMetric

class TestBoltMockVerification(unittest.TestCase):

    def test_compute_cost_matrix_calls_inplace(self):
        """
        Verify that compute_cost_matrix uses addmm_ and clamp_
        """
        metric = WassersteinMetric()

        # Setup Inputs
        x = MagicMock()
        y = MagicMock()
        x_norm = MagicMock()
        y_norm = MagicMock()

        # When x_norm + y_norm is called, it returns 'cost' mock
        # We need to simulate the broadcast add
        cost_mock = MagicMock()
        x_norm.__add__.return_value = cost_mock

        # Call method
        result = metric.compute_cost_matrix(x, y, x_norm, y_norm)

        # 1. Verify broadcast add happened
        x_norm.__add__.assert_called_with(y_norm)

        # 2. Verify addmm_ called on the RESULT of the add
        # cost.addmm_(x, y.t(), beta=1.0, alpha=-2.0)
        cost_mock.addmm_.assert_called()
        args, kwargs = cost_mock.addmm_.call_args

        # Check positional args: x, y.t()
        self.assertEqual(args[0], x)
        # We can't strictly check y.t() return value equality easily unless we mock y.t() return
        # But we verify it was called.

        self.assertEqual(kwargs['beta'], 1.0)
        self.assertEqual(kwargs['alpha'], -2.0)

        # 3. Verify clamp_ called
        cost_mock.clamp_.assert_called_with(min=0.0)

    def test_compute_transport_mass_calls_div_(self):
        """
        Verify that compute_transport_mass uses div_ for M=1 case
        """
        metric = WassersteinMetric()

        # Mock compute_cost_matrix to return a mock C
        C_mock = MagicMock()
        # We can't easily patch the method on the instance we just created because it's bound.
        # But we can patch the class or just mock the return of the internal call if we knew internals.
        # Better: Since compute_cost_matrix is called on self, we can mock it if we subclass or patch.

        with unittest.mock.patch.object(metric, 'compute_cost_matrix', return_value=C_mock):

            x = MagicMock() # Memory bank
            y = MagicMock() # Query

            # Setup M=1 case (y size(0) = 1)
            # query_state is 1st arg, memory_bank is 2nd arg in compute_transport_mass signature?
            # def compute_transport_mass(self, query_state, memory_bank, ...)

            y.size.return_value = 1

            # Call
            metric.compute_transport_mass(y, x)

            # Verify div_ called
            # C.div_(-epsilon)
            C_mock.div_.assert_called()

if __name__ == "__main__":
    unittest.main()
