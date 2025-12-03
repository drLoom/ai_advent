# Citation Test Script Usage Examples

The `test_citations.py` script now supports `--citations/--no-citations` flags to test both modes.

## Basic Usage

### 1. Test with Citations Enabled (Default)
```bash
uv run python test_citations.py
```
**What it does:**
- Tests 5 questions about humor in "The Old Man and the Sea"
- Tests both with and without reranking
- Enforces citation format in all answers
- Validates that `[Doc#]` citations are present
- Shows warnings if citations are missing

**Output includes:**
- Full answers with `[Doc#]` citations
- Citation count per answer
- Validation messages (✓ or ⚠)
- Detailed analysis comparing reranking modes

---

### 2. Test with Citations Explicitly Enabled
```bash
uv run python test_citations.py --citations
```
**Same as default** - makes citation enforcement explicit.

---

### 3. Test with Citations Disabled
```bash
uv run python test_citations.py --no-citations
```
**What it does:**
- Tests same 5 questions
- Disables citation enforcement
- Generates more natural, flowing answers
- No citation validation performed
- No `[Doc#]` markers in responses

**Output includes:**
- Natural language answers without citations
- No validation messages
- Comparison of answer styles
- Demonstrates readability difference

---

## Comparison Example

### Test Both Modes Side-by-Side

**Step 1: Run with citations**
```bash
uv run python test_citations.py --citations > citations_enabled.txt
```

**Step 2: Run without citations**
```bash
uv run python test_citations.py --no-citations > citations_disabled.txt
```

**Step 3: Compare**
```bash
diff citations_enabled.txt citations_disabled.txt
# or use a visual diff tool
code --diff citations_enabled.txt citations_disabled.txt
```

---

## Understanding the Output

### With Citations Enabled

```
Question: Какие моменты в книге можно считать юмористическими?
Reranking: NO
Citations: ENFORCED
================================================================================

Answer:

В книге можно выделить несколько юмористических моментов [Doc1]. 
Старик и молодой рыбак обсуждают лотерейный билет с номером 87 [Doc2].

✓ Citations present: 2 unique sources cited

Question 1:
  Text: Какие моменты в книге можно считать юмористическими...
  Citations found: ✓ YES
  Total citations: 2
  Unique sources: 2
  Citations: [Doc1], [Doc2]
  Warning shown: NO
```

### With Citations Disabled

```
Question: Какие моменты в книге можно считать юмористическими?
Reranking: NO
Citations: DISABLED
================================================================================

Answer:

В книге можно выделить несколько юмористических моментов. 
Старик и молодой рыбак обсуждают лотерейный билет с номером 87.

Question 1:
  Text: Какие моменты в книге можно считать юмористическими...
  Citations found: ✗ NO
  Warning shown: NO
```

---

## Use Cases

### 1. Citation System Validation
**Goal:** Verify that citation enforcement works correctly
```bash
uv run python test_citations.py --citations
```
**Check for:**
- 100% citation rate (5/5 questions)
- All answers include `[Doc#]` markers
- No warning messages
- Citations properly formatted

---

### 2. Natural Language Quality Check
**Goal:** Test answer quality without citation overhead
```bash
uv run python test_citations.py --no-citations
```
**Check for:**
- Answers are coherent and complete
- Natural language flow
- Same factual content as cited version
- Better readability

---

### 3. Hallucination Testing
**Goal:** Compare factual accuracy between modes
```bash
# Run both tests and compare manually
uv run python test_citations.py --citations > with_citations.txt
uv run python test_citations.py --no-citations > without_citations.txt
```
**Manual review:**
- Do both modes report same facts?
- Are there invented details in either version?
- Does citation mode reduce hallucinations?

---

### 4. Performance Comparison
**Goal:** Measure impact of citation enforcement
```bash
# Time with citations
time uv run python test_citations.py --citations

# Time without citations
time uv run python test_citations.py --no-citations
```
**Compare:**
- Execution time difference
- Token usage (if logged)
- Answer length differences

---

## Integration with CI/CD

### Example: GitHub Actions

```yaml
name: Test Citation System

on: [push, pull_request]

jobs:
  test-citations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test with citations
        run: uv run python test_citations.py --citations
      - name: Test without citations
        run: uv run python test_citations.py --no-citations
      - name: Archive results
        uses: actions/upload-artifact@v2
        with:
          name: citation-test-results
          path: citation_test_results.txt
```

---

## Troubleshooting

### Issue: No citations found in enforced mode

**Symptom:**
```
⚠ Warning: No citations found in response
```

**Possible causes:**
1. LLM not following instructions
2. Model doesn't support citations well
3. Retrieved context is irrelevant

**Solutions:**
- Try different model (e.g., `gpt-4o-mini`)
- Increase `--top-k` for more context
- Use `--rerank` for better relevance

---

### Issue: Test takes too long

**Solutions:**
```bash
# Reduce number of questions in test_citations.py
# or use faster model
uv run python test_citations.py --citations  # Uses gpt-4o-mini by default
```

---

## Advanced Usage

### Custom Question Set

Edit `test_citations.py` to test your own questions:

```python
QUESTIONS = [
    "Your custom question 1",
    "Your custom question 2",
    # Add more...
]
```

Then run:
```bash
uv run python test_citations.py --citations
```

---

## Expected Results

### Citation Mode (--citations)
- **Citation rate:** 80-100%
- **Average citations per answer:** 2-4
- **Validation messages:** Present
- **Answer length:** Longer (includes citations)

### Natural Mode (--no-citations)
- **Citation rate:** 0-10% (incidental)
- **Average citations per answer:** 0
- **Validation messages:** None
- **Answer length:** Shorter, more concise

---

## Documentation References

- **Main README:** [README.md](README.md)
- **Citation Test Report:** [CITATION_TEST_REPORT.md](CITATION_TEST_REPORT.md)
- **Citation Modes Guide:** [CITATION_MODES.md](CITATION_MODES.md)

---

*Last updated: December 3, 2025*
