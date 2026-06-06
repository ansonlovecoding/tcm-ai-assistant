"""
Local TF-IDF knowledge base for TCM tongue diagnosis.

Two files in kb/ are indexed at startup (lazy, on first query):
  - 中医诊断学-望舌头篇              (theoretical paragraphs)
  - 中医望诊与舌诊彩色图解-第五章.txt  (clinical cases, structured extraction)

Public API
----------
    from ai_llm.rag import retrieve

    chunks = retrieve(["chihenshe", "baitaishe"], top_k=5)
    # [{"text": "...", "source": "...", "similarity": 0.87}, ...]
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# Label → Chinese search keywords
# ---------------------------------------------------------------------------

LABEL_TERMS: dict[str, str] = {
    "jiankangshe":  "健康舌 正常舌象 淡红舌薄白苔",
    "botaishe":     "剥苔 镜面舌 光滑舌 胃阴枯竭",
    "hongshe":      "红舌 舌色鲜红 热证 内热 阴虚内热",
    "zishe":        "紫舌 血液运行不畅 血瘀 瘀滞",
    "pangdashe":    "胖大舌 舌体胖大 水饮痰湿 齿痕 脾虚",
    "shoushe":      "瘦薄舌 舌体瘦小枯薄 气血两虚 阴虚火旺",
    "hongdianshe":  "芒刺 红点 邪热亢盛",
    "liewenshe":    "裂纹舌 精血亏损 津液耗伤 阴虚",
    "chihenshe":    "齿痕舌 齿痕 脾虚 湿盛 水液代谢",
    "baitaishe":    "白苔 苔白 寒湿 表证 脾胃功能偏弱",
    "huangtaishe":  "黄苔 苔黄 里证 热证 湿热 胃肠积热",
    "heitaishe":    "黑苔 灰苔 焦黄苔 热极津枯 危重",
    "huataishe":    "滑苔 腻苔 湿浊 痰湿 阳气被阴邪抑制",
    "shenquao":     "肾 舌根 下焦 肾相关",
    "shenqutu":     "肾 舌根 下焦 肾相关",
    "gandanao":     "肝胆 舌边 肝相关",
    "gandantu":     "肝胆 舌边 肝相关",
    "piweiao":      "脾胃 舌中部 中焦",
    "piweitu":      "脾胃 舌中部 中焦",
    "xinfeiao":     "心肺 舌尖 上焦",
    "xinfeitu":     "心肺 舌尖 上焦",
}

KB_DIR = Path(__file__).parent / "kb"
MIN_CHUNK_LEN = 35


# ---------------------------------------------------------------------------
# Document loaders
# ---------------------------------------------------------------------------

def _load_theory_file(path: Path) -> list[dict]:
    """Paragraph-chunk a theoretical TCM text (e.g. 中医诊断学)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    chunks = []
    for para in re.split(r"\n{2,}", text):
        para = para.strip()
        if len(para) >= MIN_CHUNK_LEN:
            chunks.append({"text": para, "source": path.name})
    return chunks


def _load_case_file(path: Path) -> list[dict]:
    """
    Extract structured snippets from a clinical-case file.

    Each snippet: 证型名 | 舌象：... | 诊断：... | 治法：...
    Falls back to paragraph chunking if no case headers are found.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"图\d+-\d+[　\s]*[一-鿿]*\n?", "", text)

    source = path.name

    case_pat   = re.compile(
        r"(\d+[.．]\s*[一-鿿]{2,8}[　\s][一-鿿]{3,12}"
        r"[证一二三四五六七八九十]*)",
        re.MULTILINE,
    )
    tongue_pat = re.compile(
        r"舌象特征[　\s]*\n?\s*(舌[一-鿿，。、\s]{5,100})",
        re.MULTILINE,
    )
    diag_pat   = re.compile(
        r"中医诊断[　\s]*\n?\s*([一-鿿，、。]+)",
        re.MULTILINE,
    )
    treat_pat  = re.compile(
        r"治则治法[　\s]*\n?\s*([一-鿿，、。]+)",
        re.MULTILINE,
    )

    parts  = case_pat.split(text)
    chunks: list[dict] = []

    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body   = parts[i + 1] if i + 1 < len(parts) else ""

        tongue_m = tongue_pat.search(body)
        diag_m   = diag_pat.search(body)
        treat_m  = treat_pat.search(body)

        tongue_text = tongue_m.group(1).strip() if tongue_m else ""
        if not tongue_text:
            continue

        diag_text  = diag_m.group(1).strip()  if diag_m  else ""
        treat_text = treat_m.group(1).strip() if treat_m else ""

        parts_list = [header]
        parts_list.append(f"舌象：{tongue_text}")
        if diag_text:
            parts_list.append(f"诊断：{diag_text}")
        if treat_text:
            parts_list.append(f"治法：{treat_text}")

        snippet = " | ".join(parts_list)
        if len(snippet) >= MIN_CHUNK_LEN:
            chunks.append({"text": snippet, "source": source})

    if not chunks:
        for para in re.split(r"\n{2,}", text):
            para = para.strip()
            if len(para) >= MIN_CHUNK_LEN:
                chunks.append({"text": para, "source": source})

    return chunks


def load_documents(kb_dir: Path = KB_DIR) -> list[dict]:
    """Load all non-JSON files from kb_dir and return a flat list of chunks."""
    docs: list[dict] = []
    for path in sorted(kb_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() == ".json":
            continue
        try:
            sample = path.read_text(encoding="utf-8", errors="replace")[:3000]
            if "舌象特征" in sample and "初诊时间" in sample:
                chunks = _load_case_file(path)
            else:
                chunks = _load_theory_file(path)
            docs.extend(chunks)
            print(f"[rag] loaded {len(chunks)} chunks from {path.name}")
        except Exception as exc:
            print(f"[rag] skipped {path.name}: {exc}")
    return docs


# ---------------------------------------------------------------------------
# TF-IDF index  (char n-grams — no extra tokenizer needed for Chinese)
# ---------------------------------------------------------------------------

class TongueKnowledgeBase:
    """Lazy-initialised TF-IDF index over the kb/ text files."""

    def __init__(self, kb_dir: Path = KB_DIR) -> None:
        self._kb_dir = kb_dir
        self._docs: list[dict] = []
        self._vec: Optional[TfidfVectorizer] = None
        self._matrix = None  # sparse (n_docs × n_features)

    def _build(self) -> None:
        self._docs = load_documents(self._kb_dir)
        if not self._docs:
            print("[rag] warning: no documents found in kb/")
            return
        self._vec = TfidfVectorizer(
            analyzer="char",
            ngram_range=(1, 3),
            min_df=1,
            sublinear_tf=True,
        )
        self._matrix = self._vec.fit_transform([d["text"] for d in self._docs])
        print(f"[rag] index ready — {len(self._docs)} chunks total")

    def _ensure(self) -> None:
        if self._vec is None:
            self._build()

    def retrieve(
        self,
        detected_labels: list[str],
        top_k: int = 5,
        min_sim: float = 0.05,
    ) -> list[dict]:
        """
        Return up to top_k relevant chunks for the given YOLO label slugs.

        Each result dict: {"text": str, "source": str, "similarity": float}
        """
        self._ensure()
        if not self._docs or self._vec is None:
            return []

        query = " ".join(
            LABEL_TERMS[lbl] for lbl in detected_labels if lbl in LABEL_TERMS
        )
        if not query:
            return []

        q_vec = self._vec.transform([query])
        sims  = cosine_similarity(q_vec, self._matrix)[0]
        order = np.argsort(sims)[::-1]

        results: list[dict] = []
        seen:    set[str]   = set()
        for idx in order:
            sim = float(sims[idx])
            if sim < min_sim:
                break
            doc = self._docs[idx]
            key = doc["text"][:80]
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "text":       doc["text"],
                "source":     doc["source"],
                "similarity": round(sim, 4),
            })
            if len(results) >= top_k:
                break
        return results


# Module-level singleton — built once per process on first call
_kb = TongueKnowledgeBase()


def retrieve(
    detected_labels: list[str],
    top_k: int = 5,
    min_sim: float = 0.05,
) -> list[dict]:
    """Retrieve top_k relevant knowledge-base chunks for a list of YOLO label slugs."""
    return _kb.retrieve(detected_labels, top_k=top_k, min_sim=min_sim)
