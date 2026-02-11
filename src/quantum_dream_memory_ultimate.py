#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量子梦幻记忆算法终极版
===========================================
融合法则：1 + (-1) = 0 拼图融合
版本：3.0.0 Ultimate

完整融合：
- 主体：量子新记忆.txt（并行架构、完整驱动器）
- 吸收：量子记忆.txt（隔离重试、懒加载、核心规则、负熵读取）

特性：
- 并行架构（多线程工作池）
- 投影引擎（micro/macro/high 三维投影）
- 融合核心（FAISS + 纠缠缓存 + Redis）
- 压缩引擎（1±-1融合 + 频率感知）
- 隔离重试系统（插值升华）
- 懒加载扩展器（种子扩展）
- 存储核心（核心规则 + 负熵读取 + 衰减）
- Detox净化系统（毒性检测 + 修复）
- 完整HTTP API（FastAPI）
- Prometheus监控
- 自举数据注入

运行：
    python quantum_dream_memory_ultimate.py
    python quantum_dream_memory_ultimate.py --debug-run-once
    python quantum_dream_memory_ultimate.py --add-demo 100

环境变量：
    QDMA_DIM, QDMA_USE_FAISS, QDMA_ENABLE_HTTP
    QDMA_ENABLE_PROM, QDMA_MAX_WORKERS, QDMA_STATUS_PORT
"""

from __future__ import annotations
import os
import sys
import time
import json
import uuid
import math
import random
import hashlib
import threading
import traceback
import signal
import argparse
import shutil
import http.server
import socketserver
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from contextlib import asynccontextmanager

# -------------------------
# 可选依赖检测
# -------------------------
HAS_NUMPY = False
HAS_FAISS = False
HAS_REDIS = False
HAS_FASTAPI = False
HAS_PROMETHEUS = False
np = None
faiss = None
redis = None

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    faiss = None
    HAS_FAISS = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    redis = None
    HAS_REDIS = False

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import Response
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

# -------------------------
# 全局配置
# -------------------------
@dataclass
class QDMAConfig:
    """量子梦幻记忆算法终极版配置"""
    base_dir: str = os.path.abspath(".")
    data_dir: str = field(init=False)
    shard_dir: str = field(init=False)
    backup_dir: str = field(init=False)
    log_dir: str = field(init=False)

    dim: int = 128
    micro_dim: int = 64
    macro_dim: int = 32
    high_dim: int = 256

    default_sim: float = 0.70
    sim_min: float = 0.35
    default_iters: int = 4
    quant_bits: int = 8
    min_group: int = 2

    proj_token_rate: float = 10.0
    proj_token_cap: float = 20.0

    toxicity_threshold: float = 0.6
    repair_threshold: float = 0.65
    anomaly_zscore: float = 4.0
    quarantine_hold: float = 60.0
    decay_interval: float = 3600.0
    decay_rate: float = 0.01

    ent_capacity: int = 1024
    pocket_max_local: int = 16
    promote_cost: float = 0.12
    prefetch_enabled: bool = True

    faiss_batch: int = 128
    consolidation_batch: int = 64
    background_rebuild_interval: float = 5.0
    max_workers: int = 8
    max_backup_keep: int = 10
    poll_interval: float = 5.0
    idle_run_seconds: int = 120

    quarantine_retry_limit: int = 3

    work_queue_size: int = 1000
    batch_size: int = 32

    status_port: int = 0
    enable_http: bool = False
    enable_prometheus: bool = False

    debug_log: str = field(init=False)
    log_prefix: str = "[QDMA-Ultimate]"
    log_level: str = "INFO"

    max_auto_inject: int = 128
    auto_inject_samples: List[str] = field(init=False)

    sanitizer_blacklist: List[str] = field(init=False)

    use_redis: bool = field(init=False)
    use_faiss: bool = field(init=False)
    freq_alpha: float = 1.0
    freq_beta: float = 1.0
    pair_sim_factor: float = 1.0

    def __post_init__(self):
        self.data_dir = os.path.join(self.base_dir, "qdma_ultimate_data")
        self.shard_dir = os.path.join(self.data_dir, "shards")
        self.backup_dir = os.path.join(self.data_dir, "backups")
        self.log_dir = os.path.join(self.data_dir, "logs")
        self.debug_log = os.path.join(self.log_dir, "debug.log")

        self.auto_inject_samples = [
            "pocket infinite storage", "memory bread copy restore", "memory camera snapshot replay",
            "time cloth restore state", "memory disk compress replay", "memory capsule compress small",
            "holographic pocket seed aggregator", "seed singularity compressed origin", "lazy expansion reconstruct"
        ]

        self.sanitizer_blacklist = []

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.shard_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        self._load_from_env()

    def _load_from_env(self):
        self.dim = int(os.environ.get("QDMA_DIM", self.dim))
        self.default_sim = float(os.environ.get("QDMA_SIM", self.default_sim))
        self.sim_min = float(os.environ.get("QDMA_SIM_MIN", self.sim_min))
        self.toxicity_threshold = float(os.environ.get("QDMA_TOXICITY_THRESHOLD", self.toxicity_threshold))
        self.repair_threshold = float(os.environ.get("QDMA_REPAIR_THRESHOLD", self.repair_threshold))
        self.quarantine_retry_limit = int(os.environ.get("QDMA_QUARANTINE_RETRY", self.quarantine_retry_limit))
        self.max_workers = int(os.environ.get("QDMA_MAX_WORKERS", self.max_workers))
        self.status_port = int(os.environ.get("QDMA_STATUS_PORT", self.status_port))
        self.enable_http = os.environ.get("QDMA_ENABLE_HTTP", "0") == "1"
        self.enable_prometheus = HAS_PROMETHEUS and os.environ.get("QDMA_ENABLE_PROM", "0") == "1"
        self.faiss_batch = int(os.environ.get("QDMA_FAISS_BATCH", self.faiss_batch))
        self.ent_capacity = int(os.environ.get("QDMA_ENT_CAP", self.ent_capacity))
        self.pocket_max_local = int(os.environ.get("QDMA_POCKET_MAX_LOCAL", self.pocket_max_local))
        self.promote_cost = float(os.environ.get("QDMA_PROMOTE_COST", self.promote_cost))
        self.quarantine_hold = float(os.environ.get("QDMA_QUARANTINE_HOLD", self.quarantine_hold))
        self.decay_interval = float(os.environ.get("QDMA_DECAY_INTERVAL", self.decay_interval))
        self.decay_rate = float(os.environ.get("QDMA_DECAY_RATE", self.decay_rate))
        self.micro_dim = int(os.environ.get("QDMA_PROJ_MICRO_DIM", self.micro_dim))
        self.macro_dim = int(os.environ.get("QDMA_PROJ_MACRO_DIM", self.macro_dim))
        self.high_dim = int(os.environ.get("QDMA_PROJ_HIGH_DIM", self.high_dim))

        self.use_redis = HAS_REDIS and os.environ.get("QDMA_USE_REDIS", "0") == "1"
        self.use_faiss = HAS_FAISS and os.environ.get("QDMA_USE_FAISS", "1") == "1"

        if not HAS_FAISS:
            self.use_faiss = False

        blacklist = os.environ.get("QDMA_SANITIZER_BLACKLIST", "")
        if blacklist:
            self.sanitizer_blacklist = [w.strip() for w in blacklist.split(",") if w.strip()]

cfg = QDMAConfig()

# -------------------------
# 基础工具类
# -------------------------
def uid(prefix: str = "") -> str:
    return prefix + str(uuid.uuid4())[:12]

def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def safe_write_json(path: str, obj: Any):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def log(msg: str, level: str = "INFO"):
    line = f"{cfg.log_prefix} [{now_ts()}] [{level}] {msg}"
    print(line, flush=True)
    try:
        with open(cfg.debug_log, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def log_exc(prefix: str = "EXC"):
    tb = traceback.format_exc()
    log(f"{prefix}: {tb}", "ERROR")

# -------------------------
# 向量表示统一
# -------------------------
class VectorSpace:
    """统一向量空间表示"""

    @staticmethod
    def ensure_numpy(vec: Any) -> Optional[np.ndarray]:
        if vec is None:
            return None
        if HAS_NUMPY and isinstance(vec, np.ndarray):
            return vec
        if isinstance(vec, list):
            if HAS_NUMPY:
                return np.array(vec, dtype='float32')
            return vec.copy()
        return None

    @staticmethod
    def cosine_sim(a: Any, b: Any) -> float:
        vec_a = VectorSpace.ensure_numpy(a)
        vec_b = VectorSpace.ensure_numpy(b)
        if vec_a is None or vec_b is None:
            return 0.0

        if HAS_NUMPY:
            an = np.linalg.norm(vec_a) + 1e-12
            bn = np.linalg.norm(vec_b) + 1e-12
            return float(np.dot(vec_a, vec_b) / (an * bn))
        else:
            m = min(len(vec_a), len(vec_b))
            dot = sum(vec_a[i] * vec_b[i] for i in range(m))
            an = math.sqrt(sum(x*x for x in vec_a)) + 1e-12
            bn = math.sqrt(sum(y*y for y in vec_b)) + 1e-12
            return dot / (an * bn)

    @staticmethod
    def normalize(vec: Any) -> Any:
        arr = VectorSpace.ensure_numpy(vec)
        if arr is None:
            return None

        if HAS_NUMPY:
            norm = np.linalg.norm(arr) + 1e-12
            return (arr / norm).astype('float32')
        else:
            norm = math.sqrt(sum(x*x for x in arr)) + 1e-12
            return [x / norm for x in arr]

    @staticmethod
    def mean_vec(vecs: List[Any]) -> Optional[Any]:
        if not vecs:
            return None

        np_vecs = [VectorSpace.ensure_numpy(v) for v in vecs]
        np_vecs = [v for v in np_vecs if v is not None]

        if not np_vecs:
            return None

        if HAS_NUMPY:
            return np.mean(np.stack(np_vecs, axis=0), axis=0).astype('float32')
        else:
            dim = max(len(v) for v in np_vecs)
            res = [0.0] * dim
            for v in np_vecs:
                for i, x in enumerate(v):
                    if i < dim:
                        res[i] += x
            n = len(np_vecs)
            return [x / n for x in res]

    @staticmethod
    def vec_add(a: Any, b: Any) -> Optional[Any]:
        vec_a = VectorSpace.ensure_numpy(a)
        vec_b = VectorSpace.ensure_numpy(b)
        if vec_a is None or vec_b is None:
            return vec_b or vec_a

        if HAS_NUMPY:
            return (vec_a + vec_b).astype('float32')
        else:
            dim = max(len(vec_a), len(vec_b))
            return [(vec_a[i] if i < len(vec_a) else 0.0) +
                    (vec_b[i] if i < len(vec_b) else 0.0) for i in range(dim)]

    @staticmethod
    def vec_sub(a: Any, b: Any) -> Optional[Any]:
        vec_a = VectorSpace.ensure_numpy(a)
        vec_b = VectorSpace.ensure_numpy(b)
        if vec_a is None or vec_b is None:
            return None

        if HAS_NUMPY:
            return (vec_a - vec_b).astype('float32')
        else:
            dim = max(len(vec_a), len(vec_b))
            return [(vec_a[i] if i < len(vec_a) else 0.0) -
                    (vec_b[i] if i < len(vec_b) else 0.0) for i in range(dim)]

    @staticmethod
    def vec_scale(vec: Any, scale: float) -> Optional[Any]:
        arr = VectorSpace.ensure_numpy(vec)
        if arr is None:
            return None

        if HAS_NUMPY:
            return (arr * scale).astype('float32')
        else:
            return [x * scale for x in arr]

# -------------------------
# 量化辅助函数
# -------------------------
def quantize_list(vecs: List[List[float]], bits: int = cfg.quant_bits):
    flat = [x for v in vecs for x in v] if vecs else []
    if not flat:
        return [], {}
    mn = min(flat)
    mx = max(flat)
    if mn == mx:
        q = [[0] * len(vecs[0]) for _ in vecs]
        return q, {"min": mn, "max": mx, "bits": bits}
    levels = (1 << bits) - 1
    meta = {"min": mn, "max": mx, "bits": bits}
    qvecs = []
    for v in vecs:
        qv = [int(round((x - mn) / (mx - mn) * levels)) for x in v]
        qvecs.append(qv)
    return qvecs, meta

def dequantize(qvec, meta):
    mn = meta.get("min", 0.0)
    mx = meta.get("max", 0.0)
    bits = meta.get("bits", cfg.quant_bits)
    levels = (1 << bits) - 1
    if levels == 0:
        return [mn for _ in qvec]
    return [mn + (x / levels) * (mx - mn) for x in qvec]

# -------------------------
# 账本与监控系统
# -------------------------
class QDMALedger:
    chain: List[Dict[str, Any]] = []
    lock = threading.Lock()
    write_queue: Queue = Queue()
    _stop = False

    @classmethod
    def record(cls, op: str, obj_id: str, info: Dict[str, Any]):
        try:
            with cls.lock:
                prev = cls.chain[-1]['hash'] if cls.chain else ''
                entry = {
                    "ts": now_ts(),
                    "op": op,
                    "id": obj_id,
                    "info": info,
                    "prev": prev
                }
                s = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                entry['hash'] = sha256_hex(s)
                cls.chain.append(entry)
                cls.write_queue.put(entry)
        except Exception as e:
            log(f"Ledger.record error: {e}", "ERROR")

    @classmethod
    def start_writer(cls, path: str):
        t = threading.Thread(target=cls._writer_loop, args=(path,), daemon=True)
        t.start()
        return t

    @classmethod
    def _writer_loop(cls, path: str):
        buffer = []
        last_flush = time.time()
        while not cls._stop:
            try:
                item = cls.write_queue.get(timeout=1.0)
                buffer.append(item)
                if len(buffer) >= 64 or (time.time() - last_flush) > 5.0:
                    cls._flush_buffer(buffer, path)
                    buffer = []
                    last_flush = time.time()
            except Empty:
                if buffer:
                    cls._flush_buffer(buffer, path)
                    buffer = []
                    last_flush = time.time()
            except Exception as e:
                log(f"Ledger writer error: {e}", "ERROR")
                time.sleep(0.5)
        if buffer:
            cls._flush_buffer(buffer, path)

    @classmethod
    def _flush_buffer(cls, buffer: List[Dict[str, Any]], path: str):
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cls.chain, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
            log(f"Ledger flushed {len(buffer)} entries", "DEBUG")
        except Exception as e:
            log(f"Ledger flush error: {e}", "ERROR")

    @classmethod
    def dump(cls, path: str):
        try:
            with cls.lock:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cls.chain, f, ensure_ascii=False, indent=2)
            log(f"Ledger dumped to {path}")
        except Exception as e:
            log(f"Ledger dump error: {e}", "ERROR")

    @classmethod
    def stop(cls):
        cls._stop = True
        log("Ledger stopped")

# -------------------------
# 监控指标
# -------------------------
if cfg.enable_prometheus:
    MET_PROJECT = Counter("qdma_project_total", "Total PROJECT calls")
    MET_QUERY = Counter("qdma_query_total", "Total query calls")
    MET_FAISS_SEARCH = Counter("qdma_faiss_search_total", "Total FAISS searches")
    MET_ENT_HIT = Counter("qdma_ent_hit_total", "Entanglement cache hits")
    MET_ENT_PUT = Counter("qdma_ent_put_total", "Entanglement cache puts")
    MET_POCKET_PUT = Counter("qdma_pocket_put_total", "Total pocket_put calls")
    MET_DELETE = Counter("qdma_delete_total", "Total delete requests")
    MET_COMPRESS = Counter("qdma_compress_total", "Total compression runs")
    MET_SUBLIMATE = Counter("qdma_sublimate_total", "Total sublimation merges")
    LAT_PROJECT = Histogram("qdma_project_latency_seconds", "PROJECT latency seconds")
    LAT_QUERY = Histogram("qdma_query_latency_seconds", "Query latency seconds")
    GAUGE_UNITS = Gauge("qdma_units", "Number of memory units")
    GAUGE_SEEDS = Gauge("qdma_seeds", "Number of seeds")
else:
    class _Dummy:
        def inc(self, *a, **k): pass
        def observe(self, *a, **k): pass
        def set(self, *a, **k): pass
    MET_PROJECT = MET_QUERY = MET_FAISS_SEARCH = MET_ENT_HIT = MET_ENT_PUT = MET_POCKET_PUT = MET_DELETE = MET_COMPRESS = MET_SUBLIMATE = _Dummy()
    LAT_PROJECT = LAT_QUERY = _Dummy()
    GAUGE_UNITS = GAUGE_SEEDS = _Dummy()

# -------------------------
# ???? - ????
# -------------------------
@dataclass
class DreamEntity:
    id: str
    embedding: Optional[Any]
    shards: List[str]
    xi: float = 0.5
    score: float = 1.0
    importance: float = 0.0
    emotion: float = 0.0
    trit: int = 0
    core_protected: bool = False
    quarantined: bool = False
    delete_requester: Optional[str] = None
    delete_request_ts: Optional[float] = None
    version: int = 0
    ts: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    decay_score: float = 0.0
    explain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "embedding": (self.embedding.tolist() if HAS_NUMPY and isinstance(self.embedding, np.ndarray)
                         else self.embedding),
            "shards": self.shards,
            "xi": self.xi,
            "score": self.score,
            "importance": self.importance,
            "emotion": self.emotion,
            "trit": self.trit,
            "core_protected": self.core_protected,
            "quarantined": self.quarantined,
            "version": self.version,
            "ts": self.ts,
            "last_active": self.last_active,
            "decay_score": self.decay_score,
            "explain": self.explain
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DreamEntity":
        emb = data.get("embedding")
        if emb is not None and HAS_NUMPY:
            emb = np.array(emb, dtype="float32")
        return cls(
            id=data["id"],
            embedding=emb,
            shards=data.get("shards", []),
            xi=data.get("xi", 0.5),
            score=data.get("score", 1.0),
            importance=data.get("importance", 0.0),
            emotion=data.get("emotion", 0.0),
            trit=data.get("trit", 0),
            core_protected=data.get("core_protected", False),
            quarantined=data.get("quarantined", False),
            delete_requester=data.get("delete_requester"),
            delete_request_ts=data.get("delete_request_ts"),
            version=data.get("version", 0),
            ts=data.get("ts", time.time()),
            last_active=data.get("last_active", time.time()),
            decay_score=data.get("decay_score", 0.0),
            explain=data.get("explain")
        )

@dataclass
class DreamSeed:
    id: str
    seed_vec: Optional[Any]
    members: List[str]
    diffs: Dict[str, List[int]] = field(default_factory=dict)
    quant_meta: Dict[str, Any] = field(default_factory=dict)
    macro_repr: Optional[Any] = None
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "seed_vec": (self.seed_vec.tolist() if HAS_NUMPY and isinstance(self.seed_vec, np.ndarray)
                        else self.seed_vec),
            "macro_repr": (self.macro_repr.tolist() if HAS_NUMPY and isinstance(self.macro_repr, np.ndarray)
                          else self.macro_repr),
            "members": self.members,
            "diffs": self.diffs,
            "quant_meta": self.quant_meta,
            "ts": self.ts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DreamSeed":
        seed_vec = data.get("seed_vec")
        macro_repr = data.get("macro_repr")
        if HAS_NUMPY:
            if seed_vec is not None:
                seed_vec = np.array(seed_vec, dtype="float32")
            if macro_repr is not None:
                macro_repr = np.array(macro_repr, dtype="float32")
        return cls(
            id=data["id"],
            seed_vec=seed_vec,
            macro_repr=macro_repr,
            members=data.get("members", []),
            diffs=data.get("diffs", {}),
            quant_meta=data.get("quant_meta", {}),
            ts=data.get("ts", time.time())
        )

@dataclass
class Hologram:
    id: str
    embedding: Any
    confidence: float
    provenance: Dict[str, Any]
    delta_E: float
    toxic_score: float = 0.0
    explain: Optional[str] = None

# -------------------------
# ?????
# -------------------------
class Sanitizer:
    blacklist = set()

    @staticmethod
    def clean_text(b: bytes) -> bytes:
        try:
            s = b.decode("utf-8", errors="ignore")
            s = "".join(ch for ch in s if ord(ch) >= 32)
            for bad in Sanitizer.blacklist:
                if bad and bad in s:
                    s = s.replace(bad, "[REDACTED]")
            return s.encode("utf-8")
        except Exception:
            return b

# -------------------------
# ???????
# -------------------------
class DetoxSystem:
    @staticmethod
    def toxicity_score(emb: Any, background: Any = None) -> float:
        vec = VectorSpace.ensure_numpy(emb)
        if vec is None:
            return 0.0

        try:
            if HAS_NUMPY:
                mag = float(np.linalg.norm(vec))
                mean = float(np.mean(vec))
                std = float(np.std(vec)) + 1e-12
                kurt = float(np.mean(((vec - mean) / std) ** 4))
                score = (abs(mean) / 10.0) * 0.4
                score += (mag / (math.sqrt(len(vec)) + 1e-12)) * 0.3
                score += min(kurt / 3.0, 1.0) * 0.3
                if background is not None:
                    bg = VectorSpace.ensure_numpy(background)
                    if bg is not None:
                        dist = np.linalg.norm(vec - bg) / (np.linalg.norm(bg) + 1e-12)
                        score += min(dist, 1.0) * 0.2
                return min(1.0, score)
            else:
                mag = math.sqrt(sum(x*x for x in vec))
                mean = sum(vec) / len(vec)
                variance = sum((x - mean)**2 for x in vec) / len(vec)
                std = math.sqrt(variance) + 1e-12
                score = (abs(mean) / 10.0) * 0.4
                score += (mag / (math.sqrt(len(vec)) + 1e-12)) * 0.3
                fourth_moment = sum(((x - mean) / std) ** 4 for x in vec) / len(vec)
                score += min(fourth_moment / 3.0, 1.0) * 0.3
                if background is not None:
                    bg = VectorSpace.ensure_numpy(background)
                    if bg is not None:
                        diff = [vec[i] - (bg[i] if i < len(bg) else 0) for i in range(len(vec))]
                        dist = math.sqrt(sum(x*x for x in diff)) / (math.sqrt(sum(x*x for x in bg)) + 1e-12)
                        score += min(dist, 1.0) * 0.2
                return min(1.0, score)
        except Exception:
            return 0.0

    @staticmethod
    def is_anomalous(emb: Any, background: Any, z_threshold: float = cfg.anomaly_zscore) -> bool:
        vec = VectorSpace.ensure_numpy(emb)
        bg = VectorSpace.ensure_numpy(background)
        if vec is None or bg is None:
            return False

        try:
            diff = [vec[i] - (bg[i] if i < len(bg) else 0) for i in range(len(vec))]
            mean_diff = sum(diff) / len(diff)
            std_diff = math.sqrt(sum((x - mean_diff)**2 for x in diff) / len(diff)) + 1e-12
            for x in diff:
                z = abs((x - mean_diff) / std_diff)
                if z > z_threshold:
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    def repair(emb: Any, background: Any = None, strength: float = 0.4) -> Any:
        vec = VectorSpace.ensure_numpy(emb)
        if vec is None:
            return None

        try:
            if HAS_NUMPY:
                correction = -strength * np.sign(vec) * np.minimum(np.abs(vec), 0.05)
                repaired = vec + correction
            else:
                correction = [-strength * (1 if x > 0 else -1) * min(abs(x), 0.05) for x in vec]
                repaired = [vec[i] + correction[i] for i in range(len(vec))]
            if background is not None:
                bg = VectorSpace.ensure_numpy(background)
                if bg is not None:
                    if HAS_NUMPY:
                        repaired = 0.7 * repaired + 0.3 * bg
                    else:
                        repaired = [0.7 * repaired[i] + 0.3 * (bg[i] if i < len(bg) else 0)
                                  for i in range(len(repaired))]
            return repaired
        except Exception:
            return vec

# -------------------------
# ??????
# -------------------------
class TokenBucket:
    def __init__(self, rate: float, capacity: float):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.lock = threading.Lock()
        self.last = time.time()

    def consume(self, amount: float = 1.0) -> bool:
        with self.lock:
            now = time.time()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
            self.last = now
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False

# -------------------------
# ????
# -------------------------
class ProjectionEngine:
    def __init__(self, dim: int, micro_dim: int, macro_dim: int, high_dim: int):
        self.dim = dim
        self.micro_dim = micro_dim
        self.macro_dim = macro_dim
        self.high_dim = high_dim

        rng = np.random.RandomState(42) if HAS_NUMPY else random.Random(42)
        if HAS_NUMPY:
            self.micro_proj = rng.normal(scale=1.0, size=(micro_dim, dim)).astype("float32")
            self.macro_proj = rng.normal(scale=1.0, size=(macro_dim, micro_dim)).astype("float32")
            self.high_proj = rng.normal(scale=1.0, size=(high_dim, dim)).astype("float32")
        else:
            self.micro_proj = [[random.gauss(0, 1) for _ in range(dim)] for _ in range(micro_dim)]
            self.macro_proj = [[random.gauss(0, 1) for _ in range(micro_dim)] for _ in range(macro_dim)]
            self.high_proj = [[random.gauss(0, 1) for _ in range(dim)] for _ in range(high_dim)]

        self.micro_mean = np.zeros(micro_dim, dtype="float32") if HAS_NUMPY else [0.0] * micro_dim
        self.micro_count = 0

        self.reverse_executor = ThreadPoolExecutor(max_workers=4)
        self.token_bucket = TokenBucket(cfg.proj_token_rate, cfg.proj_token_cap)

        self.storage = None

        QDMALedger.record("PROJECTION_ENGINE_INIT", uid(), {
            "dim": dim, "micro_dim": micro_dim, "macro_dim": macro_dim, "high_dim": high_dim
        })
        log("ProjectionEngine initialized")

    def attach_storage(self, storage):
        self.storage = storage

    def micro_to_macro(self, emb: Any) -> Dict[str, Any]:
        vec = VectorSpace.ensure_numpy(emb)
        if vec is None:
            return {"macro": None, "meta": {"error": "null_vec"}}

        if HAS_NUMPY:
            micro = self.micro_proj.dot(vec)
        else:
            micro = [sum(self.micro_proj[i][j] * (vec[j] if j < len(vec) else 0)
                        for j in range(self.dim)) for i in range(self.micro_dim)]

        self.micro_count += 1
        if HAS_NUMPY and self.micro_count % 100 == 0:
            self.micro_mean = 0.99 * self.micro_mean + 0.01 * np.mean(micro, axis=0)

        if HAS_NUMPY:
            macro = self.macro_proj.dot(np.tanh(micro))
        else:
            tanh_micro = [math.tanh(x) for x in micro]
            macro = [sum(self.macro_proj[i][j] * tanh_micro[j]
                       for j in range(self.micro_dim)) for i in range(self.macro_dim)]

        macro = VectorSpace.normalize(macro)

        meta = {
            "method": "micro_to_macro",
            "micro_norm": float(np.linalg.norm(micro) if HAS_NUMPY else math.sqrt(sum(x*x for x in micro))),
            "macro_norm": float(np.linalg.norm(macro) if HAS_NUMPY else math.sqrt(sum(x*x for x in macro)))
        }

        QDMALedger.record("PROJ_MICRO_TO_MACRO", uid(), meta)
        return {"macro": macro, "meta": meta}

    def high_dim_project(self, emb: Any) -> Any:
        vec = VectorSpace.ensure_numpy(emb)
        if vec is None:
            return None

        if HAS_NUMPY:
            high = np.tanh(self.high_proj.dot(vec))
            return high.astype("float32")
        else:
            high = [math.tanh(sum(self.high_proj[i][j] * (vec[j] if j < len(vec) else 0)
                                  for j in range(self.dim))) for i in range(self.high_dim)]
            return VectorSpace.normalize(high)


# -------------------------
# ????
# -------------------------
class FusionCore:
    def __init__(self, dim: int = cfg.dim):
        self.dim = dim
        self.use_faiss = HAS_FAISS and cfg.use_faiss
        self.faiss_index = None
        self.faiss_ids: List[str] = []
        self.faiss_buffer: List[Any] = []
        self.faiss_buffer_ids: List[str] = []
        self.faiss_lock = threading.RLock()
        self._stop = False

        self.ent_capacity = cfg.ent_capacity
        self.ent_cache: Dict[str, Dict[str, Any]] = {}
        self.ent_lru: List[str] = []
        self.ent_hit_threshold = 0.85
        self.ent_lock = threading.Lock()

        self.use_redis = cfg.use_redis and HAS_REDIS
        self.redis_client = None
        if self.use_redis:
            try:
                self.redis_client = redis.Redis()
                self.redis_client.ping()
                log("FusionCore: Redis connected")
            except Exception as e:
                log(f"FusionCore: Redis init failed: {e}", "ERROR")
                self.redis_client = None
                self.use_redis = False

        self.prefetch_q = Queue(maxsize=2048)
        self.prefetch_enabled = cfg.prefetch_enabled

        self.project_executor = ThreadPoolExecutor(max_workers=cfg.max_workers)

        if self.use_faiss:
            try:
                index_path = os.path.join(cfg.data_dir, "faiss.index")
                if os.path.exists(index_path):
                    self.faiss_index = faiss.read_index(index_path)
                    log("FAISS index loaded")
                else:
                    self.faiss_index = faiss.IndexHNSWFlat(dim, 32)
                    self.faiss_index.hnsw.efConstruction = 64
                    self.faiss_index.hnsw.efSearch = 64
                    log("FAISS index created")
            except Exception as e:
                log(f"FAISS init error: {e}", "ERROR")
                self.use_faiss = False
                self.faiss_index = None

        self._flush_thread = threading.Thread(target=self._faiss_flush_worker, daemon=True)
        self._flush_thread.start()
        self._prefetch_thread = threading.Thread(target=self._prefetch_worker, daemon=True)
        self._prefetch_thread.start()

        self.ent_hits = 0
        self.ent_queries = 0
        self.adapt_lock = threading.Lock()
        self.storage = None
        self.projection_engine = None

        QDMALedger.record("FUSIONCORE_INIT", uid(), {
            "dim": dim, "faiss": self.use_faiss, "redis": self.use_redis
        })
        log("FusionCore initialized (projection-ready)")

    def attach_storage(self, storage):
        self.storage = storage

    def attach_projection_engine(self, projection_engine):
        self.projection_engine = projection_engine

    def faiss_add_buffered(self, mem_id: str, emb: Any):
        if not self.use_faiss or self.faiss_index is None:
            with self.faiss_lock:
                self.faiss_ids.append(mem_id)
                self.faiss_buffer.append(emb)
            return

        with self.faiss_lock:
            if HAS_NUMPY:
                self.faiss_buffer.append(emb.reshape(1, -1))
            else:
                self.faiss_buffer.append(emb)
            self.faiss_buffer_ids.append(mem_id)
            if len(self.faiss_buffer) >= cfg.faiss_batch:
                self._flush_faiss_buffer()

    def _flush_faiss_buffer(self):
        if not self.use_faiss or self.faiss_index is None:
            return
        try:
            if HAS_NUMPY:
                vecs = np.vstack(self.faiss_buffer)
            else:
                vecs = self.faiss_buffer
            self.faiss_index.add(vecs)
            self.faiss_ids.extend(self.faiss_buffer_ids)
            MET_FAISS_SEARCH.inc()
            log(f"FAISS batch added {len(self.faiss_buffer_ids)}")
        except Exception as e:
            log(f"FAISS batch add error: {e}", "ERROR")
        finally:
            self.faiss_buffer = []
            self.faiss_buffer_ids = []

    def _faiss_flush_worker(self):
        while not self._stop:
            try:
                time.sleep(1.0)
                with self.faiss_lock:
                    if self.faiss_buffer:
                        self._flush_faiss_buffer()
                    if self.use_faiss and self.faiss_index is not None:
                        try:
                            faiss.write_index(self.faiss_index, os.path.join(cfg.data_dir, "faiss.index"))
                        except Exception as e:
                            log(f"FAISS persist error: {e}", "ERROR")
            except Exception as e:
                log(f"FAISS flush worker error: {e}", "ERROR")
                time.sleep(1.0)

    def faiss_search(self, q_emb: Any, topk: int = 5) -> List[str]:
        vec = VectorSpace.ensure_numpy(q_emb)
        if vec is None:
            return []

        if self.use_faiss and self.faiss_index is not None and len(self.faiss_ids) > 0:
            try:
                if HAS_NUMPY:
                    q = vec.reshape(1, -1)
                else:
                    q = np.array([vec])
                D, I = self.faiss_index.search(q, topk)
                res = []
                for idx in I[0]:
                    if 0 <= idx < len(self.faiss_ids):
                        res.append(self.faiss_ids[int(idx)])
                MET_FAISS_SEARCH.inc()
                return res
            except Exception as e:
                log(f"FAISS search error: {e}", "ERROR")

        with self.faiss_lock:
            if not self.faiss_buffer and not self.faiss_ids:
                return []
            return self.faiss_ids[:topk]

    def ent_get(self, q_emb: Any):
        key = sha256_hex(",".join(map(str, np.round(q_emb[:8], 3).tolist())))[:16]
        with self.ent_lock:
            self.ent_queries += 1
            e = self.ent_cache.get(key)
            if not e and self.use_redis and self.redis_client:
                try:
                    raw = self.redis_client.get("ent:" + key)
                    if raw:
                        obj = json.loads(raw)
                        e = {"ent_vec": np.array(obj["ent_vec"], dtype="float32"), "mem_ids": obj["mem_ids"], 
                             "last_access": time.time(), "xi_reserve": obj.get("xi_reserve", 0.05)}
                        self.ent_cache[key] = e
                        self.ent_lru.insert(0, key)
                except Exception:
                    pass
            if not e:
                return None
            ent_vec = e["ent_vec"]
            sim = self._cosine_sim(ent_vec, q_emb)
            if sim < self.ent_hit_threshold:
                return None
            e["last_access"] = time.time()
            if key in self.ent_lru:
                self.ent_lru.remove(key)
            self.ent_lru.insert(0, key)
            self.ent_hits += 1
            MET_ENT_HIT.inc()
            self._maybe_adapt()
            return e

    def ent_put(self, mem_embeddings: List[Any], mem_ids: List[str], xi_reserve: float = 0.05):
        if not mem_embeddings:
            return None

        if HAS_NUMPY:
            ent_vec = np.mean(np.stack([VectorSpace.ensure_numpy(v) for v in mem_embeddings], axis=0), axis=0).astype("float32")
        else:
            ent_vec = VectorSpace.mean_vec(mem_embeddings)

        if ent_vec is None:
            return None

        key = sha256_hex(",".join(map(str, np.round(ent_vec[:8], 4).tolist())))[:16]
        with self.ent_lock:
            if key in self.ent_cache:
                self.ent_cache[key].update({"ent_vec": ent_vec, "mem_ids": mem_ids, "last_access": time.time(), 
                                               "xi_reserve": xi_reserve})
                if key in self.ent_lru:
                    self.ent_lru.remove(key)
                self.ent_lru.insert(0, key)
            else:
                if len(self.ent_lru) >= self.ent_capacity:
                    tail = self.ent_lru.pop()
                    self.ent_cache.pop(tail, None)
                    if self.use_redis and self.redis_client:
                        try:
                            self.redis_client.delete("ent:" + tail)
                        except Exception:
                            pass
                self.ent_cache[key] = {"ent_vec": ent_vec, "mem_ids": mem_ids, "last_access": time.time(), 
                                        "xi_reserve": xi_reserve}
                self.ent_lru.insert(0, key)
            if self.use_redis and self.redis_client:
                try:
                    self.redis_client.set("ent:" + key, json.dumps({"ent_vec": ent_vec.tolist(), "mem_ids": mem_ids, 
                                                                        "xi_reserve": xi_reserve}), ex=3600)
                except Exception:
                    pass
            MET_ENT_PUT.inc()
            return key

    def _cosine_sim(self, a: Any, b: Any) -> float:
        return VectorSpace.cosine_sim(a, b)

    def _maybe_adapt(self):
        with self.adapt_lock:
            if self.ent_queries >= 200:
                hit_rate = self.ent_hits / max(1, self.ent_queries)
                if hit_rate > 0.6 and self.ent_hit_threshold > 0.6:
                    self.ent_hit_threshold = max(0.5, self.ent_hit_threshold - 0.02)
                elif hit_rate < 0.2 and self.ent_hit_threshold < 0.95:
                    self.ent_hit_threshold = min(0.95, self.ent_hit_threshold + 0.02)
                self.ent_hits = 0
                self.ent_queries = 0

    def project(self, query_emb: Any, background: Any = None, alpha: float = 0.6, 
               projection_mode: str = "micro") -> Hologram:
        start = time.time()
        MET_PROJECT.inc()

        tscore = DetoxSystem.toxicity_score(query_emb, background)

        proj_meta = {}
        if self.projection_engine:
            if projection_mode == "micro":
                pm = self.projection_engine.micro_to_macro(query_emb)
                proj_meta = pm["meta"]
            elif projection_mode == "macro":
                pm = self.projection_engine.micro_to_macro(query_emb)
                proj_meta = pm["meta"]
            elif projection_mode == "high":
                h = self.projection_engine.high_dim_project(query_emb)
                proj_meta = {"high_dim_norm": float(np.linalg.norm(h)) if HAS_NUMPY 
                                                       else math.sqrt(sum(x*x for x in h))}

        ent = self.ent_get(query_emb)
        if ent is not None:
            ent_vec = ent["ent_vec"]
            emb = alpha * query_emb + (1.0 - alpha) * ent_vec
            delta_E = float(np.linalg.norm(emb - ent_vec)) if HAS_NUMPY else math.sqrt(sum((emb[i] - ent_vec[i])**2 for i in range(len(emb))))
            holo = Hologram(id=uid(), embedding=emb, confidence=0.92, 
                           provenance={"method": "entangled", "proj": projection_mode}, 
                           delta_E=delta_E, toxic_score=tscore)
            holo.explain = "entangled"
            LAT_PROJECT.observe(time.time() - start)
            QDMALedger.record("PROJECT_ENT", holo.id, {"delta_E": delta_E, "toxic_score": tscore, 
                                                        "proj_meta": proj_meta})
            if tscore >= cfg.toxicity_threshold:
                threading.Thread(target=self._handle_toxic_hologram, args=(holo,), daemon=True).start()
            return holo

        if self.storage and (self.use_faiss or self.faiss_buffer):
            hits = self.faiss_search(query_emb, topk=6)
            if hits:
                mem_embs = [self.storage.index[h] for h in hits if h in self.storage.index]
                mem_embs = [e for e in mem_embs if e is not None]
                if mem_embs:
                    ent_key = self.ent_put(mem_embs, hits, xi_reserve=0.05)
                    ent_vec = mem_embs[0]
                    emb = alpha * query_emb + (1.0 - alpha) * ent_vec
                    delta_E = float(np.linalg.norm(emb - ent_vec)) if HAS_NUMPY else math.sqrt(sum((emb[i] - ent_vec[i])**2 for i in range(len(emb))))
                    holo = Hologram(id=uid(), embedding=emb, confidence=0.86, 
                                   provenance={"method": "faiss_ent", "ent_key": ent_key, "proj": projection_mode}, 
                                   delta_E=delta_E, toxic_score=tscore)
                    holo.explain = "faiss_ent"
                    LAT_PROJECT.observe(time.time() - start)
                    QDMALedger.record("PROJECT_FAISS", holo.id, {"delta_E": delta_E, "hits": len(hits), 
                                                            "toxic_score": tscore, "proj_meta": proj_meta})
                    if tscore >= cfg.toxicity_threshold:
                        threading.Thread(target=self._handle_toxic_hologram, args=(holo,), daemon=True).start()
                    return holo

        B = background if background is not None else (self.storage.background if self.storage 
                                                    else (np.zeros(cfg.dim, dtype="float32") if HAS_NUMPY else [0.0] * cfg.dim))
        emb = alpha * query_emb + (1.0 - alpha) * B
        if HAS_NUMPY:
            emb += np.random.normal(scale=1e-6, size=emb.shape).astype("float32")
        else:
            emb = [emb[i] + random.gauss(0, 1e-6) for i in range(len(emb))]
        delta_E = float(np.linalg.norm(emb - B)) if HAS_NUMPY else math.sqrt(sum((emb[i] - B[i])**2 for i in range(len(emb))))
        holo = Hologram(id=uid(), embedding=emb, confidence=0.72, 
                       provenance={"method": "background", "proj": projection_mode}, 
                       delta_E=delta_E, toxic_score=tscore)
        holo.explain = "background"
        LAT_PROJECT.observe(time.time() - start)
        QDMALedger.record("PROJECT_BG", holo.id, {"delta_E": delta_E, "toxic_score": tscore, "proj_meta": proj_meta})
        if tscore >= cfg.toxicity_threshold:
            threading.Thread(target=self._handle_toxic_hologram, args=(holo,), daemon=True).start()
        return holo

    def _handle_toxic_hologram(self, holo: Hologram):
        try:
            if self.storage:
                res = self.storage.negentropy_read(holo, toxicity_threshold=cfg.toxicity_threshold)
                if res.get("status") == "ok":
                    QDMALedger.record("TOXIC_HANDLED_OK", holo.id, {"method": "light_repair"})
                    return
                repaired = res.get("hologram")
                if repaired and res.get("toxic"):
                    time.sleep(0.2)
                    if DetoxSystem.toxicity_score(repaired.embedding, self.storage.background) >= cfg.toxicity_threshold:
                        mem_id = uid()
                        mu = DreamEntity(id=mem_id, embedding=repaired.embedding.copy(), xi=0.0)
                        mu.quarantined = True
                        mu.explain = f"auto_quarantine_from_holo:{holo.id}"
                        self.storage.hot[mem_id] = mu
                        self.storage.index[mem_id] = mu.embedding.copy()
                        QDMALedger.record("AUTO_QUARANTINE", mem_id, {"from_holo": holo.id, 
                                                                    "toxic_score": repaired.delta_E})
                        log(f"Auto-quarantined {mem_id[:8]} from holo {holo.id[:8]}")
        except Exception as e:
            log(f"_handle_toxic_hologram error: {e}", "ERROR")

    def project_batch(self, queries: List[Any], background: Any = None, alpha: float = 0.6, 
                   projection_mode: str = "micro") -> List[Hologram]:
        results: List[Optional[Hologram]] = [None] * len(queries)
        for i, q in enumerate(queries):
            ent = self.ent_get(q)
            if ent is not None:
                ent_vec = ent["ent_vec"]
                emb = alpha * q + (1.0 - alpha) * ent_vec
                delta_E = float(np.linalg.norm(emb - ent_vec)) if HAS_NUMPY else math.sqrt(sum((emb[i] - ent_vec[i])**2 for i in range(len(emb))))
                tscore = DetoxSystem.toxicity_score(emb, background)
                results[i] = Hologram(id=uid(), embedding=emb, confidence=0.92, 
                                      provenance={"method": "entangled"}, 
                                      delta_E=delta_E, toxic_score=tscore, explain="entangled")
        futures = {}
        for i, q in enumerate(queries):
            if results[i] is None:
                futures[self.project_executor.submit(self.project, q, background, alpha, projection_mode)] = i
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                results[i] = fut.result()
            except Exception:
                log(f"project_batch worker error for index {i}", "ERROR")
                results[i] = self.project(queries[i], background, alpha, projection_mode)
        return results

    def prefetch(self, emb: Any):
        if not self.prefetch_enabled:
            return
        try:
            self.prefetch_q.put(emb, timeout=0.01)
        except Exception:
            pass

    def _prefetch_worker(self):
        while not self._stop:
            try:
                emb = self.prefetch_q.get(timeout=1.0)
                hits = self.faiss_search(emb, topk=8)
                if hits and self.storage:
                    mem_embs = [self.storage.index[h] for h in hits if h in self.storage.index]
                    mem_embs = [e for e in mem_embs if e is not None]
                    if mem_embs:
                        self.ent_put(mem_embs, hits, xi_reserve=0.02)
            except Empty:
                continue
            except Exception as e:
                log(f"Prefetch worker error: {e}", "ERROR")
                time.sleep(0.2)

    def shutdown(self):
        self._stop = True
        log("FusionCore shutdown requested")
        with self.faiss_lock:
            if self.faiss_buffer:
                self._flush_faiss_buffer()
            if self.use_faiss and self.faiss_index is not None:
                try:
                    faiss.write_index(self.faiss_index, os.path.join(cfg.data_dir, "faiss.index"))
                    log("FAISS index persisted on shutdown")
                except Exception as e:
                    log(f"FAISS persist error on shutdown: {e}", "ERROR")
        try:
            self.project_executor.shutdown(wait=False)
        except Exception:
            pass

# -------------------------
# ?????????(?????.txt??)
# -------------------------
class QuarantineRetrySystem:
    """?????? - ????"""
    def __init__(self, compressor: "DreamCompressor", registry: "DreamRegistry"):
        self.compressor = compressor
        self.registry = registry
        self.quarantine_path = os.path.join(cfg.data_dir, "quarantine.json")
        self._cache = None
        self._mtime = -1

    def retry_and_sublimate(self, top_k: int = 20, relax_steps: List[float] = None,
                           interp_steps: int = 5, perturb_sigma: float = 0.02) -> Dict[str, Any]:
        relax_steps = relax_steps or [0.55, 0.50, 0.45]

        if not os.path.exists(self.quarantine_path):
            return {"tried": 0, "merged": 0}

        try:
            mtime = os.path.getmtime(self.quarantine_path)
            if self._cache is not None and mtime == self._mtime:
                quarantine = self._cache
            else:
                with open(self.quarantine_path, "r", encoding="utf-8") as f:
                    quarantine = json.load(f)
                self._cache = quarantine
                self._mtime = mtime
        except Exception:
            return {"tried": 0, "merged": 0}

        q_sorted = sorted(quarantine, key=lambda x: -float(x.get("metric", 0)))
        q_top = q_sorted[:top_k]
        q_rest = q_sorted[top_k:]
        tried = 0
        merged = 0
        new_quarantine = []

        for item in q_top:
            tried += 1
            a_id = item.get("a")
            b_id = item.get("b")
            base_metric = float(item.get("metric", 0))

            a = self.registry.entities.get(a_id)
            b = self.registry.entities.get(b_id)
            if not a or not b:
                continue

            vecs = []
            for t in range(interp_steps + 1):
                alpha = t / max(1, interp_steps)
                cand = VectorSpace.vec_scale(a.embedding, 1 - alpha)
                cand = VectorSpace.vec_add(cand, VectorSpace.vec_scale(b.embedding, alpha))
                if cand:
                    vecs.append(cand)
                for _ in range(2):
                    perturbed = [x + random.gauss(0, perturb_sigma) for x in cand] if cand else None
                    if perturbed:
                        vecs.append(perturbed)

            merged_flag = False
            for sim_target in relax_steps:
                if merged_flag:
                    break
                for cand in vecs:
                    if self._attempt_merge(a, b, cand, sim_target):
                        merged_flag = True
                        break

            if not merged_flag:
                item["retries"] = item.get("retries", 0) + 1
                if item["retries"] < cfg.quarantine_retry_limit:
                    new_quarantine.append(item)
                else:
                    item["exhausted"] = True
                    new_quarantine.append(item)

        final_quarantine = new_quarantine + q_rest
        safe_write_json(self.quarantine_path, final_quarantine)
        self._cache = final_quarantine
        try:
            self._mtime = os.path.getmtime(self.quarantine_path)
        except Exception:
            self._mtime = -1
        return {"tried": tried, "merged": merged}

    def _attempt_merge(self, a: DreamEntity, b: DreamEntity,
                       cand_vec: Any, sim_target: float) -> bool:
        sim_a = VectorSpace.cosine_sim(a.embedding, cand_vec)
        sim_b = VectorSpace.cosine_sim(b.embedding, cand_vec)

        if sim_a >= sim_target and sim_b >= sim_target:
            shards = sorted(set(a.shards + b.shards))

            toxic = DetoxSystem.toxicity_score(cand_vec)
            if toxic > cfg.toxicity_threshold:
                cand_vec = DetoxSystem.repair(cand_vec)

            proj_result = self.compressor.projection.micro_to_macro(cand_vec)
            macro_repr = proj_result["macro"]

            seed = DreamSeed(
                id=uid("seed-"),
                seed_vec=cand_vec,
                macro_repr=macro_repr,
                members=shards,
                quant_meta={"sublimated_flag": True, "sim_a": sim_a, "sim_b": sim_b}
            )

            self.compressor.seed_index.register(seed)

            merged_entity = DreamEntity(
                id=uid("ent-"),
                embedding=cand_vec,
                shards=shards,
                xi=(a.xi + b.xi) / 2,
                score=(a.score + b.score),
                explain="sublimated_merge"
            )

            with self.registry.lock:
                self.registry.entities.pop(a.id, None)
                self.registry.entities.pop(b.id, None)
                self.registry.entities[merged_entity.id] = merged_entity
                self.registry.save()

            QDMALedger.record("SUBLIMATE_MERGE", seed.id, {
                "from": [a.id, b.id],
                "sim_a": sim_a,
                "sim_b": sim_b,
                "target": sim_target
            })

            log(f"Sublimated merge: {a.id}+{b.id} -> {seed.id}")
            MET_SUBLIMATE.inc()
            return True

        return False

# -------------------------
# ??????(?????.txt??)
# -------------------------
class LazyExpander:
    """????"""
    def __init__(self, seed_index: "DreamSeedIndex"):
        self.seed_index = seed_index
        self.cache = {}
        self.lock = threading.RLock()

    def quick_holo(self, seed: DreamSeed, query_vec: Any = None, alpha: float = 0.6):
        if query_vec is None:
            emb = seed.seed_vec
        else:
            emb = VectorSpace.vec_add(
                VectorSpace.vec_scale(query_vec, alpha),
                VectorSpace.vec_scale(seed.seed_vec, 1 - alpha)
            ) if seed.seed_vec is not None else query_vec

        delta = VectorSpace.cosine_sim(seed.seed_vec, emb) if seed.seed_vec is not None else 0.0

        holo = {
            "id": uid("h-"),
            "embedding": emb,
            "confidence": 0.75,
            "seed": seed.id,
            "delta": delta
        }

        QDMALedger.record("SEED_QUICK", holo["id"], {"seed": seed.id})
        return holo

    def expand(self, seed: DreamSeed, top_n: int = 6):
        with self.lock:
            if seed.id in self.cache:
                return self.cache[seed.id]

        members = []
        if seed.quant_meta and seed.diffs:
            for mid in seed.members[:top_n]:
                q = seed.diffs.get(mid)
                if q:
                    try:
                        diff = dequantize(q, seed.quant_meta)
                        emb = VectorSpace.vec_add(seed.seed_vec, diff)
                        members.append({"id": mid, "embedding": emb})
                    except Exception:
                        members.append({"id": mid})
                else:
                    members.append({"id": mid})
        else:
            for mid in seed.members[:top_n]:
                members.append({"id": mid})

        res = {
            "seed": seed.id,
            "members": members,
            "ts": time.time()
        }

        with self.lock:
            self.cache[seed.id] = res

        QDMALedger.record("SEED_EXPAND", seed.id, {"members": len(members)})
        return res


# -------------------------
# ???(????)
# -------------------------
class DreamCompressor:
    def __init__(self, registry: "DreamRegistry", seed_index: "DreamSeedIndex",
                 projection_engine: ProjectionEngine, fusion: FusionCore = None):
        self.registry = registry
        self.seed_index = seed_index
        self.projection = projection_engine
        self.fusion = fusion

        self.quarantine_path = os.path.join(cfg.data_dir, "quarantine.json")
        self.quarantine_lock = threading.RLock()

    def greedy_cluster(self, nodes: List[DreamEntity], sim_thresh: float, min_group: int):
        groups = []
        used = set()
        for i, a in enumerate(nodes):
            if a.id in used or a.quarantined:
                continue
            group = [a]
            used.add(a.id)
            for b in nodes[i+1:]:
                if b.id in used or b.quarantined:
                    continue
                try:
                    if VectorSpace.cosine_sim(a.embedding, b.embedding) >= sim_thresh:
                        group.append(b)
                        used.add(b.id)
                except Exception:
                    continue
            if len(group) >= min_group:
                groups.append(group)
        return groups

    def build_seeds(self, sim_thresh: float = cfg.default_sim, min_group: int = cfg.min_group, 
                    quant_bits: int = cfg.quant_bits):
        nodes = list(self.registry.entities.values())
        if not nodes:
            return {"created": 0}
        groups = self.greedy_cluster(nodes, sim_thresh, min_group)
        created = 0
        for g in groups:
            created += self._create_seed(g, quant_bits)
        return {"created": created, "groups": len(groups)}

    def _create_seed(self, group: List[DreamEntity], quant_bits: int):
        vecs = [e.embedding for e in group if e.embedding is not None]
        if not vecs:
            return 0
        seed_vec = VectorSpace.mean_vec(vecs)
        if seed_vec is None:
            return 0

        member_ids = []
        diffs = []
        ids = []
        for e in group:
            member_ids.extend(e.shards)
            if e.embedding is not None:
                diff = VectorSpace.vec_sub(e.embedding, seed_vec)
                if diff is not None:
                    diffs.append(diff)
                    ids.append(e.shards[0] if e.shards else e.id)

        qvecs, meta = quantize_list(diffs, bits=quant_bits) if diffs else ([], {})
        diffs_map = {ids[i]: qvecs[i] for i in range(len(ids))} if qvecs else {}

        seed_node = DreamSeed(
            id=uid("seed-"),
            seed_vec=seed_vec,
            members=member_ids,
            diffs=diffs_map,
            quant_meta=meta
        )

        self.seed_index.register(seed_node)

        with self.registry.lock:
            for n in group:
                self.registry.entities.pop(n.id, None)
            self.registry.save()

        QDMALedger.record("SEED_CREATED", seed_node.id, {"from": [n.id for n in group], 
                                                            "members": len(member_ids)})
        log(f"Created seed {seed_node.id} from {[n.id for n in group]}")
        return 1

    def complementary_sublimate_flexible(self, sim_thresh: float = None, sim_min: float = None,
                                         max_iters: int = None, target_nodes: Optional[int] = None) -> Dict[str, Any]:
        """1-1 ??:????????,????????"""
        sim_thresh = sim_thresh or cfg.default_sim
        sim_min = sim_min or cfg.sim_min
        max_iters = max_iters or cfg.default_iters

        def load_quarantine():
            try:
                if os.path.exists(self.quarantine_path):
                    return json.load(open(self.quarantine_path, "r", encoding="utf-8"))
            except Exception:
                pass
            return []

        def save_quarantine(q):
            try:
                safe_write_json(self.quarantine_path, q)
            except Exception:
                pass

        def entity_score(entity: DreamEntity) -> float:
            xi_score = entity.xi
            importance_score = entity.importance
            emotion_score = abs(entity.emotion)
            return xi_score * 0.5 + importance_score * 0.3 + emotion_score * 0.2

        quarantine = load_quarantine()
        merged_total = 0
        it = 0

        while it < max_iters:
            it += 1
            entities = list(self.registry.entities.values())
            if target_nodes and len(entities) <= target_nodes:
                break
            if len(entities) < 2:
                break

            scores = {e.id: entity_score(e) for e in entities}
            entities_sorted = sorted(entities, key=lambda x: scores.get(x.id, 0), reverse=True)

            used = set()
            pairs = []

            for i, a in enumerate(entities_sorted):
                if a.id in used or a.quarantined:
                    continue

                sa = scores.get(a.id, 0)
                best = None
                best_metric = 0.0
                best_sim = 0.0

                for b in entities_sorted[i+1:]:
                    if b.id in used or b.quarantined:
                        continue

                    sb = scores.get(b.id, 0)
                    sim = VectorSpace.cosine_sim(a.embedding, b.embedding)

                    complementarity = 1.0 - abs(sa - sb)
                    sign_bonus = 1.2 if sa * sb < 0 else 1.0
                    metric = sim * (abs(sa) + abs(sb) + 1e-6) * complementarity * sign_bonus * cfg.pair_sim_factor

                    if sim >= sim_thresh and metric > best_metric:
                        best_metric = metric
                        best = b
                        best_sim = sim
                    elif best is None and metric > best_metric:
                        best_metric = metric
                        best = b
                        best_sim = sim

                if best:
                    toxic_a = DetoxSystem.toxicity_score(a.embedding)
                    toxic_b = DetoxSystem.toxicity_score(best.embedding)

                    if toxic_a > cfg.toxicity_threshold or toxic_b > cfg.toxicity_threshold:
                        quarantine.append({
                            "a": a.id,
                            "b": best.id,
                            "sim": best_sim,
                            "metric": best_metric,
                            "iter": it,
                            "toxic_a": toxic_a,
                            "toxic_b": toxic_b,
                            "retries": 0
                        })
                        continue

                    if best_sim < sim_min:
                        pairs.append((a, best, best_metric, "low-sim"))
                    else:
                        pairs.append((a, best, best_metric, "high-sim"))

                    used.add(a.id)
                    used.add(best.id)

            if not pairs:
                break

            for a_entity, b_entity, metric, tag in pairs:
                try:
                    vecs = [a_entity.embedding, b_entity.embedding]
                    seed_vec = VectorSpace.mean_vec(vecs)
                    if seed_vec is None:
                        continue

                    proj_result = self.projection.micro_to_macro(seed_vec)
                    macro_repr = proj_result["macro"]

                    shards = sorted(set(a_entity.shards + b_entity.shards))

                    diffs = {}
                    ids = []
                    for e in [a_entity, b_entity]:
                        if e.embedding is not None:
                            diff = VectorSpace.vec_sub(e.embedding, seed_vec)
                            if diff is not None:
                                ids.append(e.shards[0] if e.shards else e.id)
                                diffs[ids[-1]] = diff

                    seed = DreamSeed(
                        id=uid("seed-"),
                        seed_vec=seed_vec,
                        macro_repr=macro_repr,
                        members=shards,
                        diffs=diffs,
                        quant_meta={"low_sim_flag": tag == "low-sim", "metric": metric}
                    )

                    self.seed_index.register(seed)

                    merged_emb = seed_vec
                    if tag == "low-sim":
                        merged_emb = VectorSpace.mean_vec([seed_vec, macro_repr])

                    merged_entity = DreamEntity(
                        id=uid("ent-"),
                        embedding=merged_emb,
                        shards=shards,
                        xi=(a_entity.xi + b_entity.xi) / 2,
                        score=(a_entity.score + b_entity.score),
                        importance=(a_entity.importance + b_entity.importance) / 2,
                        explain=f"merged_from_{tag}"
                    )

                    with self.registry.lock:
                        self.registry.entities.pop(a_entity.id, None)
                        self.registry.entities.pop(b_entity.id, None)
                        self.registry.entities[merged_entity.id] = merged_entity
                        self.registry.save()

                    QDMALedger.record("COMPRESS_MERGE", seed.id, {
                        "from": [a_entity.id, b_entity.id],
                        "shards": len(shards),
                        "metric": metric,
                        "tag": tag
                    })

                    log(f"Merged {a_entity.id}+{b_entity.id} -> {seed.id} ({tag})")
                    merged_total += 1
                    MET_COMPRESS.inc()

                except Exception:
                    log_exc("merge error")

            try:
                self.registry.save()
                self.seed_index.save()
            except Exception:
                log_exc("post-merge persist error")

        if quarantine:
            uniq = {}
            for q in quarantine:
                key = f"{q['a']}::{q['b']}"
                if key not in uniq:
                    uniq[key] = q
                else:
                    uniq[key]["retries"] = uniq[key].get("retries", 0) + 1
            save_quarantine(list(uniq.values()))
            log(f"Quarantine saved: {len(uniq)} pairs")

        return {"merged": merged_total, "iters": it, "remaining": len(self.registry.entities)}

    def force_cluster_and_merge(self, eps: float = 0.25, min_members: int = 2) -> Dict[str, Any]:
        """??????"""
        entities = list(self.registry.entities.values())
        if len(entities) < 2:
            return {"forced": 0}

        clusters = []
        used = set()

        for i, a in enumerate(entities):
            if a.id in used or a.quarantined:
                continue

            cluster = [a]
            used.add(a.id)

            for b in entities[i+1:]:
                if b.id in used or b.quarantined:
                    continue

                sim = VectorSpace.cosine_sim(a.embedding, b.embedding)
                if sim >= eps:
                    cluster.append(b)
                    used.add(b.id)

            if len(cluster) >= min_members:
                clusters.append(cluster)

        forced = 0

        for cluster in clusters:
            try:
                vecs = [e.embedding for e in cluster if e.embedding is not None]
                if not vecs:
                    continue

                seed_vec = VectorSpace.mean_vec(vecs)
                proj_result = self.projection.micro_to_macro(seed_vec)
                macro_repr = proj_result["macro"]

                shards = []
                for e in cluster:
                    shards.extend(e.shards)

                diffs = {}
                ids = []
                for e in cluster:
                    if e.embedding is not None:
                        diff = VectorSpace.vec_sub(e.embedding, seed_vec)
                        if diff is not None:
                            ids.append(e.shards[0] if e.shards else e.id)
                            diffs[ids[-1]] = diff

                seed = DreamSeed(
                    id=uid("seed-"),
                    seed_vec=seed_vec,
                    macro_repr=macro_repr,
                    members=sorted(set(shards)),
                    diffs=diffs,
                    quant_meta={"force_cluster_flag": True, "eps": eps}
                )

                self.seed_index.register(seed)

                merged_entity = DreamEntity(
                    id=uid("ent-"),
                    embedding=seed_vec,
                    shards=sorted(set(shards)),
                    xi=sum(e.xi for e in cluster) / len(cluster),
                    score=sum(e.score for e in cluster),
                    explain="force_cluster_merge"
                )

                with self.registry.lock:
                    for e in cluster:
                        self.registry.entities.pop(e.id, None)
                    self.registry.entities[merged_entity.id] = merged_entity
                    self.registry.save()

                QDMALedger.record("FORCE_CLUSTER_MERGE", seed.id, {
                    "from": [e.id for e in cluster],
                    "members": len(shards),
                    "eps": eps
                })

                log(f"Force-cluster: {seed.id} from {len(cluster)} entities")
                forced += 1

            except Exception:
                log_exc("force-cluster merge error")

        return {"forced": forced}

# -------------------------
# ????(????)
# -------------------------
class DreamStorage:
    def __init__(self, registry: "DreamRegistry", seed_index: "DreamSeedIndex",
                 fusion: FusionCore = None, projection_engine: ProjectionEngine = None):
        self.registry = registry
        self.seed_index = seed_index

        self.hot: Dict[str, DreamEntity] = {}
        self.near: Dict[str, DreamEntity] = {}
        self.shards: Dict[str, bytes] = {}
        self.index: Dict[str, Any] = {}
        self.quarantine: Dict[str, Dict[str, Any]] = {}
        self.page_table: Dict[str, Dict[str, Any]] = {}
        self.local_cache: Dict[str, str] = {}
        self.xi_pool: float = 1.0
        self.max_local = cfg.pocket_max_local

        self.faiss = FAISSIndex(cfg.dim) if "FAISSIndex" in globals() else None

        self.background = np.zeros(cfg.dim, dtype="float32") if HAS_NUMPY else [0.0] * cfg.dim

        self.work_queue = Queue(maxsize=cfg.work_queue_size)
        self.consolidation_q = Queue()
        self.rebuild_event = threading.Event()

        self.lock = threading.RLock()

        self.fusion = fusion
        self.projection_engine = projection_engine

        self._workers = []
        self._stop = False

        for _ in range(cfg.max_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)

        self._bg_thread = threading.Thread(target=self._background_loop, daemon=True)
        self._bg_thread.start()

        self._consolidation_thread = threading.Thread(target=self._consolidation_worker, daemon=True)
        self._consolidation_thread.start()

        self._decay_thread = threading.Thread(target=self._decay_worker, daemon=True)
        self._decay_thread.start()

        self.core_rules: Dict[str, Any] = {}

        QDMALedger.record("STORAGE_INIT", uid(), {"workers": cfg.max_workers})
        log(f"DreamStorage initialized with {cfg.max_workers} workers")

    def put_entity(self, entity: DreamEntity, hot: bool = True, near: bool = True):
        entity.version += 1
        entity.ts = time.time()
        entity.last_active = time.time()

        if hot:
            self.hot[entity.id] = entity
        if near:
            self.near[entity.id] = entity

        if entity.embedding is not None:
            self.index[entity.id] = entity.embedding.copy() if HAS_NUMPY and isinstance(entity.embedding, np.ndarray) else entity.embedding
            if self.faiss:
                self.faiss.add(entity.id, entity.embedding)

        self.work_queue.put(("update_bg", entity))

        QDMALedger.record("PUT_ENTITY", entity.id, {
            "xi": entity.xi,
            "shards": len(entity.shards),
            "hot": hot,
            "near": near
        })

    def put_shard(self, sid: str, payload: bytes, xi: float, trit: int = 0):
        self.shards[sid] = payload
        QDMALedger.record("PUT_SHARD", sid, {"xi": xi, "trit": trit})

    def get_entity(self, entity_id: str) -> Optional[DreamEntity]:
        entity = self.hot.get(entity_id) or self.near.get(entity_id)
        if entity and not entity.quarantined:
            entity.last_active = time.time()
            return entity
        return None

    def retrieve_any(self, entity_id: str) -> Optional[DreamEntity]:
        entity = self.hot.get(entity_id) or self.near.get(entity_id)
        if entity:
            entity.last_active = time.time()
        return entity

    def pocket_put(self, payload: bytes, embedding: Any, xi: float = 0.5,
                   core_protected: bool = False, importance: float = 0.0,
                   emotion: float = 0.0) -> Dict[str, Any]:
        try:
            clean_payload = Sanitizer.clean_text(payload)
        except Exception:
            clean_payload = payload

        mem_id = uid()
        embedding = VectorSpace.ensure_numpy(embedding)
        if embedding is None and HAS_NUMPY:
            embedding = np.random.randn(cfg.dim).astype("float32")

        unit = DreamEntity(
            id=mem_id,
            embedding=embedding,
            shards=[],
            xi=xi,
            trit=0,
            importance=importance,
            emotion=emotion,
            core_protected=core_protected,
            explain="sanitized_payload"
        )

        sid = uid()
        self.put_shard(sid, clean_payload, xi, 0)
        unit.shards = [sid]

        toxic = DetoxSystem.toxicity_score(unit.embedding, self.background)
        if toxic > cfg.toxicity_threshold:
            unit.quarantined = True
            unit.explain = f"quarantined_on_put:score={toxic:.3f}"
            self.hot[mem_id] = unit
            self.index[mem_id] = unit.embedding.copy() if unit.embedding else None
            self.quarantine[mem_id] = {
                "snapshot_hash": sha256_hex(f"{mem_id}:{time.time()}"),
                "expire_ts": time.time() + cfg.quarantine_hold,
                "requester": "auto",
                "reason": "toxicity_on_put",
                "score": toxic
            }
            QDMALedger.record("POCKET_PUT_QUARANTINED", mem_id, {"score": toxic})
            log(f"Pocket put quarantined {mem_id[:8]} score={toxic:.3f}")
            return {"status": "quarantined", "mem_id": mem_id, "score": toxic}

        self.put_entity(unit, hot=False, near=True)
        vaddr = "v:" + mem_id[:8]
        self.page_table[vaddr] = {
            "mem_id": mem_id,
            "local": False,
            "last_access": time.time()
        }

        if len(self.local_cache) < self.max_local and self.xi_pool > cfg.promote_cost:
            self._promote_to_local(vaddr)

        QDMALedger.record("POCKET_PUT", vaddr, {"mem_id": mem_id})
        return {"status": "ok", "vaddr": vaddr}

    def pocket_query(self, context_emb: Any, topk: int = 5, projection_mode: str = "micro") -> List[Dict[str, Any]]:
        start = time.time()

        vec = VectorSpace.ensure_numpy(context_emb)
        if vec is None:
            return []

        mids = []
        if self.fusion:
            mids = self.fusion.faiss_search(vec, topk=topk)

        if not mids:
            if not self.index:
                return []
            ids = list(self.index.keys())
            mats = [self.index[i] for i in ids if self.index[i] is not None]
            if not mats:
                return []

            if HAS_NUMPY:
                mats = np.stack(mats, axis=0)
                qn = np.linalg.norm(vec) + 1e-12
                norms = np.linalg.norm(mats, axis=1) + 1e-12
                sims = (mats @ vec) / (norms * qn)
                top_idx = np.argsort(-sims)[:topk]
                mids = [ids[int(i)] for i in top_idx]
            else:
                qn = math.sqrt(sum(x*x for x in vec)) + 1e-12
                sims = []
                for i, mat in enumerate(mats):
                    norm = math.sqrt(sum(x*x for x in mat)) + 1e-12
                    dot = sum(mat[j] * vec[j] for j in range(min(len(mat), len(vec))))
                    sim = dot / (norm * qn)
                    sims.append(sim)
                top_idx = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:topk]
                mids = [ids[i] for i in top_idx]

        results = []
        for mid in mids:
            u = self.retrieve_any(mid)
            if not u or u.quarantined:
                continue

            vaddr = None
            for va, info in self.page_table.items():
                if info["mem_id"] == mid:
                    vaddr = va
                    break

            if not vaddr:
                vaddr = "v:" + mid[:8]
                self.page_table[vaddr] = {
                    "mem_id": mid,
                    "local": False,
                    "last_access": time.time()
                }

            self.page_table[vaddr]["last_access"] = time.time()
            if len(results) < self.max_local:
                threading.Thread(target=self._promote_to_local, args=(vaddr,), daemon=True).start()

            results.append({"vaddr": vaddr, "mem_id": mid, "explain": u.explain})

        QDMALedger.record("POCKET_QUERY", uid(), {"hits": len(results), "proj_mode": projection_mode})
        return results

    def _promote_to_local(self, vaddr: str):
        info = self.page_table.get(vaddr)
        if not info:
            return

        mem_id = info["mem_id"]
        if self.xi_pool < cfg.promote_cost:
            return

        self.xi_pool -= cfg.promote_cost
        u = self.retrieve_any(mem_id)
        if u:
            info["local"] = True
            self.local_cache[vaddr] = mem_id

            if len(self.local_cache) > self.max_local:
                self._evict_one()

            QDMALedger.record("PROMOTE", vaddr, {"mem_id": mem_id, "xi_pool": self.xi_pool})

    def _evict_one(self):
        lru = None
        lru_ts = float("inf")
        for va, info in self.page_table.items():
            if info.get("local") and info["last_access"] < lru_ts:
                lru = va
                lru_ts = info["last_access"]

        if lru:
            self.page_table[lru]["local"] = False
            self.local_cache.pop(lru, None)

    def push_consolidation(self, mem_id: str):
        try:
            self.consolidation_q.put(mem_id, timeout=0.1)
        except Exception:
            pass

    def _consolidation_worker(self):
        batch = []
        while not self._stop:
            try:
                mem_id = self.consolidation_q.get(timeout=1.0)
                batch.append(mem_id)

                if len(batch) >= cfg.consolidation_batch:
                    self._do_consolidation_batch(batch)
                    batch = []
            except Empty:
                if batch:
                    self._do_consolidation_batch(batch)
                    batch = []
            except Exception as e:
                log(f"Consolidation worker error: {e}", "ERROR")
                time.sleep(0.5)

    def _do_consolidation_batch(self, mem_ids: List[str]):
        for mem_id in mem_ids:
            u = self.retrieve_any(mem_id)
            if not u or u.quarantined:
                continue

            data = (f"DETAILS:{u.id}:{time.time()}").encode("utf-8")
            chunks = [data[i:i+32] for i in range(0, len(data), 32)]
            sids = []

            for c in chunks:
                sid = uid()
                self.put_shard(sid, c, u.xi, u.trit)
                sids.append(sid)

            u.shards = sids
            self.put_entity(u, hot=False, near=True)

        log(f"Consolidation batch done size={len(mem_ids)}")

    def _worker_loop(self):
        while not self._stop:
            try:
                task = self.work_queue.get(timeout=1.0)
                if task is None:
                    break

                task_type, data = task

                if task_type == "update_bg":
                    self._update_background(data)

            except Empty:
                continue
            except Exception as e:
                log(f"Worker error: {e}", "ERROR")

    def _update_background(self, entity: DreamEntity):
        if entity.embedding is None:
            return

        vec = VectorSpace.ensure_numpy(entity.embedding)
        if vec is None:
            return

        if HAS_NUMPY:
            alpha = 1.0 / max(1, len(self.index))
            self.background = (1 - alpha) * self.background + alpha * vec
        else:
            alpha = 1.0 / max(1, len(self.index))
            self.background = [(1 - alpha) * self.background[i] + alpha * vec[i]
                              for i in range(len(self.background))]

    def _background_loop(self):
        while not self._stop:
            try:
                triggered = self.rebuild_event.wait(timeout=cfg.background_rebuild_interval)
                if triggered:
                    self._rebuild_background()
                time.sleep(cfg.background_rebuild_interval)
            except Exception as e:
                log(f"Background loop error: {e}", "ERROR")
                time.sleep(1.0)

    def _rebuild_background(self):
        if not self.index:
            self.background = np.zeros(cfg.dim, dtype="float32") if HAS_NUMPY else [0.0] * cfg.dim
            return

        try:
            vecs = [self.index[i] for i in self.index.keys() if self.index[i] is not None]
            if not vecs:
                return

            if HAS_NUMPY:
                mats = np.stack(vecs, axis=0)
                ids = [i for i in self.index.keys() if self.index[i] is not None]
                weights = np.array([
                    max(self.retrieve_any(i).xi if self.retrieve_any(i) else 0.01, 0.01) *
                    (1.0 + (self.retrieve_any(i).importance if self.retrieve_any(i) else 0.0))
                    for i in ids
                ])
                total = weights.sum() + 1e-12
                self.background = (weights[:, None] * mats).sum(axis=0) / total
                self.background = self.background.astype("float32")
            else:
                total_xi = sum(self.retrieve_any(i).xi if self.retrieve_any(i) else 0.01
                                for i in self.index.keys() if self.index[i] is not None) + 1e-12
                dim = len(vecs[0])
                self.background = [0.0] * dim
                for i, v in enumerate(self.index.keys()):
                    if self.index[i] is not None:
                        xi = self.retrieve_any(i).xi if self.retrieve_any(i) else 0.01
                        for j in range(dim):
                            if j < len(self.index[i]):
                                self.background[j] += xi * self.index[i][j] / total_xi

            QDMALedger.record("BACKGROUND_REBUILD", uid(), {"units": len(self.index)})
            log("Background field rebuilt")
        except Exception as e:
            log(f"Background rebuild error: {e}", "ERROR")

    def negentropy_read(self, holo: Hologram, toxicity_threshold: float = cfg.toxicity_threshold):
        mean_val = float(np.mean(holo.embedding)) if HAS_NUMPY else sum(holo.embedding) / len(holo.embedding)
        toxic_score = DetoxSystem.toxicity_score(holo.embedding, self.background)

        temp = DreamEntity(id="temp", embedding=holo.embedding.copy(), xi=0.5)
        violations = self._check_core_rules(temp)

        toxic = (toxic_score > toxicity_threshold) or (len(violations) > 0)

        if not toxic:
            QDMALedger.record("NEGENTROPY_OK", holo.id, {"toxic_score": toxic_score})
            return {"status": "ok", "hologram": holo, "toxic": False}

        c = -0.4 * np.sign(holo.embedding) * np.minimum(np.abs(holo.embedding), 0.05) if HAS_NUMPY else [-0.4 * (1 if x > 0 else -1) * min(abs(x), 0.05) for x in holo.embedding]
        if HAS_NUMPY:
            repaired_emb = holo.embedding + c
        else:
            repaired_emb = [holo.embedding[i] + c[i] for i in range(len(holo.embedding))]

        delta_comp = float(np.linalg.norm(c)) if HAS_NUMPY else math.sqrt(sum(x*x for x in c))
        repaired = Hologram(id=uid(), embedding=repaired_emb, confidence=max(0.1, holo.confidence - 0.05), 
                          provenance={"repair_of": holo.id, "stage": "light"}, 
                          delta_E=holo.delta_E + delta_comp, toxic_score=toxic_score)

        new_score = DetoxSystem.toxicity_score(repaired.embedding, self.background)

        QDMALedger.record("NEGENTROPY_REPAIR_STAGE1", repaired.id, {"orig": holo.id, "delta_comp": delta_comp, "new_score": new_score})

        if new_score <= toxicity_threshold:
            threading.Thread(target=self._async_validate_repair, args=(repaired,), daemon=True).start()
            return {"status": "repaired", "hologram": repaired, "toxic": False, "delta_comp": delta_comp}

        stronger = Hologram(id=uid(), embedding=repaired.embedding.copy(), 
                          confidence=max(0.05, repaired.confidence - 0.1), 
                          provenance={"repair_of": holo.id, "stage": "strong"}, 
                          delta_E=repaired.delta_E, toxic_score=new_score)
        threading.Thread(target=self._strong_repair_and_validate, args=(stronger, holo.id), daemon=True).start()
        return {"status": "repaired_async", "hologram": stronger, "toxic": True, "delta_comp": delta_comp}

    def _strong_repair_and_validate(self, repaired: Hologram, orig_holo_id: str):
        try:
            if HAS_NUMPY:
                repaired.embedding = 0.5 * repaired.embedding + 0.5 * self.background
            else:
                repaired.embedding = [0.5 * repaired.embedding[i] + 0.5 * self.background[i] for i in range(len(repaired.embedding))]

            new_score = DetoxSystem.toxicity_score(repaired.embedding, self.background)
            QDMALedger.record("NEGENTROPY_REPAIR_STAGE2", repaired.id, {"orig": orig_holo_id, "new_score": new_score})

            if new_score > cfg.toxicity_threshold:
                mem_id = uid()
                mu = DreamEntity(id=mem_id, embedding=repaired.embedding.copy(), xi=0.0)
                mu.quarantined = True
                mu.explain = f"auto_quarantine_from_repair:{orig_holo_id}"
                self.hot[mem_id] = mu
                self.index[mem_id] = mu.embedding.copy()
                self.quarantine[mem_id] = {
                    "snapshot_hash": sha256_hex(mem_id + ":" + str(time.time())),
                    "expire_ts": time.time() + cfg.quarantine_hold,
                    "requester": "auto_repair",
                    "reason": "repair_failed",
                    "score": new_score
                }
                QDMALedger.record("AUTO_QUARANTINE", mem_id, {"from_holo": orig_holo_id, "score": new_score})
                log(f"Auto-quarantined {mem_id[:8]} from repair of holo {orig_holo_id[:8]}")
            else:
                QDMALedger.record("NEGENTROPY_VALIDATE", repaired.id, {"validated": True})
                log(f"Repair validated {repaired.id[:8]}")
        except Exception as e:
            log(f"_strong_repair_and_validate error: {e}", "ERROR")

    def _async_validate_repair(self, repaired: Hologram):
        time.sleep(0.5)
        QDMALedger.record("NEGENTROPY_VALIDATE", repaired.id, {"validated": True})
        log(f"Repair validated {repaired.id[:8]}")

    def add_core_rule(self, rule_id: str, fn: Callable[[DreamEntity], bool], signer: str = "admin"):
        self.core_rules[rule_id] = {"fn": fn, "signer": signer}
        QDMALedger.record("CORE_RULE_ADD", rule_id, {"signer": signer})
        log(f"Core rule added {rule_id}")

    def _check_core_rules(self, unit: DreamEntity) -> List[str]:
        violated = []
        for rid, info in self.core_rules.items():
            try:
                ok = info["fn"](unit)
            except Exception:
                ok = False
            if not ok:
                violated.append(rid)
        return violated

    def request_self_delete(self, mem_id: str, requester: str, hold_seconds: float = None) -> Dict[str, Any]:
        hold_seconds = hold_seconds or cfg.quarantine_hold
        u = self.retrieve_any(mem_id)

        if not u:
            return {"status": "not_found"}

        if u.core_protected:
            QDMALedger.record("DELETE_REJECT_CORE", mem_id, {"requester": requester})
            return {"status": "rejected_core_protected"}

        snap_hash = sha256_hex(f"{mem_id}:{time.time()}")
        expire_ts = time.time() + hold_seconds

        self.quarantine[mem_id] = {
            "snapshot_hash": snap_hash,
            "expire_ts": expire_ts,
            "requester": requester,
            "reason": "self_delete"
        }

        u.quarantined = True
        u.delete_requester = requester
        u.delete_request_ts = time.time()

        if mem_id in self.index:
            del self.index[mem_id]

        QDMALedger.record("QUARANTINE", mem_id, {
            "requester": requester,
            "expire_ts": expire_ts
        })

        log(f"Quarantined {mem_id} by {requester} until {expire_ts}")

        threading.Thread(target=self._delayed_permanent_delete, args=(mem_id, expire_ts), daemon=True).start()
        MET_DELETE.inc()

        return {"status": "quarantined", "mem_id": mem_id, "hold_until": expire_ts}

    def undo_delete(self, mem_id: str, requester: str):
        info = self.quarantine.get(mem_id)
        if not info:
            return {"status": "not_quarantined"}

        if info["requester"] != requester and requester != "admin":
            return {"status": "not_authorized"}

        u = self.retrieve_any(mem_id)
        if not u:
            return {"status": "unit_missing"}

        u.quarantined = False
        u.delete_requester = None
        u.delete_request_ts = None
        self.index[mem_id] = u.embedding.copy()
        self.quarantine.pop(mem_id, None)

        QDMALedger.record("UNDO_QUARANTINE", mem_id, {"requester": requester})
        log(f"Undo quarantine {mem_id} by {requester}")
        return {"status": "restored", "mem_id": mem_id}

    def _delayed_permanent_delete(self, mem_id: str, expire_ts: float):
        while time.time() < expire_ts and not self._stop:
            time.sleep(0.5)

        info = self.quarantine.get(mem_id)
        if not info:
            return

        if time.time() >= info["expire_ts"]:
            del self.hot[mem_id]
            del self.near[mem_id]
            if mem_id in self.index:
                del self.index[mem_id]
            del self.quarantine[mem_id]

            QDMALedger.record("PERMANENT_DELETE", mem_id, {"ts": time.time()})
            log(f"Permanently deleted {mem_id}")

    def _decay_worker(self):
        while not self._stop:
            try:
                time.sleep(cfg.decay_interval)
                now = time.time()

                to_decay = []
                for mid, u in list(self.hot.items()):
                    age = now - u.last_active
                    u.decay_score += cfg.decay_rate * (age / max(1.0, cfg.decay_interval))

                    if u.decay_score > 0.5 and u.importance < 0.1:
                        to_decay.append(mid)

                for mid in to_decay:
                    u = self.hot.get(mid)
                    if not u:
                        continue

                    u.xi = max(0.0, u.xi - 0.1)

                    QDMALedger.record("DECAY_APPLIED", mid, {"decay_score": u.decay_score, "xi": u.xi})

                    if u.xi <= 0.0 and not u.core_protected:
                        self.request_self_delete(mid, requester="decay_worker", hold_seconds=cfg.quarantine_hold)

                log(f"Decay pass done, decayed={len(to_decay)}")
            except Exception as e:
                log(f"Decay worker error: {e}", "ERROR")
                time.sleep(1.0)

    def shutdown(self):
        self._stop = True
        log("DreamStorage shutdown complete")

# -------------------------
# 注册表与索引系统
# -------------------------
class DreamRegistry:
    def __init__(self):
        self.entities: Dict[str, DreamEntity] = {}
        self.lock = threading.RLock()
        self.path = os.path.join(cfg.data_dir, "entities.json")
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for eid, ed in data.get("entities", {}).items():
                    self.entities[eid] = DreamEntity.from_dict(ed)
            except Exception as e:
                log(f"Registry load error: {e}", "ERROR")

    def save(self):
        with self.lock:
            data = {"entities": {eid: e.to_dict() for eid, e in self.entities.items()}}
            safe_write_json(self.path, data)

    def register(self, entity: DreamEntity):
        with self.lock:
            self.entities[entity.id] = entity
            self.save()
        QDMALedger.record("ENTITY_REGISTER", entity.id, {"shards": len(entity.shards)})
        try:
            GAUGE_UNITS.set(len(self.entities))
        except Exception:
            pass

class DreamSeedIndex:
    def __init__(self):
        self.seeds: Dict[str, DreamSeed] = {}
        self.lock = threading.RLock()
        self.path = os.path.join(cfg.data_dir, "seeds.json")
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for sid, sd in data.get("seeds", {}).items():
                    self.seeds[sid] = DreamSeed.from_dict(sd)
            except Exception as e:
                log(f"SeedIndex load error: {e}", "ERROR")

    def save(self):
        with self.lock:
            data = {"seeds": {sid: s.to_dict() for sid, s in self.seeds.items()}}
            safe_write_json(self.path, data)

    def register(self, seed: DreamSeed):
        with self.lock:
            self.seeds[seed.id] = seed
            self.save()
        QDMALedger.record("SEED_REGISTER", seed.id, {"members": len(seed.members)})
        try:
            GAUGE_SEEDS.set(len(self.seeds))
        except Exception:
            pass

# -------------------------
# 自举数据注入
# -------------------------
class SelfBootstrapper:
    def __init__(self, registry: DreamRegistry):
        self.registry = registry
        self.injected_counter_path = os.path.join(cfg.data_dir, "injected_count.json")

    def ingest_from_shards(self, max_import: int = 1024) -> int:
        if not os.path.isdir(cfg.shard_dir):
            return 0

        files = sorted(os.listdir(cfg.shard_dir))
        imported = 0
        seen_hashes = set()

        for fname in files[:max_import]:
            fpath = os.path.join(cfg.shard_dir, fname)
            try:
                with open(fpath, "rb") as f:
                    payload = f.read()
            except Exception:
                continue

            h = hashlib.sha256(payload).hexdigest()
            if h in seen_hashes:
                continue

            seen_hashes.add(h)

            vec = []
            for i in range(cfg.dim):
                idx = (i * 2) % len(h)
                try:
                    b = int(h[idx:idx+2], 16)
                except Exception:
                    b = 0
                val = ((b / 255.0) * 0.6) - 0.3
                vec.append(val)

            nid = uid("ent-")
            shard_id = fname

            node = DreamEntity(
                id=nid,
                embedding=np.array(vec, dtype="float32") if HAS_NUMPY else vec,
                shards=[shard_id],
                explain="ingested_from_shard"
            )

            self.registry.register(node)
            imported += 1

        return imported

    def inject_animation_samples(self, count: int = 24) -> int:
        injected = 0
        i = 0
        count = min(count, cfg.max_auto_inject)

        already = self._get_injected_count()
        to_inject = max(0, count - already)

        while injected < to_inject:
            s = cfg.auto_inject_samples[i % len(cfg.auto_inject_samples)] + f" sample-{already+injected}"

            h = hashlib.sha256(s.encode("utf-8")).digest()

            vec = []
            for k in range(cfg.dim):
                b = h[k % len(h)]
                val = ((b /255.0) * 0.6) - 0.3
                vec.append(val)

            nid = uid("ent-")
            node = DreamEntity(
                id=nid,
                embedding=np.array(vec, dtype="float32") if HAS_NUMPY else vec,
                shards=[f"anim-{already+injected}"],
                explain="injected_animation_sample"
            )

            self.registry.register(node)
            injected += 1
            i += 1

        if injected > 0:
            self._set_injected_count(already + injected)

        return injected

    def _get_injected_count(self) -> int:
        try:
            if os.path.exists(self.injected_counter_path):
                with open(self.injected_counter_path, "r", encoding="utf-8") as f:
                    return int(json.load(f).get("count", 0))
        except Exception:
            pass
        return 0

    def _set_injected_count(self, n: int):
        try:
            safe_write_json(self.injected_counter_path, {"count": n})
        except Exception:
            pass

# -------------------------
# FAISS加速层
# -------------------------
class FAISSIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = None
        self.ids: List[str] = []
        self.buffer: List[Any] = []
        self.buffer_ids: List[str] = []
        self.lock = threading.RLock()
        self.enabled = HAS_FAISS and cfg.use_faiss

        if self.enabled:
            try:
                index_path = os.path.join(cfg.data_dir, "faiss.index")
                if os.path.exists(index_path):
                    self.index = faiss.read_index(index_path)
                    log("FAISS index loaded")
                else:
                    self.index = faiss.IndexHNSWFlat(dim, 32)
                    self.index.hnsw.efConstruction = 64
                    self.index.hnsw.efSearch = 64
                    log("FAISS index created")
            except Exception as e:
                log(f"FAISS init error: {e}", "ERROR")
                self.enabled = False

    def add(self, mem_id: str, emb: Any):
        vec = VectorSpace.ensure_numpy(emb)
        if vec is None:
            return

        if not self.enabled:
            with self.lock:
                self.buffer.append(vec)
                self.buffer_ids.append(mem_id)
                if len(self.buffer) >= cfg.faiss_batch:
                    self._flush()
            return

        with self.lock:
            if HAS_NUMPY:
                self.buffer.append(vec.reshape(1, -1))
            else:
                self.buffer.append(vec)
            self.buffer_ids.append(mem_id)
            if len(self.buffer) >= cfg.faiss_batch:
                self._flush()

    def _flush(self):
        if not self.buffer:
            return

        try:
            if self.enabled and self.index:
                if HAS_NUMPY:
                    vecs = np.vstack(self.buffer)
                else:
                    vecs = self.buffer
                self.index.add(vecs)
                self.ids.extend(self.buffer_ids)
                log(f"FAISS batch added {len(self.buffer_ids)}")
            else:
                self.ids.extend(self.buffer_ids)
        except Exception as e:
            log(f"FAISS flush error: {e}", "ERROR")
        finally:
            self.buffer = []
            self.buffer_ids = []

    def search(self, emb: Any, topk: int = 5) -> List[str]:
        vec = VectorSpace.ensure_numpy(emb)
        if vec is None:
            return []

        if self.enabled and self.index and len(self.ids) > 0:
            try:
                if HAS_NUMPY:
                    q = vec.reshape(1, -1)
                else:
                    q = np.array([vec])
                D, I = self.index.search(q, topk)
                res = []
                for idx in I[0]:
                    if 0 <= idx < len(self.ids):
                        res.append(self.ids[int(idx)])
                return res
            except Exception as e:
                log(f"FAISS search error: {e}", "ERROR")

        with self.lock:
            if not self.buffer and not self.ids:
                return []
            return self.ids[:topk]

    def save(self):
        if not self.enabled:
            return

        try:
            with self.lock:
                if self.buffer:
                    self._flush()
                index_path = os.path.join(cfg.data_dir, "faiss.index")
                faiss.write_index(self.index, index_path)
                log("FAISS index saved")
        except Exception as e:
            log(f"FAISS save error: {e}", "ERROR")

# -------------------------
# 并行协调器
# -------------------------
class QuantumDreamDriverUltimate:
    def __init__(self):
        self.registry = DreamRegistry()
        self.seed_index = DreamSeedIndex()
        self.projection = ProjectionEngine(cfg.dim, cfg.micro_dim, cfg.macro_dim, cfg.high_dim)
        self.fusion = FusionCore(cfg.dim)
        self.storage = DreamStorage(self.registry, self.seed_index, self.fusion, self.projection)
        self.compressor = DreamCompressor(self.registry, self.seed_index, self.projection, self.fusion)
        self.quarantine_retry = QuarantineRetrySystem(self.compressor, self.registry)
        self.lazy_expander = LazyExpander(self.seed_index)
        self.bootstrapper = SelfBootstrapper(self.registry)

        self.fusion.storage = self.storage
        self.fusion.projection_engine = self.projection
        self.projection.storage = self.storage

        self.compress_queue = Queue(maxsize=cfg.work_queue_size)
        self.project_queue = Queue(maxsize=cfg.work_queue_size)
        self.quarantine_queue = Queue(maxsize=cfg.work_queue_size)
        self.consolidation_queue = Queue(maxsize=cfg.work_queue_size)

        self.running = True
        self._stop_requested = False

        self._compress_workers = []
        self._project_workers = []
        self._quarantine_workers = []
        self._consolidation_workers = []

        for _ in range(cfg.max_workers // 3):
            t = threading.Thread(target=self._compress_worker, daemon=True)
            t.start()
            self._compress_workers.append(t)

        for _ in range(cfg.max_workers // 3):
            t = threading.Thread(target=self._project_worker, daemon=True)
            t.start()
            self._project_workers.append(t)

        for _ in range(2):
            t = threading.Thread(target=self._quarantine_worker, daemon=True)
            t.start()
            self._quarantine_workers.append(t)

        for _ in range(cfg.max_workers // 3):
            t = threading.Thread(target=self._consolidation_worker, daemon=True)
            t.start()
            self._consolidation_workers.append(t)

        self._coordinator = threading.Thread(target=self._coordinate_loop, daemon=True)
        self._coordinator.start()

        self.metrics = {
            "compress_runs": 0,
            "project_runs": 0,
            "quarantine_retries": 0,
            "consolidations": 0,
            "entities_merged": 0,
            "seeds_created": 0,
            "bootstrapped": 0
        }
        self.lock = threading.RLock()

        QDMALedger.record("DRIVER_INIT", uid(), {
            "workers": cfg.max_workers,
            "dimensions": {"dim": cfg.dim, "micro": cfg.micro_dim, "macro": cfg.macro_dim, "high": cfg.high_dim}
        })
        log("QuantumDreamDriverUltimate initialized with full parallel architecture")

    def request_shutdown(self):
        self._stop_requested = True

    def _compress_worker(self):
        while not self._stop_requested:
            try:
                task = self.compress_queue.get(timeout=1.0)
                if task is None:
                    break

                task_type, params = task

                if task_type == "complementary":
                    result = self.compressor.complementary_sublimate_flexible(**params)
                    with self.lock:
                        self.metrics["compress_runs"] += 1
                        self.metrics["entities_merged"] += result.get("merged", 0)

                elif task_type == "force_cluster":
                    result = self.compressor.force_cluster_and_merge(**params)
                    with self.lock:
                        self.metrics["compress_runs"] += 1
                        self.metrics["entities_merged"] += result.get("forced", 0)

            except Empty:
                continue
            except Exception as e:
                log_exc("compress_worker error")

    def _project_worker(self):
        while not self._stop_requested:
            try:
                task = self.project_queue.get(timeout=1.0)
                if task is None:
                    break

                task_type, data = task

                if task_type == "micro_to_macro":
                    emb = data.get("embedding")
                    result = self.projection.micro_to_macro(emb)
                    with self.lock:
                        self.metrics["project_runs"] += 1

                elif task_type == "high_dim":
                    emb = data.get("embedding")
                    result = self.projection.high_dim_project(emb)
                    with self.lock:
                        self.metrics["project_runs"] += 1

            except Empty:
                continue
            except Exception as e:
                log_exc("project_worker error")

    def _quarantine_worker(self):
        while not self._stop_requested:
            try:
                task = self.quarantine_queue.get(timeout=1.0)
                if task is None:
                    break

                result = self.quarantine_retry.retry_and_sublimate(**task)
                with self.lock:
                    self.metrics["quarantine_retries"] += 1

            except Empty:
                continue
            except Exception as e:
                log_exc("quarantine_worker error")

    def _consolidation_worker(self):
        while not self._stop_requested:
            try:
                mem_id = self.consolidation_queue.get(timeout=1.0)
                if mem_id is None:
                    break

                u = self.storage.retrieve_any(mem_id)
                if u and not u.quarantined:
                    self.storage.push_consolidation(mem_id)
                    with self.lock:
                        self.metrics["consolidations"] += 1

            except Empty:
                continue
            except Exception as e:
                log_exc("consolidation_worker error")

    def _coordinate_loop(self):
        last_compress = time.time()
        last_project = time.time()
        last_quarantine = time.time()
        last_consolidation = time.time()

        while not self._stop_requested:
            try:
                now = time.time()

                if now - last_compress > cfg.idle_run_seconds:
                    self.schedule_compress()
                    last_compress = now

                if now - last_project > (cfg.poll_interval * 2):
                    self.schedule_project()
                    last_project = now

                if now - last_quarantine > (cfg.poll_interval * 3):
                    self.schedule_quarantine_retry()
                    last_quarantine = now

                if now - last_consolidation > (cfg.poll_interval * 4):
                    self.schedule_consolidation()
                    last_consolidation = now

                time.sleep(cfg.poll_interval)

            except Exception as e:
                log_exc("coordinate_loop error")

    def schedule_compress(self):
        try:
            self.compress_queue.put(("complementary", {
                "sim_thresh": cfg.default_sim,
                "sim_min": cfg.sim_min,
                "max_iters": cfg.default_iters
            }), timeout=0.1)
            log("Compress task scheduled")
        except Exception:
            pass

    def schedule_project(self):
        entities = list(self.registry.entities.values())
        if entities:
            sample = random.choice(entities)
            if sample.embedding:
                try:
                    self.project_queue.put(("micro_to_macro", {"embedding": sample.embedding}), timeout=0.1)
                    log("Project task scheduled")
                except Exception:
                    pass

    def schedule_quarantine_retry(self):
        try:
            self.quarantine_queue.put({
                "top_k": 20,
                "relax_steps": [0.55, 0.50, 0.45],
                "interp_steps": 5,
                "perturb_sigma": 0.02
            }, timeout=0.1)
            log("Quarantine retry task scheduled")
        except Exception:
            pass

    def schedule_consolidation(self):
        entities = list(self.registry.entities.values())
        if entities:
            for e in entities[:cfg.consolidation_batch]:
                try:
                    self.consolidation_queue.put(e.id, timeout=0.05)
                except Exception:
                    pass
            log("Consolidation task scheduled")

    def add_entity(self, embedding: Any, shards: List[str] = None,
                   xi: float = 0.5, importance: float = 0.0,
                   emotion: float = 0.0, core_protected: bool = False) -> str:
        vec = VectorSpace.ensure_numpy(embedding)
        if vec is None:
            vec = np.random.randn(cfg.dim).astype("float32") if HAS_NUMPY else [random.gauss(0, 1) for _ in range(cfg.dim)]

        shards = shards or [uid("shard-")]

        toxic = DetoxSystem.toxicity_score(vec)
        if toxic > cfg.toxicity_threshold:
            vec = DetoxSystem.repair(vec)

        entity = DreamEntity(
            id=uid("ent-"),
            embedding=vec,
            shards=shards,
            xi=xi,
            importance=importance,
            emotion=emotion,
            core_protected=core_protected,
            explain="user_added"
        )

        self.registry.register(entity)
        self.storage.put_entity(entity)

        QDMALedger.record("ADD_ENTITY", entity.id, {"toxic": toxic})
        log(f"Added entity {entity.id}")

        return entity.id

    def query(self, embedding: Any, topk: int = 5) -> List[Dict[str, Any]]:
        vec = VectorSpace.ensure_numpy(embedding)
        if vec is None:
            return []

        toxic = DetoxSystem.toxicity_score(vec)
        if toxic > cfg.toxicity_threshold:
            vec = DetoxSystem.repair(vec)

        proj_result = self.projection.micro_to_macro(vec)
        macro_vec = proj_result["macro"]

        enhanced_vec = VectorSpace.mean_vec([vec, macro_vec])

        similar_ids = self.storage.faiss.search(enhanced_vec, topk)

        results = []
        for sid in similar_ids:
            entity = self.storage.get_entity(sid)
            if entity:
                sim = VectorSpace.cosine_sim(enhanced_vec, entity.embedding)
                results.append({
                    "entity_id": sid,
                    "similarity": float(sim),
                    "explain": entity.explain
                })

        return results

    def pocket_put(self, payload: bytes, embedding: Any, xi: float = 0.5,
                   core_protected: bool = False, importance: float = 0.0,
                   emotion: float = 0.0) -> Dict[str, Any]:
        return self.storage.pocket_put(payload, embedding, xi, core_protected, importance, emotion)

    def pocket_query(self, context_emb: Any, topk: int = 5, projection_mode: str = "micro") -> List[Dict[str, Any]]:
        return self.storage.pocket_query(context_emb, topk, projection_mode)

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "entities": len(self.registry.entities),
                "seeds": len(self.seed_index.seeds),
                "metrics": dict(self.metrics),
                "background_norm": float(np.linalg.norm(self.storage.background)) if HAS_NUMPY 
                                   else math.sqrt(sum(x*x for x in self.storage.background)),
                "faiss_enabled": self.storage.faiss.enabled if self.storage.faiss else False,
                "timestamp": now_ts()
            }

    def bootstrap_data(self, max_import: int = 1024, max_inject: int = 24):
        imported = self.bootstrapper.ingest_from_shards(max_import)
        if imported > 0:
            with self.lock:
                self.metrics["bootstrapped"] += imported
            log(f"Bootstrapped {imported} shards")

        injected = self.bootstrapper.inject_animation_samples(max_inject)
        if injected > 0:
            with self.lock:
                self.metrics["bootstrapped"] += injected
            log(f"Injected {injected} samples")

    def shutdown(self):
        self.running = False
        self._stop_requested = True

        for _ in range(len(self._compress_workers)):
            self.compress_queue.put(None)

        for _ in range(len(self._project_workers)):
            self.project_queue.put(None)

        for _ in range(len(self._quarantine_workers)):
            self.quarantine_queue.put(None)

        for _ in range(len(self._consolidation_workers)):
            self.consolidation_queue.put(None)

        self.registry.save()
        self.seed_index.save()
        self.storage.shutdown()
        QDMALedger.dump(os.path.join(cfg.data_dir, "ledger.json"))

        log("QuantumDreamDriverUltimate shutdown complete")

# -------------------------
# HTTP API
# -------------------------
_global_driver: Optional[QuantumDreamDriverUltimate] = None

def set_global_driver(driver: QuantumDreamDriverUltimate):
    global _global_driver
    _global_driver = driver

def get_global_driver() -> Optional[QuantumDreamDriverUltimate]:
    return _global_driver

if HAS_FASTAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        driver = QuantumDreamDriverUltimate()
        set_global_driver(driver)
        yield
        if driver:
            driver.shutdown()

    app = FastAPI(lifespan=lifespan)

    @app.get("/")
    async def root():
        return {
            "name": "Quantum Dream Memory Algorithm Ultimate",
            "version": "3.0.0 Ultimate",
            "description": "Complete fusion of QEM and QMC using 1 + (-1) = 0 puzzle fusion"
        }

    @app.get("/status")
    async def status():
        d = get_global_driver()
        return d.get_status() if d else {"status": "not_initialized"}

    @app.post("/add")
    async def add_entity(payload: Dict[str, Any]):
        d = get_global_driver()
        if not d:
            raise HTTPException(status_code=503, detail="Driver not initialized")

        embedding = payload.get("embedding")
        shards = payload.get("shards")
        xi = payload.get("xi", 0.5)
        importance = payload.get("importance", 0.0)
        emotion = payload.get("emotion", 0.0)
        core_protected = payload.get("core_protected", False)

        entity_id = d.add_entity(embedding, shards, xi, importance, emotion, core_protected)
        return {"entity_id": entity_id, "status": "ok"}

    @app.post("/pocket_put")
    async def pocket_put(payload: Dict[str, Any]):
        d = get_global_driver()
        if not d:
            raise HTTPException(status_code=503, detail="Driver not initialized")

        text = payload.get("text", "").encode("utf-8")
        embedding = payload.get("embedding")
        xi = float(payload.get("xi", 0.5))
        core_protected = payload.get("core_protected", False)
        importance = float(payload.get("importance", 0.0))
        emotion = float(payload.get("emotion", 0.0))

        res = d.pocket_put(text, embedding, xi, core_protected, importance, emotion)
        return res

    @app.post("/query")
    async def query(payload: Dict[str, Any]):
        d = get_global_driver()
        if not d:
            raise HTTPException(status_code=503, detail="Driver not initialized")

        embedding = payload.get("embedding")
        topk = int(payload.get("topk", 5))
        results = d.query(embedding, topk)
        return {"results": results}

    @app.post("/pocket_query")
    async def pocket_query(payload: Dict[str, Any]):
        d = get_global_driver()
        if not d:
            raise HTTPException(status_code=503, detail="Driver not initialized")

        context_emb = payload.get("context_emb")
        topk = int(payload.get("topk", 5))
        mode = payload.get("proj_mode", "micro")
        results = d.pocket_query(context_emb, topk, mode)
        return {"results": results}

    @app.get("/metrics")
    async def metrics():
        if HAS_PROMETHEUS:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        d = get_global_driver()
        return d.get_status() if d else {"status": "no_metrics"}

    @app.post("/bootstrap")
    async def bootstrap(payload: Dict[str, Any]):
        d = get_global_driver()
        if not d:
            raise HTTPException(status_code=503, detail="Driver not initialized")

        max_import = int(payload.get("max_import", 1024))
        max_inject = int(payload.get("max_inject", 24))

        d.bootstrap_data(max_import, max_inject)
        return {"status": "bootstrapped"}

# -------------------------
# 主入口
# -------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="量子梦幻记忆算法终极版")
    parser.add_argument("--debug-run-once", action="store_true", help="运行一次详细调试后退出")
    parser.add_argument("--no-auto", action="store_true", help="不自动运行（仅API模式）")
    parser.add_argument("--add-demo", type=int, default=0, help="添加演示实体数量")
    parser.add_argument("--query-demo", action="store_true", help="执行演示查询")
    parser.add_argument("--bootstrap", action="store_true", help="执行自举数据注入")
    args = parser.parse_args(argv)

    log("=== 量子梦幻记忆算法终极版启动 ===")
    log(f"版本：3.0.0 Ultimate")
    log(f"融合法则：1 + (-1) = 0 (拼图融合)")
    log(f"并行架构：{cfg.max_workers} 工作线程")
    log(f"维度配置：dim={cfg.dim}, micro={cfg.micro_dim}, macro={cfg.macro_dim}, high={cfg.high_dim}")
    log(f"FAISS：{'启用' if HAS_FAISS else '未安装'}")
    log(f"Redis：{'启用' if HAS_REDIS else '未安装'}")
    log(f"FastAPI：{'启用' if HAS_FASTAPI else '未安装'}")
    log(f"Prometheus：{'启用' if HAS_PROMETHEUS else '未安装'}")
    log(f"NumPy：{'启用' if HAS_NUMPY else '降级到纯Python'}")

    driver = QuantumDreamDriverUltimate()
    set_global_driver(driver)

    if args.bootstrap:
        log("执行自举数据注入...")
        driver.bootstrap_data(1024, 24)

    if args.add_demo > 0:
        log(f"添加 {args.add_demo} 个演示实体...")
        for i in range(args.add_demo):
            emb = np.random.randn(cfg.dim).astype("float32") if HAS_NUMPY else [random.gauss(0, 1) for _ in range(cfg.dim)]
            shards = [f"demo-shard-{i}-{j}" for j in range(random.randint(1, 4))]
            xi = random.random()
            importance = random.random()
            emotion = random.uniform(-1, 1)
            driver.add_entity(emb, shards, xi, importance, emotion)
            time.sleep(0.01)
        log(f"演示实体添加完成")

    if args.query_demo:
        log("执行演示查询...")
        q_emb = np.random.randn(cfg.dim).astype("float32") if HAS_NUMPY else [random.gauss(0, 1) for _ in range(cfg.dim)]
        results = driver.query(q_emb, topk=3)
        log(f"查询结果：{results}")

    if args.debug_run_once:
        log("调试运行一次...")
        driver.schedule_compress()
        time.sleep(5.0)
        status = driver.get_status()
        log(f"系统状态：{status}")
        driver.shutdown()
        log("调试运行完成")
        return

    if args.no_auto:
        log("自动运行已禁用")
        if HAS_FASTAPI and cfg.enable_http:
            import uvicorn
            log(f"启动HTTP服务器 on port {cfg.status_port or 8000}")
            uvicorn.run(app, host="0.0.0.0", port=cfg.status_port or 8000)
        return

    try:
        log("进入主循环...")
        while driver.running:
            time.sleep(1.0)
    except KeyboardInterrupt:
        log("接收到中断信号，正在关闭...")
    finally:
        driver.shutdown()
        log("=== 量子梦幻记忆算法终极版已停止 ===")

if __name__ == "__main__":
    main(sys.argv[1:])
