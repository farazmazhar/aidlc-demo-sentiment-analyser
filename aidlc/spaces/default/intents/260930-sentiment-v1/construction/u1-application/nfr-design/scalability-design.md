# Scalability Design — `u1-application`

## Design solutions

| Requirement | Design solution |
|---|---|
| NFR-SC1 | No scaling element exists: one process, one user, no worker pool and no queue. The design records the absence rather than leaving it to inference. |
| NFR-SC2 | The history read is bounded at the boundary by its limit and reads newest-first, so the page's cost is set by what it asks for rather than by how much history exists. |
| NFR-SC3 | One local store file, opened by the process, with no second process or service resolving it. The store's schema change runs in the same process at start. |

## Growth path, deliberately not built

If the tool ever served more than one user, the order of work would be: a real credential store, a
retention policy, then a proper concurrency story for the store. Writing that path down here is the
design's way of saying the current shape is a choice, not an oversight.
