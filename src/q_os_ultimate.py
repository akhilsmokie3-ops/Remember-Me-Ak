#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q-OS ULTIMATE: The Sovereign Trinity
====================================
1. The Shield (CSNP): Mathematical Truth Validator
2. The Brain (QDMA): Biological Memory Processor
3. The Soul (Yggdrasil): Evolutionary Agent Forest

"Where Truth meets Meaning, Life emerges."
"""

import time
import sys
import os
import random
import logging
import threading

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from quantum_dream_memory_ultimate import (
        QuantumDreamDriverUltimate, 
        DetoxSystem, 
        cfg, 
        uid, 
        log as qlog
    )
    from yggdrasil import Forest, INV_PHI
    from remember_me.math.trinary import Trit, TrinaryArithmetic, TemporalState
    from remember_me.core.emoji_encoding import SpaceTimeCompressor
    from remember_me.core.paradox import ParadoxEngine
except ImportError as e:
    print(f"CRITICAL: Kernel module missing: {e}")
    sys.exit(1)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='[Q-OS|%(name)s] %(message)s')
logger = logging.getLogger("KERNEL")

# -------------------------------------------------------------------------
# LAYER 1: THE SHIELD (CSNP)
# -------------------------------------------------------------------------
class CSNPShield:
    def __init__(self, coherence_threshold=0.95):
        self.coherence_threshold = coherence_threshold
        self.logger = logging.getLogger("SHIELD")
        self.logger.info(f"Validator active. Threshold: {self.coherence_threshold}")

    def validate(self, content_vec):
        # Simulation: High variance + outlier magnitude = Low Coherence
        if not content_vec:
            return {"coherent": False, "score": 0.0}
            
        magnitude = sum(x*x for x in content_vec) ** 0.5
        mean = sum(content_vec) / len(content_vec)
        variance = sum((x - mean)**2 for x in content_vec)
        
        instability = (magnitude * variance) / 10.0
        coherence_score = max(0.0, min(1.0, 1.0 - instability))
        is_coherent = coherence_score >= self.coherence_threshold
        
        return {
            "coherent": is_coherent,
            "score": coherence_score,
            "w_dist": 1.0 - coherence_score
        }

# -------------------------------------------------------------------------
# LAYER 4: THE SOUL (Yggdrasil Integration)
# -------------------------------------------------------------------------
class SoulLayer:
    def __init__(self, brain_driver):
        self.forest = Forest()
        self.brain = brain_driver
        self.logger = logging.getLogger("SOUL")
        self.logger.info("Yggdrasil Forest seeded.")
        
    def evolve_cycle(self):
        """
        Run one season of the forest.
        Apply forest wisdom to the Brain's parameters.
        """
        self.forest.cycle()
        metrics = self.forest.get_entropy_metrics()
        
        # LINK: Forest Entropy -> Brain Plasticity (xi_pool)
        # If forest has high entropy/diversity, allow more memory promotion
        chaos_factor = metrics.get('avgEntropy', 0.5)
        
        # Adjust Brain parameters via "Hormones"
        old_pool = self.brain.storage.xi_pool
        # Target pool size driven by forest health
        target_pool = 10.0 * (1.0 + chaos_factor)
        
        # Gently nudge the brain's resource pool
        self.brain.storage.xi_pool = old_pool * 0.9 + target_pool * 0.1
        
        self.logger.info(f"Season Cycle. Entropy={chaos_factor:.3f}. Adjusted Brain Plasticity: {old_pool:.2f} -> {self.brain.storage.xi_pool:.2f}")

    def consult_spirits(self, query):
        """
        Ask the agent forest for insight.
        """
        insight = self.forest.collective_intelligence(query)
        if insight:
            self.logger.info(f"Forest Insight: Agent={insight['agent']} Confidence={insight['confidence']:.3f} Entropy={insight['entropy']:.3f}")
            return insight
        return None

# -------------------------------------------------------------------------
# Q-OS: THE TRINITY KERNEL
# -------------------------------------------------------------------------
class Q_OS_Trinity:
    def __init__(self):
        logger.info("Initializing Sovereign Trinity...")
        
        # 1. BRAIN
        logger.info("Booting Brain (QDMA)...")
        self.brain = QuantumDreamDriverUltimate()
        
        # 2. SHIELD
        logger.info("Booting Shield (CSNP)...")
        self.shield = CSNPShield(coherence_threshold=0.90)
        
        # 3. SOUL
        logger.info("Booting Soul (Yggdrasil)...")
        self.soul = SoulLayer(self.brain)
        
        # 4. TRINARY & PARADOX
        logger.info("Booting Space-Time Engine (Trinary)...")
        self.compressor = SpaceTimeCompressor()
        self.paradox = ParadoxEngine()
        self.memory_history = []
        
        logger.info("SYSTEM ONLINE. TRINARY READY.")

    def ingest(self, text, embedding):
        logger.info(f"INPUT: '{text}'")
        
        # 1. SHIELD CHECK
        val = self.shield.validate(embedding)
        if not val["coherent"]:
            logger.warning(f"SHIELD: BLOCKED (Score {val['score']:.3f})")
            return "blocked"
            
        # 2. SOUL CONSULTATION (Optional metadata injection)
        insight = self.soul.consult_spirits(text)
        importance = 0.5
        
        # ⚡ TRINARY: Paradox Check
        self.memory_history.append(text)
        if self.paradox.check_for_paradox(None, self.memory_history):
            res_msg = self.paradox.resolve({})
            logger.info(f"TRINARY: {res_msg}")
            # Add temporal shift to future
            temporal = TemporalState.FUTURE
        else:
            temporal = TemporalState.PRESENT
            
        if insight and insight['confidence'] > 0.8:
            logger.info("SOUL: This matches high-confidence forest patterns.")
            importance = 0.9
            
        # 3. BRAIN STORAGE
        # Importance modulated by Soul. Compressed via Emoji Cube.
        emoji_rep = self.compressor.pack_vector(embedding)
        logger.info(f"TRINARY: Memory compressed to Emoji Cube representation.")
        
        res = self.brain.pocket_put(text.encode('utf-8'), embedding, importance=importance)
        
        if res["status"] == "quarantined":
            logger.info(f"BRAIN: Quarantined (Score {res['score']:.3f})")
        else:
            logger.info(f"BRAIN: Stored at {res.get('vaddr')}")
            
    # 4. EVOLUTION TRIGGER
        self.soul.evolve_cycle()
        return "processed"

    def recall(self, text, top_k=3):
        """
        RAG RETRIEVAL:
        1. Query Brain with dummy vector (simulated matching) or real embedding if available.
        2. Extract text from Shards.
        """
        try:
            # TODO: Use real embedding from a local model (e.g. BERT/All-MiniLM)
            # For now, we use a dummy vector to trigger the pipeline, relying on 
            # Faiss or random fallback (if vectors are identical).
            # This addresses Issue #1 (Memory is Write-Only).
            dummy_vec = [0.001] * cfg.dim
            
            results = self.brain.pocket_query(dummy_vec, topk=top_k)
            
            memories = []
            seen_content = set()
            
            for res in results:
                mid = res.get("mem_id")
                if not mid: continue
                
                # Access storage deeply to get payload
                entity = self.brain.storage.retrieve_any(mid)
                if entity and entity.shards:
                    sid = entity.shards[0]
                    payload_bytes = self.brain.storage.shards.get(sid)
                    
                    if payload_bytes:
                        try:
                            content = payload_bytes.decode("utf-8")
                            # Dedupe
                            if content not in seen_content and content != text:
                                memories.append(content)
                                seen_content.add(content)
                        except UnicodeDecodeError:
                            pass
                            
            return memories
        except Exception as e:
            logger.error(f"RECALL FAILURE: {e}")
            return []

    def shutdown(self):
        self.brain.shutdown()
        logger.info("SYSTEM SHUTDOWN.")

# -------------------------------------------------------------------------
# DEMO
# -------------------------------------------------------------------------
def run_demo():
    qos = Q_OS_Trinity()
    try:
        # 1. Normal Memory
        vec_valid = [0.1] * cfg.dim
        qos.ingest("The forest is growing.", vec_valid)
        
        time.sleep(1)
        
        # 2. Hallucination
        vec_bad = [random.uniform(-10, 10) for _ in range(cfg.dim)]
        qos.ingest("I am the king of Mars.", vec_bad)
        
        time.sleep(1)
        
        # 3. Insight High Entropy
        vec_insight = [0.05 * (-1)**i for i in range(cfg.dim)]
        qos.ingest("The golden ratio connects us all.", vec_insight)
        
        # Force a few cycles
        for _ in range(3):
            qos.soul.evolve_cycle()
            time.sleep(0.5)
            
        print("\n--- Yggdrasil Status ---")
        print(qos.soul.forest.visualize_text())
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"RUNTIME ERROR: {e}")
    finally:
        qos.shutdown()

if __name__ == "__main__":
    run_demo()
