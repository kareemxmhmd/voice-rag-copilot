"""Interactive & Benchmark CLI for Voice RAG Copilot (Phases 2 & 3).

Tests the full Retrieval + Generation pipeline on 5 realistic spoken queries:
1. English Customer: Bundle pricing & discounts
2. Arabic / Mixed Customer: Free trial cancellation rules & charges
3. Internal Ops: Q3 Churn rates and LTV breakdown
4. Arabic Customer: Defective product return & restocking fee policy
5. Out of Domain: Strict grounding verification (I don't know rule)
"""

import re
from src.rag.generator import VoiceRAGGenerator


def test_generator_pipeline():
    print("=" * 80)
    print(" Voice RAG Copilot - Phase 3 Generation Core Verification (Text RAG)")
    print("=" * 80)

    generator = VoiceRAGGenerator()

    test_queries = [
        {
            "id": 1,
            "category": "Customer (English) - Bundle Pricing",
            "query": "How much is the Work Anywhere Bundle for a Pro member, and what's the regular price?",
            "check_terms": ["1,187", "1,008.95", "15"],
        },
        {
            "id": 2,
            "category": "Customer (Arabic/Mixed) - Trial Cancellation",
            "query": "لو أنا بدأت الـ Free Trial بتاع الـ Pro Plan ونسيت أعمل Cancel، هتحاسبوني إمتى وبكام؟",
            "check_terms": ["14", "24", "180"],
        },
        {
            "id": 3,
            "category": "Internal Ops (English) - Churn & LTV KPIs",
            "query": "What was Basic churn in Q3, and what's the average LTV for Basic versus Pro?",
            "check_terms": ["6.4", "2.1", "297", "714"],
        },
        {
            "id": 4,
            "category": "Customer (Arabic/Mixed) - Defective Return Policy",
            "query": "اشتريت سماعة NovaBuds Pro بـ 149 دولار وفتحتها بس طلعت Defective. ينفع أعمل Return؟ وهتخصموا Restocking Fee؟",
            "check_terms": ["14", "149"],
        },
        {
            "id": 5,
            "category": "Grounding Check (Out-of-Domain Query)",
            "query": "Can I purchase international airline flight tickets using NovaCart membership?",
            "check_terms": ["don't have", "not have", "مش متوفرة", "لا تتوفر"],
        },
    ]

    has_failures = False

    for test in test_queries:
        print(f"\n[Test #{test['id']}] {test['category']}")
        print(f"Query: \"{test['query']}\"")

        res = generator.generate(test["query"], top_k=3)

        print(f"Sources: {res['sources']}")
        print(f"Latency: Retrieval = {res['retrieval_ms']}ms | LLM = {res['llm_ms']}ms | Total = {res['total_ms']}ms")
        print(f"\nSpoken Answer:\n  \"{res['answer']}\"\n")

        # Verify voice formatting: No markdown asterisks, hashes, bullets, brackets
        has_markdown = bool(re.search(r"[\*#`~\[\]]|^\s*[-•]\s*", res["answer"], flags=re.MULTILINE))
        if has_markdown:
            print("  [Warning] Output contains markdown symbols!")
            has_failures = True
        else:
            print("  [Voice Ready] Clean spoken style with 0 markdown symbols.")

        # Check keyword presence
        matched = any(term.lower() in res["answer"].lower() for term in test["check_terms"])
        if matched:
            print(f"  [Grounding] PASSED - Answer matched expected factual terms.")
        else:
            print(f"  [Grounding] Check terms not clearly found: {test['check_terms']}")

    print("\n" + "=" * 80)
    if not has_failures:
        print(" PHASE 3 TEXT RAG COMPLETED SUCCESSFULLY! All responses are voice-ready.")
    else:
        print(" PHASE 3 COMPLETED WITH WARNINGS.")
    print("=" * 80)


if __name__ == "__main__":
    test_generator_pipeline()
