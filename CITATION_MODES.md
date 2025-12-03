# Citation Modes Documentation

## Overview

The RAG system now supports **toggleable citation enforcement**, giving you control over whether answers should include mandatory source citations or be more naturally formatted.

## Modes

### 1. With Citations (Default) - `--citations`

**Command:**
```bash
uv run python main.py index ask "Who is Santiago?" --citations
# or simply (citations enabled by default):
uv run python main.py index ask "Who is Santiago?"
```

**Output Example:**
```
Сантьяго — это старик и главный герой, который известен как чемпион в 
состязаниях по борьбе. Он одержал победу над негром из Сьенфуэгоса в поединке, 
который длился с воскресенья до понедельника [Doc1]. 

Сантьяго также имеет опыт участия в нескольких других состязаниях, но вскоре 
решил оставить это занятие, поняв, что такие поединки вредят его правой руке, 
необходимой для рыбной ловли [Doc1].

✓ Citations present: 1 unique sources cited
```

**Features:**
- ✅ Every factual claim includes `[Doc#]` citation
- ✅ Automatic validation detects missing citations
- ✅ Warning shown if citations are missing
- ✅ Prevents hallucinations through source grounding
- ✅ Makes claims verifiable

**Best for:**
- Research and fact-checking
- Academic or professional use
- When accuracy and verifiability are critical
- Building trust in AI-generated answers
- Compliance and audit requirements

---

### 2. Without Citations - `--no-citations`

**Command:**
```bash
uv run python main.py index ask "Who is Santiago?" --no-citations
```

**Output Example:**
```
Сантьяго — это старик, который участвовал в состязаниях по борьбе и стал 
известен как Чемпион после победы над негром. Он также является рыбаком, который
осознал, что такие поединки вредят его правой руке, необходимой для ловли рыбы.
```

**Features:**
- ✅ More natural, flowing text
- ✅ Shorter, more concise answers
- ✅ Better readability for casual use
- ✅ Still grounded in source documents
- ✅ No citation validation overhead

**Best for:**
- Casual reading and exploration
- Quick answers without verification needs
- More natural conversational style
- When brevity is preferred
- Informal use cases

---

## Comparison

| Feature | With Citations | Without Citations |
|---------|---------------|-------------------|
| **Citation markers** | `[Doc#]` in text | None |
| **Validation** | Yes, automatic | No |
| **Answer length** | Longer (includes citations) | Shorter |
| **Readability** | More formal | More natural |
| **Verifiability** | High (every claim traceable) | Medium (sources shown separately) |
| **Use case** | Research, professional | Casual, quick answers |
| **Default** | ✓ Yes | No |

---

## Usage Examples

### Example 1: Research Mode (Citations ON)
```bash
uv run python main.py index ask "What are the key findings?" \
  --citations \
  --model "openai/gpt-4o-mini" \
  --rerank \
  --threshold 0.6
```
**Use case:** Academic research, fact verification, professional reports

### Example 2: Casual Reading (Citations OFF)
```bash
uv run python main.py index ask "What's the story about?" \
  --no-citations \
  --model "openai/gpt-4o-mini"
```
**Use case:** Personal reading, quick summaries, exploratory questions

### Example 3: Testing Both Modes
```bash
# With citations
uv run python main.py index ask "Who won the battle?" --citations

# Without citations
uv run python main.py index ask "Who won the battle?" --no-citations
```
**Use case:** Comparing output styles, choosing preference

---

## Technical Details

### Prompt Differences

**With Citations:**
- System prompt includes "CRITICAL REQUIREMENTS" for citation enforcement
- Requires `[Doc#]` format for every factual claim
- Provides citation format examples
- User prompt explicitly requests "mandatory citations"

**Without Citations:**
- System prompt uses softer "Guidelines"
- Suggests citing "when relevant" (optional)
- More flexible, natural language encouraged
- No mandatory citation requirements

### Validation

**With Citations:**
```
✓ Citations present: 3 unique sources cited
⚠ Warning: No citations found in response
```

**Without Citations:**
- No citation validation performed
- No warnings shown
- Sources still listed at the end if `--show-sources` is enabled

---

## Recommendations

### Use `--citations` when:
1. **Accuracy is critical** - Medical, legal, financial information
2. **Accountability required** - Professional reports, research papers
3. **Fact-checking needed** - Verifying claims, auditing information
4. **Building trust** - Demonstrating answer reliability to others
5. **Learning/studying** - Understanding where information comes from

### Use `--no-citations` when:
1. **Casual reading** - Personal interest, entertainment
2. **Brainstorming** - Creative ideas, general exploration
3. **Quick answers** - When speed matters more than verification
4. **Readability priority** - When citations would be distracting
5. **Already familiar** - When you know the content and trust the system

---

## Migration Guide

### For Existing Users

**Before (citations always enforced):**
```bash
uv run python main.py index ask "question"
# Citations were mandatory, no way to disable
```

**Now (citations toggleable, default ON):**
```bash
# Same behavior - citations enabled by default
uv run python main.py index ask "question"

# NEW: Can disable if needed
uv run python main.py index ask "question" --no-citations
```

**No breaking changes** - Existing scripts continue to work with citations enabled by default.

---

## Help Command

View all options:
```bash
uv run python main.py index ask --help
```

Output includes:
```
--citations         --no-citations             Enforce citation format in
                                               answers
                                               [default: citations]
```

---

## Best Practices

1. **Default to citations** for professional work
2. **Use `--no-citations`** for casual exploration
3. **Always show sources** (`--show-sources`, enabled by default) regardless of citation mode
4. **Combine with reranking** (`--rerank`) for best quality in either mode
5. **Test both modes** when first using the system to find your preference
6. **Document your choice** in scripts/workflows for consistency

---

## Future Enhancements

Potential improvements:
- [ ] Citation style options (inline, footnote, endnote)
- [ ] Partial citation mode (cite only key claims)
- [ ] Citation density control (strict, moderate, minimal)
- [ ] Auto-suggest citation mode based on query type
- [ ] Export citations in standard formats (APA, MLA, Chicago)

---

*Last updated: December 3, 2025*
