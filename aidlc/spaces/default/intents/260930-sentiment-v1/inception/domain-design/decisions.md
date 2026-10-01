# Architecture Decision Records — Domain Design

Durable log of the significant design choices made in this stage. Each ADR follows the Inception
phase's required structure: Context, Decision, Consequences, Alternatives Rejected.

---

## ADR-001: Five components rather than module-per-component or a finer split

**Context.** The application exists as twelve Python modules in one package. The stage must name the
logical building blocks the v1 code is organised into, and the requirements add work (an in-place
migration, a provider column, a typed engine contract, page states) that does not respect today's
file boundaries. The project is small — one page, one API, one local user — and caps its runtime
dependencies at two.

**Decision.** Five components: Configuration, Persistence, SentimentEngines, AnalysisService and
WebSurface.

**Consequences.** Boundaries follow lifecycle and change rate rather than files: the migration and
storage contract change together, the engine implementations are the swappable part, the service owns
sequencing, and the HTTP/page layer owns everything a person touches. The cost is that some components
span several existing modules, so a change inside one component may touch more than one file.

**Alternatives Rejected.**
- *One component per existing module* (eight or nine): preserves the current file map exactly, but
  produces components with no independent lifecycle (for example `models` and `repository` change
  together) and pushes the boundary decision into Construction.
- *A finer cut separating contracts/entities from behaviour*: gives a records component its own
  owner, but in a system this small the record shape and its storage never diverge, and the extra
  component adds an interface without an independent reason to change.

---

## ADR-002: Persistence owns the analysis record

**Context.** The stored record (text, label, per-label probabilities, confidence, model, provider,
timestamp) is referenced by the API response, the history view and the engine contract. Every entity
needs exactly one owner, and the migration that adds a column touches the same shape.

**Decision.** Persistence owns `AnalysisRecord`.

**Consequences.** The record's shape and its storage evolve in one place, and the migration has a
single owning component. Other components pass records in and out but do not define their shape beyond
what they consume, so a schema change is a Persistence change plus its callers.

**Alternatives Rejected.**
- *A records/contracts component owning the shape while persistence stores it*: separates the wire
  shape from the stored shape, which is worth doing when the two diverge; here they are identical and
  the split would add a pass-through component.
- *The analysis service owning the record*: makes persistence a dumb store, but then the service owns a
  shape defined by the database schema and the migration loses its owner.

---

## ADR-003: In-process event handoff between the analysis service and the engines

**Context.** The human chose an event-style handoff rather than a direct synchronous call. The
affirmed constraints rule out any external broker: the app is localhost-only, ships no cloud
component and keeps runtime dependencies at two packages.

**Decision.** The AnalysisService publishes an analysis request and receives the engine's typed result
through an in-process handoff — a dispatcher inside the process, not a queue server. The interaction is
recorded as `style: event` in the component catalogue.

**Consequences.** The service no longer holds a direct reference to the engine implementation, which
keeps the engine set swappable and makes the dispatch point the single place where mode resolution
takes effect. The cost is indirection: a call that used to be a function invocation becomes a
publish-and-receive, and failures must be carried back as results rather than raised through the call
stack — which the contract already requires, since a failure must never become a guessed label.

**Alternatives Rejected.**
- *Direct synchronous calls through the interface* (the current code): simplest and fewest moving
  parts, but rejects the human's decision and keeps the engine choice inside the service.
- *A registry the service resolves the engine from, still synchronous*: removes the direct reference
  without the indirection, but still couples the service to the resolution mechanism at call time.
- *An external broker or queue server*: excluded by the localhost-only, dependency-light constraints.

---

## ADR-004: One web-surface component

**Context.** Routes, the page, the health endpoint and the in-app sign-in flow currently live in one
module plus the static assets, and the refined mockups add page states (loading, empty, success,
invalid input, live-mode failure) plus the connection indicator's states.

**Decision.** Keep them as one component, WebSurface.

**Consequences.** The page and the API it calls change together, which matches how this interface
evolves: a state added to the page usually needs the route that feeds it. The component is the largest
in the system, so its internal structure (routes, page state, session handling) has to stay legible
without becoming components.

**Alternatives Rejected.**
- *Split the JSON API from the page/static surface*: reasonable once a second client exists; today the
  page is the only consumer and the split would duplicate the envelope and validation rules.
- *Split routes, page-state handling and the connection indicator apart*: three components in a
  one-page app, each with no independent lifecycle or deployment.

---

## ADR-005: Brownfield treatment — keep today's module boundaries and layout

**Context.** The intent is to harden an existing app into a clean v1 rather than rewrite it, and the
five components cut across the existing twelve modules.

**Decision.** Keep the current package layout and module boundaries; the v1 work renames and converges
in place, and no module is moved into a sub-package to mirror a component.

**Consequences.** The diff stays reviewable and the existing test suite keeps importing what it
imports, which matters under the acceptance-tests-first posture. The cost is that the component map is
not mirrored by the directory tree, so the catalogue in `components.md` is the only place the mapping
is written down.

**Alternatives Rejected.**
- *Regroup modules into sub-packages mirroring the components*: makes the map physical, but rewrites
  every import and every test for no behavioural gain in a package this size.
- *Restructure where the current layout obscures a boundary*: no such place was found — each existing
  module sits inside exactly one component.
