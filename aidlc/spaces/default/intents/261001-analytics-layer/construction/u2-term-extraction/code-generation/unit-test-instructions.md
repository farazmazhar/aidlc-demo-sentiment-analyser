# Unit Test Instructions — `u2-term-extraction`

## Framework and configuration

`pytest` only, configured in `pyproject.toml` under `[tool.pytest.ini_options]`:
`testpaths = ["tests"]`, `addopts = "-q --cov=app --cov-report=term-missing
--cov-fail-under=80"`, `filterwarnings = ["error"]`. This unit adds no tooling.

## How to run this unit's tests

Scoped to this unit, so Build and Test does not rerun the whole suite per unit:

```bash
env -u APPIMAGE python -m pytest -q tests/test_terms.py --cov-fail-under=0
```

> **`--cov-fail-under=0` and why it is here.** `addopts` applies the
> **whole-application** 80 % floor to *every* run, so a single-file subset scores
> far below it and exits 1 — not because a test failed, but because one module
> cannot cover the whole app. The flag disables the floor **for the scoped run
> only**.
>
> **The residual, stated plainly:** the command above has **no coverage gate of its
> own** and exits 0 regardless of coverage. Read the number; do not rely on the
> exit code. The floor is enforced on the whole-suite run, where
> `--cov-fail-under=80` and `[tool.coverage.report] fail_under = 80` both still
> apply.

`env -u APPIMAGE` is required on hosts that export `APPIMAGE`: CPython then reports
the AppImage as `sys.executable` and a subprocess spawn fails with exit 130. It is
a no-op where the variable is unset.

## Expected coverage

The whole-application line floor is 80 %, enforced twice. `app/terms.py` is a small
pure module and is expected at **100 %** — both operations and all three constants
are exercised directly by `tests/test_terms.py`.

## What the ten tests assert

| Test | Criterion |
|---|---|
| `test_tokenize_returns_the_hand_read_tokens_for_every_case` | `AC4.1.3` — the boundary rule, by hand-read cases |
| `test_tokenize_applies_neither_a_length_nor_a_stopword_filter` | `AC4.2.3` — the split is real: `tokenize` filters nothing |
| `test_significant_terms_drops_short_tokens_and_stopwords_and_keeps_the_order` | `AC4.1.1`, `AC4.1.2` |
| `test_significant_terms_never_retokenises_and_keeps_repeats` | `BR1.2`, `BR3.4` |
| `test_significant_terms_leaves_an_all_stopword_sequence_empty` | `AC4.1.5` |
| `test_the_stopword_set_contains_no_sentiment_word` | `AC4.1.4`, `BR4.4` |
| `test_the_private_pattern_is_gone_and_only_one_tokeniser_exists` | `AC4.2.1` |
| `test_the_offline_engine_scoring_is_unchanged_by_the_promotion` | `AC4.2.2` |
| `test_the_promoted_tokeniser_reproduces_the_pattern_it_replaced` | `AC4.2.2` — exhaustive over 1,110 inputs |
| `test_the_offline_engine_never_calls_the_significance_filter` | `AC4.2.3`, `BR5.2` |

**The tenth test is load-bearing and the eighth is not sufficient alone.** The parity
test over a corpus cannot distinguish "the filter was applied to scoring" from "it was
not", because no keyword is a stopword and the shortest keyword is exactly
`MIN_TERM_LENGTH` — both runs produce identical labels. The tenth test asserts the
*operation boundary* instead, which is what makes `BR5.2` decidable.

## Mocking and stubbing

None. The unit's whole surface is two pure functions; the tests call them directly.
The offline engine's purity is asserted by reading its source for the operations it
does **not** call, which is an instrument, not a mock.

## Test data management

No fixtures, no database, no filesystem. Inputs are literal strings and literal token
sequences. The suite's session-wide offline guard remains armed; this unit needs no
network and must never acquire one (`NFR2.1`).

## Ordering

Acceptance-level tests were written against the criteria **before** the module was
implemented (under U1, when the module was built here by mistake); the parity and
instrument tests were written **after**. That matches the team's `custom` posture.
