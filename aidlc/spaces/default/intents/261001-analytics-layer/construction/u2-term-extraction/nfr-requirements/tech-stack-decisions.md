# Tech Stack Decisions — `u2-term-extraction`

> **Intent:** `261001-analytics-layer` · stage `nfr-requirements` (construction) ·
> unit `u2-term-extraction` (kind `library`).
>
> **Upstream inputs.** This unit's `functional-spec.md` (the module surface), `rules.md`
> (`BR4.1`–`BR4.5`, the constant-ownership rules that keep the stack at stdlib only),
> and `contract-summary.md` (the pinned boundaries whose additive-only rule this unit
> honours by adding no dependency). The Inception `technology-stack` record is the
> baseline this file measures itself against: it fixes the interpreter and the two
> declared runtime packages, and this unit's whole stack claim is that it needs neither
> more nor fewer.
>
> **This unit adds nothing to the stack.** It is a pure-stdlib leaf in an application
> whose runtime dependency cap is **exactly two** (`fastapi`, `uvicorn`, `C2`/`C-6`).
> The decisions below are therefore about *what is deliberately not chosen*, and each
> one names the rule that rules it out.

## The three imports this module is allowed

| Import | Used for | Why it is the right choice |
|---|---|---|
| `re` | the one word-splitting pattern, compiled once at module scope | Stdlib. The pattern is a constant, not a per-call compilation; `re` is the smallest tool that expresses "maximal runs of `[a-z']`". |
| `collections.abc.Sequence` | the annotation on `significant_terms` | Stdlib typing support only. It documents that the operation filters a sequence and never tokenises (`BR1.2`). |
| `__future__.annotations` | PEP 563 postponed evaluation | The codebase convention, pinned by `AC8.6.1`. |

Nothing else. The module's complete import list is three lines, and
`NFR1.3`'s isolation test is what keeps it that way: an import of anything from `app`
fails the fan-out-0 assertion.

## What is deliberately NOT chosen, and why

| Not chosen | Why not | Rule |
|---|---|---|
| **NLTK, spaCy, scikit-learn** | Each is a large dependency, several ship corpora, and they replace a rule the project has deliberately kept simple and ownable. The stopword set is 100-odd words in a module constant; a corpus download would also create the module's only egress path. | `C2`/`C-6` dependency cap; `NFR1.6`; `AC4.1.4` |
| **A downloaded stopword corpus** | Would break the offline guarantee outright and add a network dependency to a leaf whose entire value is having none. | `NFR1.2`, `FR4.4`, `AC4.1.4` |
| **Stemming or lemmatisation** | Changes what a "term" is, and the ranking it feeds is meant to report the words the text actually contains. Out of scope for this unit. | `FR4.1`–`FR4.3` scope |
| **A regex alternative library** (`regex`, `re2`) | `re` handles `[a-z']+` exactly. Adding a package to compile one simple pattern is unjustifiable under the cap. | `C-6` |
| **Precompiled token caching** (an LRU or a memo table) | Would add mutable module state to a unit specified as pure, and the call sites tokenise rows already in memory. A cache would be an optimisation with no measured problem behind it. | `BR6.2`, `BR6.3` |
| **Unicode-aware tokenisation** (`\w` with `UNICODE`, or `unicodedata`) | Would widen the token class beyond `[a-z']`, which changes what the offline engine scores and breaks `BR5.1`'s parity guarantee. Non-Latin text contributing nothing is a **recorded accepted limitation** (`AC4.1.3`), not an oversight. | `BR2.1`, `BR5.1`, `AC4.1.3` |
| **A `utils.py` or `helpers.py` for shared string work** | The convention is that a helper lives with the concept it serves; neither file may exist. | `AC8.6.3` |
| **A `pydantic` model for the constants or the surface** | `app/` is stdlib-dataclasses-only; and this module declares no shape at all. | `AC8.6.2` |
| **Configuration for the threshold or the stopword set** | The module consumes no configuration value, so it adds none. Both are constants, deliberately: a configurable stopword set would make the terms output environment-dependent. | `AC8.6.4`, `BR4.2`, `BR4.3` |
| **Any logging** | A logging call is an I/O path. The module reports nothing and raises nothing; its callers log if they need to. | `BR6.2`, `BR6.3` |

## The two constraints this unit must satisfy, restated

1. **Exactly two declared runtime dependencies**, unchanged (`C2`/`C-6`). This unit
   adds none — it uses `re` and a typing import from the standard library.
2. **No new external service** (`C-5`). This unit calls nothing at all.

## Versions

No version pinning arises. The module consumes no third-party library, and the two stdlib
modules it uses (`re`, `collections.abc`) are part of the interpreter the project already
declares (`requires-python = ">=3.11"`).
