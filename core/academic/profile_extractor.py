from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from core.ai_engine.config import get_vectorstore
from core.models import AcademicDocument


MAJOR_KEYWORDS: Dict[str, List[str]] = {
    "Teknik Informatika": ["teknik informatika", "informatika", "ilmu komputer", "computer science"],
    "Sistem Informasi": ["sistem informasi", "information systems"],
    "Teknik Elektro": ["teknik elektro", "elektro", "electrical engineering"],
    "Teknik Mesin": ["teknik mesin", "mesin", "mechanical engineering"],
    "Teknik Industri": ["teknik industri", "industrial engineering"],
    "Manajemen": ["manajemen", "management"],
    "Akuntansi": ["akuntansi", "accounting"],
    "Hukum": ["hukum", "law"],
    "Psikologi": ["psikologi", "psychology"],
}

CAREER_KEYWORDS: Dict[str, List[str]] = {
    "Software Engineer": ["software engineer", "backend developer", "frontend developer", "full stack"],
    "Data Scientist": ["data scientist", "machine learning", "data analyst", "ai engineer"],
    "UI/UX Designer": ["ui ux", "ux designer", "product designer", "user experience"],
    "Cybersecurity": ["cybersecurity", "security analyst", "penetration tester", "infosec"],
    "Product Manager": ["product manager", "product management"],
}

_MAJOR_LINE_RE = re.compile(r"(program studi|prodi|jurusan)\s*[:\-]?\s*([^\n\r,.;]{3,80})", re.IGNORECASE)
_CAREER_LINE_RE = re.compile(r"(target karir|career|tujuan karir)\s*[:\-]?\s*([^\n\r,.;]{3,80})", re.IGNORECASE)
_SEMESTER_RE = re.compile(r"\b(?:semester|smt|sem)\s*[:\-]?\s*(\d{1,2})\b", re.IGNORECASE)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _confidence_from_score(score: float) -> float:
    if score >= 5:
        return 0.95
    if score >= 3.5:
        return 0.82
    if score >= 2:
        return 0.68
    if score >= 1:
        return 0.52
    return 0.35


def _summary_confidence(max_score: float) -> str:
    if max_score >= 4:
        return "high"
    if max_score >= 2:
        return "medium"
    return "low"


def _record_hit(
    scores: Dict[str, float],
    evidences: Dict[str, List[str]],
    key: str,
    score: float,
    evidence: str,
) -> None:
    scores[key] += score
    if evidence and evidence not in evidences[key]:
        evidences[key].append(evidence[:180])


def _match_map_from_text(
    text: str,
    source: str,
    mapping: Dict[str, List[str]],
    explicit_re: re.Pattern[str] | None,
) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
    scores: Dict[str, float] = defaultdict(float)
    evidences: Dict[str, List[str]] = defaultdict(list)
    low = _norm(text)

    if explicit_re:
        for m in explicit_re.finditer(text or ""):
            val = _norm(m.group(2))
            for label, aliases in mapping.items():
                if any(_norm(a) in val for a in aliases):
                    _record_hit(scores, evidences, label, 3.0, f"{source}: {m.group(0)}")

    for label, aliases in mapping.items():
        for a in aliases:
            if _norm(a) in low:
                _record_hit(scores, evidences, label, 1.1, f"{source}: {a}")
                break

    return scores, evidences


def _merge_scores(
    target_scores: Dict[str, float],
    target_evidence: Dict[str, List[str]],
    add_scores: Dict[str, float],
    add_evidence: Dict[str, List[str]],
) -> None:
    for k, v in add_scores.items():
        target_scores[k] += float(v or 0)
    for k, vals in add_evidence.items():
        for e in vals:
            if e not in target_evidence[k]:
                target_evidence[k].append(e)


def _rank_candidates(
    scores: Dict[str, float],
    evidences: Dict[str, List[str]],
    as_semester: bool = False,
) -> List[Dict[str, Any]]:
    items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    out: List[Dict[str, Any]] = []
    for key, score in items[:5]:
        if score <= 0:
            continue
        item: Dict[str, Any] = {
            "value": int(key) if as_semester else key,
            "label": f"Semester {int(key)}" if as_semester else key,
            "confidence": _confidence_from_score(score),
            "evidence": evidences.get(key, [])[:3],
        }
        out.append(item)
    return out


def _collect_semester_candidates(texts: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    scores: Dict[str, float] = defaultdict(float)
    evidences: Dict[str, List[str]] = defaultdict(list)
    for source, text in texts:
        for m in _SEMESTER_RE.finditer(text or ""):
            sem = m.group(1)
            try:
                sem_int = int(sem)
            except Exception:
                continue
            if sem_int < 1 or sem_int > 14:
                continue
            key = str(sem_int)
            _record_hit(scores, evidences, key, 1.8, f"{source}: {m.group(0)}")
    return _rank_candidates(scores, evidences, as_semester=True)


def _gather_texts(user) -> Tuple[List[Tuple[str, str]], List[str]]:
    docs = AcademicDocument.objects.filter(user=user, is_embedded=True).order_by("-uploaded_at")
    doc_titles = [str(d.title or "") for d in docs]
    texts: List[Tuple[str, str]] = []

    for t in doc_titles:
        if t:
            texts.append((f"title:{t}", t))

    try:
        vectorstore = get_vectorstore()
        chunks = vectorstore.similarity_search(
            "program studi prodi jurusan semester target karir career pekerjaan",
            k=25,
            filter={"user_id": str(user.id)},
        )
        for c in chunks:
            content = str(getattr(c, "page_content", "") or "").strip()
            if not content:
                continue
            source = str((getattr(c, "metadata", {}) or {}).get("source") or "chunk")
            texts.append((f"chunk:{source}", content[:1500]))
    except Exception:
        # fallback: title-only mode
        pass

    return texts, doc_titles


def extract_profile_hints(user) -> Dict[str, Any]:
    texts, doc_titles = _gather_texts(user)
    has_docs = bool(doc_titles)

    major_scores: Dict[str, float] = defaultdict(float)
    major_evidence: Dict[str, List[str]] = defaultdict(list)
    career_scores: Dict[str, float] = defaultdict(float)
    career_evidence: Dict[str, List[str]] = defaultdict(list)

    for source, text in texts:
        m_scores, m_evidence = _match_map_from_text(
            text=text,
            source=source,
            mapping=MAJOR_KEYWORDS,
            explicit_re=_MAJOR_LINE_RE,
        )
        c_scores, c_evidence = _match_map_from_text(
            text=text,
            source=source,
            mapping=CAREER_KEYWORDS,
            explicit_re=_CAREER_LINE_RE,
        )
        _merge_scores(major_scores, major_evidence, m_scores, m_evidence)
        _merge_scores(career_scores, career_evidence, c_scores, c_evidence)

    major_candidates = _rank_candidates(major_scores, major_evidence)
    career_candidates = _rank_candidates(career_scores, career_evidence)
    semester_candidates = _collect_semester_candidates(texts)

    max_major = max(major_scores.values(), default=0.0)
    max_career = max(career_scores.values(), default=0.0)
    max_semester = max((x.get("confidence", 0.0) for x in semester_candidates), default=0.0) * 5
    max_score = max(max_major, max_career, max_semester)

    confidence_summary = _summary_confidence(max_score)
    has_relevant_docs = bool(major_candidates or career_candidates or semester_candidates)

    warning = None
    if not has_docs:
        warning = "Upload sumber dengan data yang relevan agar jawaban konsisten."
    elif not has_relevant_docs or confidence_summary == "low":
        warning = "Upload sumber dengan data yang relevan agar jawaban konsisten."
    else:
        # konflik kandidat jika skor dua teratas berdekatan
        sorted_major = sorted(major_scores.values(), reverse=True)
        sorted_career = sorted(career_scores.values(), reverse=True)
        major_conflict = len(sorted_major) > 1 and abs(sorted_major[0] - sorted_major[1]) <= 0.5
        career_conflict = len(sorted_career) > 1 and abs(sorted_career[0] - sorted_career[1]) <= 0.5
        if major_conflict or career_conflict:
            warning = "Data dokumen terdeteksi beragam. Upload sumber yang lebih relevan agar jawaban konsisten."

    return {
        "major_candidates": major_candidates,
        "career_candidates": career_candidates,
        "semester_candidates": semester_candidates,
        "confidence_summary": confidence_summary,
        "has_relevant_docs": has_relevant_docs,
        "warning": warning,
    }

