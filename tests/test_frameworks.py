import pytest
from remember_me.core.frameworks import OISTruthBudget, HaiyueMicrocosm, VelocityPhysics

class TestOISTruthBudget:
    def test_initialization(self):
        ois = OISTruthBudget(100)
        assert ois.budget == 100
        assert ois.check() is True

    def test_deduction(self):
        ois = OISTruthBudget(100)
        ois.deduct(20, "Assumption")
        assert ois.budget == 80
        assert len(ois.history) == 1
        assert ois.history[0]["amount"] == 20
        assert ois.history[0]["reason"] == "Assumption"

    def test_depletion(self):
        ois = OISTruthBudget(10)
        ois.deduct(20, "Huge Error")
        assert ois.budget == -10
        assert ois.check() is False

class TestHaiyueMicrocosm:
    def test_simulation_prompt(self):
        haiyue = HaiyueMicrocosm()
        prompt = haiyue.formulate_simulation_prompt("Should I buy bitcoin?")
        assert "Input: 'Should I buy bitcoin?'" in prompt
        assert "[TRAJECTORY +1 (Optimistic)]" in prompt
        assert "[TRAJECTORY -1 (Pessimistic)]" in prompt
        assert "Convergence Point" in prompt

class TestVelocityPhysics:
    def test_hare_mode(self):
        vp = VelocityPhysics()
        signal = {"urgency": 0.8, "entropy": 0.1}
        assert vp.determine_mode(signal) == "WAR_SPEED"

    def test_turtle_mode(self):
        vp = VelocityPhysics()
        signal = {"urgency": 0.1, "entropy": 0.8}
        assert vp.determine_mode(signal) == "TURTLE_INTEGRITY"

    def test_sync_point(self):
        vp = VelocityPhysics()
        signal = {"urgency": 0.1, "entropy": 0.1}
        assert vp.determine_mode(signal) == "SYNC_POINT"
