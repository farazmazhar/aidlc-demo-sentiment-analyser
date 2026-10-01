# Unit ↔ Story Map — `very-cool-sentiment-analysis` v1

Every story is assigned to a unit; every unit has stories. With one unit, the assignment is total and
the ordering below is a reading order inside that unit, not a schedule.

| Story | Unit ID | Directory |
|---|---|---|
| US1.1 Install, run and test it locally, offline by default | U1 | `u1-application` |
| US1.2 Documentation, names and manifest tell the truth | U1 | `u1-application` |
| US2.1 Submit text and get a labelled result with its alternatives | U1 | `u1-application` |
| US2.2 Empty input is refused and nothing is stored | U1 | `u1-application` |
| US3.1 The answer is read as typed data, never guessed from prose | U1 | `u1-application` |
| US4.1 See previous analyses newest-first, with a defined limit | U1 | `u1-application` |
| US5.1 Choose the live model, with a stated credential precedence | U1 | `u1-application` |
| US5.2 A live attempt without a usable key fails with an instruction | U1 | `u1-application` |
| US5.3 The active engine and connection state are always visible | U1 | `u1-application` |
| US6.1 Connect from the page, keep the credential in memory, drop a rejected one | U1 | `u1-application` |
| US7.1 Stored results keep the v1 contract through an in-place migration | U1 | `u1-application` |
| US8.1 The key never leaks and the app never leaves the machine | U1 | `u1-application` |
| US9.1 The live client is proven by tests and the coverage floor holds | U1 | `u1-application` |

## Coverage verification

- **Stories assigned:** 13 of 13; none unassigned.
- **Units with stories:** 1 of 1; `U1` carries every story.
- **Cross-cutting stories:** none span more than one unit, because there is one unit. US1.2
  (documentation, class names, the stale comment) touches more than one component inside the unit but
  not more than one unit.

## Implementation order inside the unit

A reading order for the work, derived from the dependency-shaped parts of the stories rather than from
an economic judgement (that belongs to Delivery Planning):

1. **US1.1, US8.1** — the app runs offline, binds loopback and keeps the key contained; nothing else
   can be exercised until this holds.
2. **US3.1, US2.1, US2.2** — the engine contract, the labelled result and the invalid-input refusal.
3. **US7.1** — the stored record, the provider column and the in-place migration.
4. **US4.1** — the history view with its defined limit.
5. **US5.1, US5.2, US5.3, US6.1** — engine selection, the live-attempt refusal, engine visibility and
   the connection flow.
6. **US9.1** — the live client under an injected transport and the coverage floor.
7. **US1.2** — documentation, class names and the stale comment, landed with the change they describe.

## Notes on the mapping

- The story ids are preserved exactly as `stories.md` defines them.
- `U1`'s kind is `service`, so every construction design stage applies to it; there is no unit that
  owes a reduced artifact set.
