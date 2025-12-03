"""Test citation enforcement with 5 questions about humor in the book."""
import re
import subprocess
import argparse
from typing import Dict, List, Tuple

# Test questions in Russian about humor in "The Old Man and the Sea"
QUESTIONS = [
    # "Какие моменты в книге можно считать юмористическими, несмотря на серьёзный тон повествования?",
    "Как Сантьяго сам над собой шутит во время борьбы с рыбой или трудностей в море?",
    # "Есть ли в диалогах Сантьяго и Манолина лёгкие или ироничные реплики, создающие ощущение тёплого юмора?",
    # "Какие сравнения или наблюдения Сантьяго можно трактовать как скрытую иронию?",
    # "Использует ли автор юмор для раскрытия характера старика? Если да — какие эпизоды это показывают?"
]


def run_question(question: str, use_rerank: bool = False, enforce_citations: bool = True) -> Dict:
    """Run a single question and capture the output."""
    cmd = [
        "uv", "run", "python", "main.py", "index", "ask",
        question,
        "--model", "openai/gpt-4o-mini",
        "--top-k", "5"
    ]

    if use_rerank:
        cmd.extend(["--rerank", "--rerank-model", "openai/gpt-4o-mini", "--threshold", "0.5"])

    # Add citation flag
    if enforce_citations:
        cmd.append("--citations")
    else:
        cmd.append("--no-citations")

    print(f"\n{'='*80}")
    print(f"Question: {question}")
    print(f"Reranking: {'YES' if use_rerank else 'NO'}")
    print(f"Citations: {'ENFORCED' if enforce_citations else 'DISABLED'}")
    print('='*80)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )

    output = result.stdout

    # Extract answer section
    answer_match = re.search(r'Answer:\s*\n\n(.+?)(?=\n\n✓|⚠|Sources:|$)', output, re.DOTALL)
    answer = answer_match.group(1).strip() if answer_match else ""

    # Check for citations
    citations = re.findall(r'\[Doc\d+\]', answer)
    has_citations = len(citations) > 0
    unique_citations = len(set(citations))

    # Check for citation warning
    has_warning = "⚠ Warning: No citations found" in output

    return {
        'question': question,
        'answer': answer,
        'citations': citations,
        'has_citations': has_citations,
        'unique_citations': unique_citations,
        'has_warning': has_warning,
        'full_output': output
    }


def analyze_results(results: List[Dict]) -> None:
    """Analyze and display test results."""
    print("\n\n" + "="*80)
    print("CITATION ANALYSIS RESULTS")
    print("="*80)

    total = len(results)
    with_citations = sum(1 for r in results if r['has_citations'])
    without_citations = total - with_citations

    print(f"\nTotal questions tested: {total}")
    print(f"Answers with citations: {with_citations}/{total} ({with_citations/total*100:.1f}%)")
    print(f"Answers without citations: {without_citations}/{total} ({without_citations/total*100:.1f}%)")

    print("\n" + "-"*80)
    print("DETAILED RESULTS:")
    print("-"*80)

    for i, result in enumerate(results, 1):
        print(f"\nQuestion {i}:")
        print(f"  Text: {result['question'][:80]}...")
        print(f"  Citations found: {'✓ YES' if result['has_citations'] else '✗ NO'}")
        if result['has_citations']:
            print(f"  Total citations: {len(result['citations'])}")
            print(f"  Unique sources: {result['unique_citations']}")
            print(f"  Citations: {', '.join(sorted(set(result['citations'])))}")
        print(f"  Warning shown: {'YES' if result['has_warning'] else 'NO'}")

        # Show the full answer
        print("\n  Full Answer:")
        print("  " + "-" * 76)
        for line in result['answer'].split('\n'):
            print(f"  {line}")
        print("  " + "-" * 76)


def main():
    """Run all test questions."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Test citation enforcement in RAG system'
    )
    parser.add_argument(
        '--citations',
        dest='enforce_citations',
        action='store_true',
        default=True,
        help='Enforce citation format in answers (default)'
    )
    parser.add_argument(
        '--no-citations',
        dest='enforce_citations',
        action='store_false',
        help='Disable citation enforcement'
    )
    args = parser.parse_args()

    citation_mode = "ENABLED" if args.enforce_citations else "DISABLED"

    print("Testing Citation Enforcement in RAG System")
    print("=" * 80)
    print("\nRunning 5 questions about humor in 'The Old Man and the Sea'")
    print(f"Citation mode: {citation_mode}")
    print("Testing both with and without reranking\n")

    # Test without reranking
    print("\n" + "="*80)
    print("PART 1: Testing WITHOUT Reranking")
    print(f"Citations: {citation_mode}")
    print("="*80)
    results_no_rerank = []
    for question in QUESTIONS:
        try:
            result = run_question(
                question,
                use_rerank=False,
                enforce_citations=args.enforce_citations
            )
            results_no_rerank.append(result)
            print(f"\n✓ Completed question {len(results_no_rerank)}/5")
        except Exception as e:
            print(f"\n✗ Error: {e}")

    # Test with reranking
    print("\n\n" + "="*80)
    print("PART 2: Testing WITH Reranking")
    print(f"Citations: {citation_mode}")
    print("="*80)
    results_with_rerank = []
    for question in QUESTIONS:
        try:
            result = run_question(
                question,
                use_rerank=True,
                enforce_citations=args.enforce_citations
            )
            results_with_rerank.append(result)
            print(f"\n✓ Completed question {len(results_with_rerank)}/5")
        except Exception as e:
            print(f"\n✗ Error: {e}")

    # Analyze results
    print("\n\n" + "="*80)
    print("WITHOUT RERANKING RESULTS")
    analyze_results(results_no_rerank)

    print("\n\n" + "="*80)
    print("WITH RERANKING RESULTS")
    analyze_results(results_with_rerank)

    # Comparison
    print("\n\n" + "="*80)
    print("COMPARISON: Reranking vs No Reranking")
    print("="*80)

    no_rerank_citation_rate = sum(1 for r in results_no_rerank if r['has_citations']) / len(results_no_rerank) * 100
    rerank_citation_rate = sum(1 for r in results_with_rerank if r['has_citations']) / len(results_with_rerank) * 100

    print(f"\nCitation rate without reranking: {no_rerank_citation_rate:.1f}%")
    print(f"Citation rate with reranking: {rerank_citation_rate:.1f}%")

    avg_citations_no_rerank = sum(len(r['citations']) for r in results_no_rerank) / len(results_no_rerank)
    avg_citations_rerank = sum(len(r['citations']) for r in results_with_rerank) / len(results_with_rerank)

    print(f"\nAverage citations per answer (no rerank): {avg_citations_no_rerank:.1f}")
    print(f"Average citations per answer (with rerank): {avg_citations_rerank:.1f}")

    print("\n" + "="*80)
    print("HALLUCINATION ANALYSIS")
    print("="*80)
    print("\nTo assess hallucinations, manually review the answers above and check:")
    print("1. Do cited facts actually appear in the source documents?")
    print("2. Are there uncited claims that seem invented?")
    print("3. Does reranking help reduce irrelevant context and improve accuracy?")


if __name__ == "__main__":
    main()
