# Logical Components — `u1-application`

The design-level pieces inside the unit: what each one is responsible for and which requirements it
carries. These are not units and not deployment elements — they are the seams the code will be
organised around, and they map onto the domain components already catalogued.

| Logical component | Responsibility | Carries | Maps to domain component |
|---|---|---|---|
| Settings resolver | Resolve the active mode, model and credential source; produce redacted representations | NFR1.1, NFR2.1, NFR2.2, NFR6.2 | Configuration |
| Store access | Open the store, create it on first run, apply the in-place schema change, write and read records | NFR-R2, NFR-SC2, NFR-SC3, NFR-P1 | Persistence |
| Engine interface | One contract, two implementations; typed result only | NFR1.1 | SentimentEngines |
| Engine dispatcher | Publish a request, receive a typed result, carry failures back as results rather than exceptions | NFR-P2, NFR-R3, NFR1.1 | SentimentEngines / AnalysisService (the in-process handoff) |
| Live transport | The one outbound call, carrying the timeout and injectable so tests need no network | NFR-P2, NFR1.2, NFR6.3 | SentimentEngines |
| Boundary validation | Validate text and the limit, refusing before any store work | NFR-R1, NFR-S1 | AnalysisService / WebSurface |
| Error builder | One envelope for every app-raised failure | NFR-S1 | WebSurface |
| Session credential holder | Hold a session credential in memory, discard a rejected one, expose only its state | NFR2.1, NFR-R3 | WebSurface |
| Connection state | Produce the single payload the health endpoint and the page both read | NFR6.1 | WebSurface |
| Page state | Render the reachable states from that payload and the last result | NFR6.1, NFR6.2 | WebSurface |

## Notes

- The in-process handoff from Domain Design (ADR-003) appears here as the engine dispatcher: a
  publishing seam between the analysis sequence and the engine implementations, inside one unit.
- Two components carry the loopback bind and the absence of a pipeline: the server's start path
  (NFR5.1) and the checkpoint check (NFR4.1, NFR4.2). Neither needs its own component.
- Every logical component sits inside the single unit; none is separately deployable.
