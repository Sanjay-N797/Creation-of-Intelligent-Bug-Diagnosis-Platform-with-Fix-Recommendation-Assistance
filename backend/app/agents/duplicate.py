import re
from typing import Dict, Any, List
from backend.app.utils.similarity import calculate_similarity, compute_tfidf_similarity

class DuplicateDetectionAgent:
    def __init__(self):
        self.name = "Duplicate Detection Agent"
        self.icon = "🔄"
        self.SIMILARITY_THRESHOLD = 15

    def analyze(self, bug_report: Dict[str, Any], resolved_bugs: List[Dict[str, Any]]) -> Dict[str, Any]:
        title = bug_report.get("title", "")
        description = bug_report.get("description", "")
        stack_trace = bug_report.get("stackTrace", "") or bug_report.get("stack_trace", "") or ""
        combined_text = f"{title} {description} {stack_trace}"

        similarities = self._compute_similarities(combined_text, resolved_bugs)
        duplicates = self._filter_duplicates(similarities)
        exact_matches = self._find_exact_matches(title, resolved_bugs)
        category_matches = self._find_category_matches(bug_report.get("category"), resolved_bugs)

        high_conf = [d for d in duplicates if d["similarity"] >= 50]

        top_dup = duplicates[0] if duplicates else {}
        is_dup = len(duplicates) > 0 and top_dup.get("similarity", 0) >= 20

        return {
            "agent": self.name,
            "icon": self.icon,
            "isDuplicate": is_dup,
            "hasDuplicates": is_dup,
            "similarityScore": top_dup.get("similarity", 0),
            "matchedBugId": top_dup.get("id"),
            "matchedBugTitle": top_dup.get("title"),
            "historicalResolution": top_dup.get("resolution"),
            "duplicates": duplicates,
            "exactMatches": exact_matches,
            "categoryMatches": category_matches,
            "highConfidenceDuplicates": high_conf,
            "summary": self._generate_summary(duplicates),
            "details": {
                "vectorEngine": "scikit-learn TfidfVectorizer + Cosine Similarity",
                "status": f"🔄 Found {len(duplicates)} similar bug(s) in the database" if duplicates else "✅ No similar bugs found — this is a unique issue",
                "duplicates": [
                    {
                        "display": f"{d['id']}: {d['title']}",
                        "similarity": f"{d['similarity']}% TF-IDF Cosine Match (Title: {d['titleSimilarity']}%, Content: {d['contentSimilarity']}%, Error: {d['errorSimilarity']}%)",
                        "resolution": d["resolution"],
                        "status": d["status"]
                    } for d in duplicates
                ],
                "exactMatches": [f"⚡ Exact title match: {m['id']} — {m['title']}" for m in exact_matches],
                "recommendation": self._get_recommendation(duplicates)
            }
        }


    def _compute_similarities(self, new_text: str, bugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not bugs:
            return []

        corpus_texts = [f"{b.get('title', '')} {b.get('description', '')} {b.get('stack_trace', '')}" for b in bugs]
        tfidf_sims = compute_tfidf_similarity(new_text, corpus_texts)

        results = []
        for idx, bug in enumerate(bugs):
            bug_text = corpus_texts[idx]
            tfidf_sim = tfidf_sims[idx]

            title_sim = calculate_similarity(" ".join(new_text.split()[:20]), bug.get("title", ""))
            error_sim = self._compare_error_types(new_text, bug_text)

            combined_sim = round(tfidf_sim * 60 + title_sim * 25 + error_sim * 15)
            final_sim = min(99, combined_sim)

            results.append({
                "bug": bug,
                "similarity": final_sim,
                "titleSimilarity": round(title_sim * 100),
                "contentSimilarity": round(tfidf_sim * 100),
                "errorSimilarity": round(error_sim * 100)
            })
        return results

    def _compare_error_types(self, text1: str, text2: str) -> float:
        pattern = re.compile(r'(\w+(?:Error|Exception|Failure))', re.IGNORECASE)
        errors1 = set(m.lower() for m in pattern.findall(text1))
        errors2 = set(m.lower() for m in pattern.findall(text2))

        if not errors1 or not errors2:
            return 0.0

        intersection = errors1.intersection(errors2)
        union = errors1.union(errors2)
        return len(intersection) / len(union) if union else 0.0

    def _filter_duplicates(self, similarities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered = [s for s in similarities if s["similarity"] >= self.SIMILARITY_THRESHOLD]
        sorted_sims = sorted(filtered, key=lambda x: x["similarity"], reverse=True)[:5]

        out = []
        for item in sorted_sims:
            b = item["bug"]
            out.append({
                "id": b.get("bug_code") or f"BUG-{b.get('id'):03d}",
                "title": b.get("title"),
                "category": b.get("category"),
                "severity": b.get("severity"),
                "status": b.get("status"),
                "similarity": item["similarity"],
                "titleSimilarity": item["titleSimilarity"],
                "contentSimilarity": item["contentSimilarity"],
                "errorSimilarity": item["errorSimilarity"],
                "rootCause": b.get("root_cause") or "Not documented",
                "resolution": b.get("resolution") or "Not documented",
                "dateResolved": str(b.get("date_resolved")) if b.get("date_resolved") else None
            })
        return out

    def _find_exact_matches(self, title: str, bugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not title:
            return []
        lower_t = title.lower()
        matches = []
        for b in bugs:
            if b.get("title", "").lower() == lower_t:
                matches.append({
                    "id": b.get("bug_code") or f"BUG-{b.get('id'):03d}",
                    "title": b.get("title"),
                    "resolution": b.get("resolution")
                })
        return matches

    def _find_category_matches(self, category: str, bugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not category or category == "Auto-detect":
            return []
        matches = []
        for b in bugs:
            if b.get("category") == category:
                matches.append({
                    "id": b.get("bug_code") or f"BUG-{b.get('id'):03d}",
                    "title": b.get("title"),
                    "similarity": "Category Match"
                })
        return matches[:3]

    def _generate_summary(self, duplicates: List[Dict[str, Any]]) -> str:
        if not duplicates:
            return "✅ No duplicate bugs found — this appears to be a new issue."
        highest = duplicates[0]
        if highest["similarity"] >= 70:
            return f"⚠️ HIGH MATCH: {highest['id']} \"{highest['title']}\" ({highest['similarity']}% similar) — likely duplicate!"
        elif highest["similarity"] >= 40:
            return f"🔍 POSSIBLE MATCH: {highest['id']} \"{highest['title']}\" ({highest['similarity']}% similar) — review recommended."
        else:
            return f"📋 {len(duplicates)} partially similar bug(s) found — closest match: {highest['similarity']}% similar."

    def _get_recommendation(self, duplicates: List[Dict[str, Any]]) -> str:
        if not duplicates:
            return "➡️ Proceed with full analysis — no prior resolution available."
        highest = duplicates[0]
        if highest["similarity"] >= 70:
            return f"🔗 Strongly recommend reviewing {highest['id']} resolution before proceeding."
        return "📖 Review similar bugs for potential insights before investigating from scratch."
