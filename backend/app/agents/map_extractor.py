from app.agents.base import BaseMAPExtractor
import re

# ── OLLAMA VERSION (disabled — requires more RAM) ─────────────────────────────
#
# from langchain_ollama import ChatOllama
# from langchain.prompts import ChatPromptTemplate
# import json
#
# FEW_SHOT_EXAMPLES = """
# Example 1:
# Circular: "All scheduled commercial banks shall maintain CRR at 4.50% of their Net Demand and Time Liabilities effective from the fortnight beginning October 2024."
# MAPs:
# [{"action": "Maintain CRR at 4.50% of NDTL effective fortnight beginning October 2024", "confidence": 0.95}]
# """
#
# PROMPT = ChatPromptTemplate.from_template("""
# You are a regulatory compliance analyst. Extract all Mandatory Action Points (MAPs) from the circular below.
# {few_shot}
# Circular: "{circular_text}"
# Respond ONLY with valid JSON:
# {{"maps": [{{"action": "...", "confidence": 0.0_to_1.0}}], "confidence": overall_confidence_0_to_1}}
# """)
#
# class MAPExtractor(BaseMAPExtractor):
#     def __init__(self):
#         self.llm = ChatOllama(model="qwen2.5", temperature=0, base_url="http://localhost:11434")
#     def extract(self, doc: dict) -> dict:
#         chain = PROMPT | self.llm
#         response = chain.invoke({"few_shot": FEW_SHOT_EXAMPLES, "circular_text": doc["text"][:12000]})
#         try:
#             return json.loads(response.content)
#         except:
#             return {"maps": [], "confidence": 0.0}

# ── ACTIVE VERSION (rule-based — fully offline, no RAM needed) ────────────────

OBLIGATION_PATTERNS = [
    r"[^.]{0,60}(?:shall|must|are required to|is required to|are mandated to|is mandated to)[^.]{10,250}\.",
    r"[^.]{0,60}(?:all banks|all entities|all regulated entities|all listed entities|all scheduled)[^.]{10,250}\.",
    r"[^.]{0,60}(?:banks shall|entities shall|companies shall|intermediaries shall)[^.]{10,250}\.",
    r"[^.]{0,60}(?:it is mandatory|mandatory requirement|compliance is required)[^.]{10,250}\.",
]

NOISE_PHRASES = [
    "means ", "defined as", "refers to", "for the purpose",
    "in this circular", "as per rbi", "background", "preamble",
    "it may be recalled", "attention is invited", "please refer",
]


class MAPExtractor(BaseMAPExtractor):
    def __init__(self):
        pass  # no model needed

    def extract(self, doc: dict) -> dict:
        text = doc["text"][:15000]
        text = re.sub(r'\s+', ' ', text).strip()

        # Split text into sentences roughly by period
        sentences = re.split(r'\.', text)

        maps = []
        seen = set()
        keywords = ['shall', 'must', 'required to', 'mandated to', 'advised to', 'directed to']

        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip sentences that are too short or too long
            if len(sentence) < 40 or len(sentence) > 800:
                continue

            if any(noise in sentence.lower() for noise in NOISE_PHRASES):
                continue

            if any(re.search(r'\b' + kw + r'\b', sentence, re.IGNORECASE) for kw in keywords):
                key = sentence[:80].lower()
                if key in seen:
                    continue
                seen.add(key)

                if 'shall' in sentence.lower() or 'must' in sentence.lower():
                    confidence = 0.88
                elif 'required' in sentence.lower() or 'mandated' in sentence.lower():
                    confidence = 0.82
                else:
                    confidence = 0.75

                maps.append({"action": sentence + ".", "confidence": confidence})

        overall_confidence = round(sum(m["confidence"] for m in maps) / len(maps), 2) if maps else 0.0

        print(f"=== MAP EXTRACTOR: found {len(maps)} MAPs ===")
        for i, m in enumerate(maps, 1):
            print(f"  {i}. [{m['confidence']}] {m['action'][:100]}...")

        return {"maps": maps, "confidence": overall_confidence}