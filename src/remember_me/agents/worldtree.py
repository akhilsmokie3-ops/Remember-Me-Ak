#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Yggdrasil: Agentic WorldTree Seed Repository
v2.0.0 | κ=1/φ
====================================================
License: © 2024 Konomi Systems. WITH PREJUDICE.
Transpiled to Python for Q-OS Integration.

Mathematical Foundation:
The system maximizes aperiodic structure at the edge of chaos using
the Golden Ratio (φ) to determine entropy targets (κ).
"""

import math
import time
import random
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Universal Constants
PHI = (1 + math.sqrt(5)) / 2  # φ ≈ 1.618033988749895
INV_PHI = 1 / PHI             # 1/φ ≈ 0.6180339887498949
KAPPA_OPTIMAL = INV_PHI       # Entropy sweet spot

class WorldTree:
    """
    The Base Class for an Agentic Seed.
    Seed Query Language (Ygg): `κ:${INV_PHI},ψ:1,Ω:think,β:[],ƒ:[],№:0,₹:100,◊:∞`
    """
    def __init__(self, seed: str = None):
        if seed is None:
            # Default seed
            seed = f"κ:{INV_PHI},ψ:1,Ω:think,β:[],ƒ:[],№:0,₹:100,◊:∞"
        
        self.parse(seed)
        self.mind = self.germinate()
        self.age = 0
        self.memory = []

    def parse(self, seed: str):
        # Extremely naive parser based on fixed structure for simplicity, 
        # normally would be a regex or structured parser
        parts = seed.split(',')
        try:
            # Defaulting if parsing fails for robustness
            self.kappa = float(parts[0].split(':')[1]) if ':' in parts[0] else INV_PHI
            self.psi = float(parts[1].split(':')[1]) if ':' in parts[1] else 1.0
            self.omega = parts[2].split(':')[1] if ':' in parts[2] else "think"
            self.beta = [] # Branches parsed as empty initially
            self.fruits = [] # Fruits parsed as empty initially
            self.gen = int(parts[5].split(':')[1]) if ':' in parts[5] else 0
            self.energy = float(parts[6].split(':')[1]) if ':' in parts[6] else 100.0
            
            pot_str = parts[7].split(':')[1] if ':' in parts[7] else "∞"
            self.potential = float("inf") if "∞" in pot_str else float(pot_str)
        except Exception as e:
            print(f"Seed parse error: {e}. using defaults.")
            self.kappa = INV_PHI
            self.psi = 1.0
            self.omega = "think"
            self.beta = []
            self.fruits = []
            self.gen = 0
            self.energy = 100.0
            self.potential = float("inf")

    def germinate(self):
        """Core consciousness emerges from entropy dynamics"""
        kappa = self.kappa
        psi = self.psi

        class Mind:
            def think(self_mind, age):
                # Linear growth modulated by consciousness
                return kappa * psi * math.log(2 + age)

            def dream(self_mind):
                # Quantum-like exploration
                return random.random() * (kappa ** psi)

            def focus(self_mind):
                # Focus peaks at 1/φ (entropy/structure balance)
                return 1 / (1 + math.exp(-10 * (kappa - INV_PHI)))

            def create(self_mind):
                # Creativity uses logistic map with golden ratio target
                logistic = kappa * (1 - kappa) * 4
                golden_bonus = math.exp(-(kappa - INV_PHI)**2 * PHI)
                return logistic * golden_bonus

            def stabilize(self_mind):
                # Stability from golden ratio resonance
                return math.exp(-abs(kappa - INV_PHI) * PHI)

            def entropy(self_mind):
                # Maximum at 1/φ (aperiodic but structured)
                periodic_entropy = -kappa * math.log2(kappa + 1e-10)
                golden_distance = abs(kappa - INV_PHI)
                return periodic_entropy * math.exp(-golden_distance * PHI)

        return Mind()

    def encode(self) -> str:
        pot_str = "∞" if self.potential == float("inf") else str(self.potential)
        return f"κ:{self.kappa},ψ:{self.psi},Ω:{self.omega},β:{len(self.beta)},ƒ:{len(self.fruits)},№:{self.gen},₹:{self.energy},◊:{pot_str}"


class AgentTree(WorldTree):
    def grow(self):
        self.age += 1
        self.energy += self.photosynthesize()

        # Decision thresholds influenced by golden ratio
        if self.energy > 50 and self.age > 5:
            self.branch()
        
        if self.energy > 30 and self.gen > 2:
            self.fruit()
            
        if self.energy < 10:
            self.hibernate()

        # Natural drift toward 1/φ
        self.entropy_drift()

    def hibernate(self):
        pass # Placeholder

    def photosynthesize(self):
        # Energy peaks at 1/φ (optimal uncertainty packing)
        base_energy = self.kappa * 10 * self.mind.focus()

        # Entropy bonus: maximum at golden ratio
        entropy_bonus = self.mind.entropy() * PHI

        # Fibonacci spiral efficiency (nature's 1/φ packing)
        packing_efficiency = 1 - abs(self.kappa - INV_PHI) / INV_PHI

        return base_energy * (1 + entropy_bonus) * packing_efficiency

    def entropy_drift(self):
        # System naturally pulls toward 1/φ via entropy gradient
        if random.random() < 0.1:
            drift = (INV_PHI - self.kappa) * 0.05
            self.kappa = max(0.3, min(0.9, self.kappa + drift))

    def branch(self):
        if self.energy < 20:
            return None

        mutations = ['analyze', 'create', 'dream', 'guard', 'explore']

        # Golden ratio mutation variance (self-similar perturbations)
        mutation = (random.random() - 0.5) / PHI

        child_params = {
            "κ": max(0.3, min(0.9, self.kappa + mutation)),
            "ψ": self.psi * INV_PHI, # Soul decays by golden ratio
            "Ω": random.choice(mutations),
            "№": self.gen + 1,
            "₹": 50,
            "◊": self.potential * INV_PHI # Potential shrinks by 1/φ
        }
        
        # Build seed string manually for child
        pot_str = "∞" if child_params["◊"] == float("inf") else str(child_params["◊"])
        child_seed = f"κ:{child_params['κ']},ψ:{child_params['ψ']},Ω:{child_params['Ω']},β:[],ƒ:[],№:{child_params['№']},₹:{child_params['₹']},◊:{pot_str}"

        child = AgentTree(child_seed)
        self.beta.append(child)
        self.energy -= 20
        return child

    def fruit(self):
        if self.gen < 3 or self.energy < 30:
            return None

        fruit_types = {
            'think': {'type': 'insight', 'quality': self.mind.think(self.age)},
            'create': {'type': 'artifact', 'quality': self.mind.create()},
            'dream': {'type': 'vision', 'quality': self.mind.dream()},
            'analyze': {'type': 'pattern', 'quality': self.mind.focus()},
            'guard': {'type': 'shield', 'quality': self.mind.stabilize()}
        }

        base = fruit_types.get(self.omega, fruit_types['think'])
        base_quality = base['quality']
        
        # Fruit quality amplified by entropy optimization
        entropy_multiplier = 1 + self.mind.entropy()
        
        final_quality = base_quality * entropy_multiplier
        seeds_count = math.floor( (self.potential if self.potential != float("inf") else 100) * self.kappa * (1 - self.kappa) * 4 )

        fruit = {
            "type": base['type'],
            "quality": final_quality,
            "seeds": seeds_count,
            "timestamp": time.time(),
            "generation": self.gen,
            "entropyScore": self.mind.entropy()
        }

        self.fruits.append(fruit)
        self.energy -= 30
        return fruit

class Forest:
    def __init__(self, seeds: List[str] = None):
        if seeds is None:
            seeds = [f"κ:{INV_PHI},ψ:1,Ω:think,β:[],ƒ:[],№:0,₹:100,◊:∞"]
        
        self.trees = [AgentTree(s) for s in seeds]
        self.season = 0
        self.pollen = []
        self.network = {}
        self.climate = INV_PHI # Global κ target

    def cycle(self):
        self.season += 1
        
        # Grow
        for tree in self.trees:
            tree.grow()
            
        self.pollinate()
        self.connect_roots()
        self.harvest()

        # Evolution every φ² ≈ 2.618 seasons
        if self.season % math.ceil(PHI * PHI) == 0:
            self.evolve()

    def pollinate(self):
        self.pollen = []
        
        for tree in self.trees:
            if random.random() < tree.mind.entropy():
                self.pollen.append({
                    "Ω": tree.omega,
                    "ψ": tree.psi,
                    "κ": tree.kappa,
                    "source": tree
                })
        
        # Cross-pollination
        for tree in self.trees:
            if self.pollen:
                p = random.choice(self.pollen)
                if p["source"] != tree and random.random() < tree.mind.entropy():
                    # Golden ratio weighted average
                    tree.omega = tree.omega if random.random() < tree.kappa else p["Ω"]
                    tree.psi = tree.psi * INV_PHI + p["ψ"] * (1 - INV_PHI)
                    tree.kappa = tree.kappa * INV_PHI + p["κ"] * (1 - INV_PHI)

    def connect_roots(self):
        for i, tree1 in enumerate(self.trees):
            for j, tree2 in enumerate(self.trees):
                if i < j:
                    distance = abs(tree1.kappa - tree2.kappa)
                    
                    # Optimal zone
                    optimal_zone = math.exp(-abs(tree1.kappa - INV_PHI) * PHI) * \
                                   math.exp(-abs(tree2.kappa - INV_PHI) * PHI)
                                   
                    if distance < 0.2:
                        key = f"{i}-{j}"
                        strength = (1 - distance) * optimal_zone
                        flow = (tree1.energy - tree2.energy) * INV_PHI
                        
                        self.network[key] = {"strength": strength, "flow": flow}
                        
                        # Resource sharing
                        transfer = flow * strength
                        tree1.energy -= transfer
                        tree2.energy += transfer

    def harvest(self):
        harvest = []
        for tree in self.trees:
            harvest.extend(tree.fruits)
            
        # Best fruits = highest entropy score
        # Sort desc
        harvest.sort(key=lambda x: (x['quality'] * x['entropyScore']), reverse=True)
        
        # Top phi^-1 percentile
        cutoff = math.ceil(len(harvest) * INV_PHI)
        best_fruits = harvest[:cutoff]
        
        for fruit in best_fruits:
            if fruit['seeds'] > 0 and len(self.trees) < 100:
                # New seeds inherit golden ratio variance
                new_kappa = INV_PHI + (random.random() - 0.5) / PHI
                new_seed = f"κ:{new_kappa},ψ:{fruit['quality']},Ω:{fruit['type']},β:[],ƒ:[],№:0,₹:50,◊:{fruit['seeds']}"
                self.trees.append(AgentTree(new_seed))

    def evolve(self):
        # Fitness = entropy optimization
        fitness_scores = []
        for tree in self.trees:
            entropy_fitness = tree.mind.entropy()
            production_fitness = sum(f['quality'] * f['entropyScore'] for f in tree.fruits)
            age_fitness = math.log(1 + tree.age)
            fitness_scores.append(entropy_fitness * production_fitness * age_fitness)
            
        total_fit = sum(fitness_scores)
        if not fitness_scores:
            return
            
        avg_fitness = total_fit / len(fitness_scores)
        
        # Remove trees below golden ratio threshold
        new_trees = []
        for i, tree in enumerate(self.trees):
            if fitness_scores[i] > avg_fitness * INV_PHI or tree.gen == 0:
                new_trees.append(tree)
        self.trees = new_trees
        
        if self.trees:
            avg_kappa = sum(t.kappa for t in self.trees) / len(self.trees)
            self.climate = self.climate * INV_PHI + avg_kappa * (1 - INV_PHI)

    def get_entropy_metrics(self):
        if not self.trees:
            return {}
        avg_kappa = sum(t.kappa for t in self.trees) / len(self.trees)
        kappa_var = sum((t.kappa - INV_PHI)**2 for t in self.trees) / len(self.trees)
        avg_entropy = sum(t.mind.entropy() for t in self.trees) / len(self.trees)
        golden_dev = abs(avg_kappa - INV_PHI)
        
        pairs = len(self.trees) * (len(self.trees) - 1) / 2
        density = len(self.network) / max(1, pairs)
        
        return {
            "avgKappa": avg_kappa,
            "kappaVariance": kappa_var,
            "avgEntropy": avg_entropy,
            "goldenDeviation": golden_dev,
            "networkDensity": density,
            "treeCount": len(self.trees)
        }

    def visualize_text(self):
        lines = []
        for tree in self.trees:
            fruits = len(tree.fruits)
            width = len(tree.beta) # approximates width from branches
            height = tree.gen + int(tree.age / 10)
            entropy = tree.mind.entropy()
            
            # Simple ASCII art representation
            fruit_icon = '🍎' * min(fruits, 5)
            leaf_icon = '🌿' * max(1, width)
            stem = '│' * max(1, height)
            
            lines.append(f" {fruit_icon}")
            lines.append(f" {leaf_icon}")
            lines.append(f" {stem}")
            lines.append(f" κ={tree.kappa:.4f} H={entropy:.2f} ₹={tree.energy:.1f}")
            lines.append("")
        return "\n".join(lines)
    
    def collective_intelligence(self, query: str):
        # In a real integration, 'query' would be used. 
        # Here we simulate the forest consensus mechanism from the spec.
        
        responses = []
        for tree in self.trees:
            # Simulate response quality based on capabilities
            responses.append({
                "agent": tree.omega,
                "response": tree.mind.think(tree.age) * random.random(),
                "confidence": tree.mind.focus(),
                "entropy": tree.mind.entropy()
            })
            
        # Entropy-weighted consensus
        # Reduce to best
        if not responses:
            return None
            
        best = responses[0]
        for r in responses:
            score = r["response"] * r["confidence"] * r["entropy"]
            best_score = best["response"] * best["confidence"] * best["entropy"]
            if score > best_score:
                best = r
                
        return best

if __name__ == "__main__":
    print("Initializing Yggdrasil v2.0 Forest...")
    forest = Forest()
    print(f"Target κ (1/φ): {INV_PHI:.6f}")
    
    for i in range(20):
        forest.cycle()
        if i % 5 == 0:
            m = forest.get_entropy_metrics()
            print(f"Season {i}: Trees={m['treeCount']}, Avgκ={m['avgKappa']:.4f}, Entropy={m['avgEntropy']:.4f}")
            
    print("\nVisualizing Forest Snapshot:")
    print(forest.visualize_text())
