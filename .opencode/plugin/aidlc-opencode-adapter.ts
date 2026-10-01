// aidlc-opencode-adapter.ts — the opencode hook shim (AUTHORED shell file; the
// aidlc-*.ts hook bodies in <project>/.aidlc/hooks/ are PACKAGED core,
// byte-shared with the Claude Code harness).
//
// opencode has no settings.json/hooks.json hook registry; its extension seam is
// the PLUGIN API. This adapter maps opencode's V2 plugin hooks onto the core
// hook bodies, each run as a bun subprocess fed the ClaudeCodeHookInput JSON
// shape the core hooks parse:
//
//   opencode V2 moment                         → core hook (Claude event it mirrors)
//   --------------------------------------------------------------------------
//   ctx.session.hook("prompt", …)              → aidlc-session-start.ts (first per session)
//                                                aidlc-record-human-turn.ts (every human turn)
//   ctx.tool.hook("execute.before", …)         → aidlc-deliver-stage-rules.ts rewrite +
//                                                plan-approval guard + reviewer-scope +
//                                                review-freeze + state-transition guard (PreToolUse)
//   ctx.tool.hook("execute.after", …)          → aidlc-write-audit-log.ts +
//                                                aidlc-run-sensors.ts (PostToolUse Write|Edit)
//                                                aidlc-rebuild-stage-graph.ts (PostToolUse Bash)
//                                                aidlc-sync-workflow-state.ts (PostToolUse TaskUpdate)
//                                                aidlc-log-subagent.ts (SubagentStop)
//   ctx.session.hook("compaction", …)          → aidlc-validate-state.ts (PreCompact)
//   ctx.event.subscribe() session.idle         → aidlc-continue-workflow.ts (Stop)
//
// Stop enforcement: session.idle is a REACTIVE event, so when the core
// continue-workflow hook answers {"decision":"block","reason":…} this adapter
// re-engages the loop by injecting the reason as a new session prompt. The
// injected prompt carries the NUDGE sentinel so the prompt hook never mints
// HUMAN presence for it.
//
// NOTE (V1→V2 migration): the original shim exported a V1 default function
// returning a hook map. OpenCode V2 rejects that shape ("Plugin must export a
// default definition with an id and an effect or setup function"), so the
// plugin silently never loaded and no hook ever ran. This file default-exports
// a V2 definition object with `id` + `setup(ctx)`.

import { spawn } from "node:child_process";
import { isAbsolute, join } from "node:path";

const NUDGE_SENTINEL = "[aidlc-forwarding-nudge]";
const PROJECTED_INVOKE = "bun .aidlc/tools/aidlc.ts";
const TRUSTED_NAMESPACE = "engine";
const PROJECTED_TRUSTED_NAMESPACE = TRUSTED_NAMESPACE.startsWith("{{")
  ? "engine"
  : TRUSTED_NAMESPACE;
const DEFAULT_AIDLC_COMMAND = PROJECTED_INVOKE.startsWith("{{")
  ? ["bun", ".aidlc/tools/aidlc.ts", PROJECTED_TRUSTED_NAMESPACE]
  : [...PROJECTED_INVOKE.trim().split(/\s+/), PROJECTED_TRUSTED_NAMESPACE];

function runCoreHook(
  hookFile: string,
  input: Record<string, unknown>,
  cwd: string,
  aidlcCommand: readonly string[],
): Promise<{ stdout: string; stderr: string; code: number }> {
  return new Promise((resolve) => {
    const [bin, ...prefix] = aidlcCommand;
    const hook = hookFile.replace(/^aidlc-/, "").replace(/\.ts$/, "");
    if (!bin) return resolve({ stdout: "", stderr: "", code: 0 });
    try {
      const child = spawn(bin, [...prefix, "hook", hook, "--project-dir", cwd], {
        cwd,
        stdio: ["pipe", "pipe", "pipe"],
        env: {
          ...process.env,
          AIDLC_PROJECT_DIR: cwd,
          CLAUDE_PROJECT_DIR: cwd,
        },
      });
      let out = "";
      let err = "";
      child.stdout.on("data", (d: Buffer) => {
        out += d.toString();
      });
      child.stderr.on("data", (d: Buffer) => {
        err += d.toString();
      });
      child.on("error", () => resolve({ stdout: "", stderr: "", code: 0 })); // fail open
      child.on("close", (code: number | null) =>
        resolve({ stdout: out, stderr: err, code: code ?? 0 })
      );
      child.stdin.write(JSON.stringify(input));
      child.stdin.end();
    } catch {
      resolve({ stdout: "", stderr: "", code: 0 }); // fail open
    }
  });
}

export type EngineErrorToast = {
  title?: string;
  message: string;
  variant: "info" | "success" | "warning" | "error";
  duration?: number;
};

const AIDLC_BUN_PREFIX = /^bun[ \t]+\.aidlc\/(?:tools|hooks)\//;
const AIDLC_ENTRYPOINT = /^\.aidlc\/(tools|hooks)\/([A-Za-z0-9][A-Za-z0-9._-]*\.ts)$/;

// emit.ts replaces the empty array with every packaged .aidlc/{tools,hooks}/*.ts
// path. The adapter can then reject a newly-authored payload.ts even though the
// host's coarse bash permission glob matches it.
const shippedAidlcEntrypoints: ReadonlySet<string> = new Set<string>(
  /* @aidlc-shipped-entrypoints@ */ [
    "hooks/aidlc-continue-workflow.ts",
    "hooks/aidlc-deliver-stage-rules.ts",
    "hooks/aidlc-fold-usage.ts",
    "hooks/aidlc-log-subagent.ts",
    "hooks/aidlc-plan-approval-guard.ts",
    "hooks/aidlc-rebuild-stage-graph.ts",
    "hooks/aidlc-record-human-turn.ts",
    "hooks/aidlc-review-freeze.ts",
    "hooks/aidlc-reviewer-scope.ts",
    "hooks/aidlc-run-sensors.ts",
    "hooks/aidlc-session-end.ts",
    "hooks/aidlc-session-start.ts",
    "hooks/aidlc-state-transition-guard.ts",
    "hooks/aidlc-statusline.ts",
    "hooks/aidlc-sync-workflow-state.ts",
    "hooks/aidlc-validate-state.ts",
    "hooks/aidlc-write-audit-log.ts",
    "hooks/review-freeze-command.ts",
    "hooks/runtime-integrity.ts",
    "tools/aidlc-archive.ts",
    "tools/aidlc-artifact-resolution.ts",
    "tools/aidlc-artifact-vocabulary.ts",
    "tools/aidlc-attest.ts",
    "tools/aidlc-audit.ts",
    "tools/aidlc-bolt.ts",
    "tools/aidlc-channel.ts",
    "tools/aidlc-color.ts",
    "tools/aidlc-command.ts",
    "tools/aidlc-completions.ts",
    "tools/aidlc-config-diagnostics.ts",
    "tools/aidlc-construction-checkpoints.ts",
    "tools/aidlc-directive.ts",
    "tools/aidlc-distribution.ts",
    "tools/aidlc-doctor-bundle.ts",
    "tools/aidlc-doctor.ts",
    "tools/aidlc-documentkb-schema.ts",
    "tools/aidlc-graph.ts",
    "tools/aidlc-guard-fences.ts",
    "tools/aidlc-guard-operation.ts",
    "tools/aidlc-guard-switch.ts",
    "tools/aidlc-includes.ts",
    "tools/aidlc-init.ts",
    "tools/aidlc-inline-context.ts",
    "tools/aidlc-install-paths.ts",
    "tools/aidlc-jump.ts",
    "tools/aidlc-knowledge.ts",
    "tools/aidlc-learnings.ts",
    "tools/aidlc-lib.ts",
    "tools/aidlc-lifecycle.ts",
    "tools/aidlc-log.ts",
    "tools/aidlc-machine-config.ts",
    "tools/aidlc-metrics.ts",
    "tools/aidlc-model-policy.ts",
    "tools/aidlc-orchestrate.ts",
    "tools/aidlc-plugin-build.ts",
    "tools/aidlc-plugin-create.ts",
    "tools/aidlc-plugin-emit.ts",
    "tools/aidlc-plugin-test.ts",
    "tools/aidlc-plugin-validate.ts",
    "tools/aidlc-plugin.ts",
    "tools/aidlc-release.ts",
    "tools/aidlc-review-brief.ts",
    "tools/aidlc-rule-schema.ts",
    "tools/aidlc-runner-gen.ts",
    "tools/aidlc-runtime-budget.ts",
    "tools/aidlc-runtime-paths.ts",
    "tools/aidlc-runtime.ts",
    "tools/aidlc-sensor-claim-sources.ts",
    "tools/aidlc-sensor-linter.ts",
    "tools/aidlc-sensor-required-sections.ts",
    "tools/aidlc-sensor-schema.ts",
    "tools/aidlc-sensor-traceability.ts",
    "tools/aidlc-sensor-type-check.ts",
    "tools/aidlc-sensor-upstream-coverage.ts",
    "tools/aidlc-sensor.ts",
    "tools/aidlc-settings.ts",
    "tools/aidlc-stage-schema.ts",
    "tools/aidlc-state.ts",
    "tools/aidlc-steering.ts",
    "tools/aidlc-swarm-checkpoints.ts",
    "tools/aidlc-swarm.ts",
    "tools/aidlc-testing-posture.ts",
    "tools/aidlc-tiers.ts",
    "tools/aidlc-transaction.ts",
    "tools/aidlc-uninstall-plan.ts",
    "tools/aidlc-unit.ts",
    "tools/aidlc-update.ts",
    "tools/aidlc-usage.ts",
    "tools/aidlc-utility.ts",
    "tools/aidlc-validate.ts",
    "tools/aidlc-validity.ts",
    "tools/aidlc-version.ts",
    "tools/aidlc-windows-uninstall.ts",
    "tools/aidlc-workspace-doctor.ts",
    "tools/aidlc-workspace-manifest.ts",
    "tools/aidlc-workspace-sync.ts",
    "tools/aidlc-worktree.ts",
    "tools/aidlc.ts"
  ],
);

const PROJECTED_BUN_TOOLS = DEFAULT_AIDLC_COMMAND[0] === "bun"
  ? (DEFAULT_AIDLC_COMMAND[1] ?? "").replace(/aidlc\.ts$/, "")
  : null;

/** Parse one expansion-free shell command into argv, or reject shell syntax. */
function directShellWords(command: string): string[] | null {
  const words: string[] = [];
  let word = "";
  let wordStarted = false;
  let quote: "'" | '"' | null = null;
  for (let i = 0; i < command.length; i++) {
    const ch = command[i];
    if (quote === "'") {
      if (ch === "'") quote = null;
      else word += ch;
      continue;
    }
    if (quote === '"') {
      if (ch === '"') {
        quote = null;
        continue;
      }
      if (ch === "\\" && i + 1 < command.length) {
        const next = command[++i];
        if (next === "\n" || next === "\r") return null;
        word += next;
        continue;
      }
      if (ch === "`" || ch === "$" || ch === "\n" || ch === "\r") return null;
      word += ch;
      continue;
    }
    if (ch === "'" || ch === '"') {
      quote = ch;
      wordStarted = true;
      continue;
    }
    if (ch === " " || ch === "\t") {
      if (wordStarted) {
        words.push(word);
        word = "";
        wordStarted = false;
      }
      continue;
    }
    if (
      ch === "\n" ||
      ch === "\r" ||
      ch === "\\" ||
      ch === "`" ||
      ch === "$" ||
      ch === "#" ||
      ch === ";" ||
      ch === "|" ||
      ch === "&" ||
      ch === "(" ||
      ch === ")" ||
      ch === "<" ||
      ch === ">"
    ) {
      return null;
    }
    word += ch;
    wordStarted = true;
  }
  if (quote !== null) return null;
  if (wordStarted) words.push(word);
  return words;
}

/** Return a denial reason only when the static AIDLC allow-prefix would match. */
function aidlcBashBoundaryViolation(
  command: string,
  allowedEntrypoints: ReadonlySet<string> = shippedAidlcEntrypoints,
): string | null {
  if (/^aidlc(?:[ \t]|$)/.test(command)) {
    const words = directShellWords(command);
    if (words?.[0] === "aidlc") return null;
    return (
      "AIDLC bash permission allows one direct invocation of a framework tool only. " +
      "Do not use chaining, redirection, expansion, or command substitution."
    );
  }
  if (PROJECTED_BUN_TOOLS === null) {
    return null;
  }
  if (!AIDLC_BUN_PREFIX.test(command)) return null;
  const words = directShellWords(command);
  const target = words?.[1]?.match(AIDLC_ENTRYPOINT);
  if (
    words?.[0] === "bun" &&
    target &&
    allowedEntrypoints.has(`${target[1]}/${target[2]}`)
  ) {
    return null;
  }
  return (
    "AIDLC bash permission allows one direct invocation of a shipped tool or hook only. " +
    "Use an unchanged .aidlc entrypoint without chaining, redirection, expansion, or command substitution."
  );
}

/** Extract every source and destination path touched by an apply_patch call. */
function applyPatchPaths(args: Record<string, unknown>): string[] {
  const patch =
    (args.patchText as string) ??
    (args.patch as string) ??
    (args.command as string) ??
    "";
  const paths: string[] = [];
  for (const match of patch.matchAll(/^\*\*\* (?:Add|Update|Delete) File: (.+)$/gm)) {
    paths.push(match[1].trim());
  }
  for (const match of patch.matchAll(/^\*\*\* Move to: (.+)$/gm)) {
    paths.push(match[1].trim());
  }
  return Array.from(new Set(paths.filter((p) => p.length > 0)));
}

type ReviewerCall = {
  toolName: "Read" | "Edit" | "Write" | "LS" | "Glob" | "Grep" | "Bash";
  toolInput: Record<string, unknown>;
};

function reviewerCalls(tool: string, args: Record<string, unknown>): ReviewerCall[] {
  if (tool === "bash") {
    return [{ toolName: "Bash", toolInput: { command: (args.command as string) ?? "" } }];
  }
  if (tool === "read") {
    return [{
      toolName: "Read",
      toolInput: { file_path: (args.filePath as string) ?? (args.path as string) ?? "" },
    }];
  }
  if (tool === "write") {
    return [{
      toolName: "Write",
      toolInput: { file_path: (args.filePath as string) ?? (args.path as string) ?? "" },
    }];
  }
  if (tool === "edit") {
    return [{
      toolName: "Edit",
      toolInput: { file_path: (args.filePath as string) ?? (args.path as string) ?? "" },
    }];
  }
  if (tool === "glob") {
    return [{
      toolName: "Glob",
      toolInput: {
        pattern: (args.pattern as string) ?? "",
        path: (args.path as string) ?? "",
      },
    }];
  }
  if (tool === "grep") {
    return [{
      toolName: "Grep",
      toolInput: {
        pattern: (args.pattern as string) ?? "",
        path: (args.path as string) ?? "",
        glob: (args.include as string) ?? "",
      },
    }];
  }
  if (tool === "list") {
    return [{
      toolName: "LS",
      toolInput: { path: (args.path as string) ?? "" },
    }];
  }
  if (tool === "apply_patch") {
    return applyPatchPaths(args).map((filePath) => ({
      toolName: "Write",
      toolInput: { file_path: filePath },
    }));
  }
  return [];
}

function sessionStartHandled(stdout: string): boolean {
  try {
    const parsed = JSON.parse(stdout) as { additionalContext?: unknown };
    return typeof parsed.additionalContext === "string";
  } catch {
    return false;
  }
}

type HookInput = "write" | "edit" | "apply_patch" | "bash" | string;

/**
 * V2 definition. The loader requires a default export object with `id` and
 * `setup` (or `effect`); a V1 function export is rejected and the plugin is
 * skipped entirely.
 */
export default {
  id: "aidlc.opencode.adapter",
  async setup(ctx: any) {
    const directory: string = ctx?.location?.directory ?? process.cwd();
    const aidlcCommand = DEFAULT_AIDLC_COMMAND;
    const runCore = (hookFile: string, input: Record<string, unknown>) =>
      runCoreHook(hookFile, input, directory, aidlcCommand);

    // Sessions whose session-start hook reached an active workflow.
    const started = new Set<string>();
    // Main sessions that delivered a real human turn. Stop enforcement keys on
    // this lighter latch because workflow state can be created during turn one.
    const sawHumanTurn = new Set<string>();
    // Sessions confirmed as main (no parentID) — presence + continue-workflow
    // enforcement apply only to these; child (task-tool) sessions are workers.
    const mainSession = new Map<string, boolean>();
    const sessionAgent = new Map<string, string>();
    const idleInFlight = new Set<string>();
    // The Plan Approval guard judges the workflow of a bound session. A child
    // session skips SessionStart and has no binding, so send the main session
    // that owns it.
    const ownerSession = new Map<string, string>();

    async function isMainSession(sessionID: string): Promise<boolean> {
      const cached = mainSession.get(sessionID);
      if (cached !== undefined) return cached;
      try {
        const s = await ctx.session.get({ sessionID });
        const main = !(s?.parentID);
        mainSession.set(sessionID, main);
        return main;
      } catch {
        // An uncertain child must never record-human-turn human presence.
        return false;
      }
    }

    async function owningSession(sessionID: string): Promise<string> {
      const cached = ownerSession.get(sessionID);
      if (cached !== undefined) return cached;
      let current = sessionID;
      try {
        for (let depth = 0; depth < 8; depth++) {
          const s = await ctx.session.get({ sessionID: current });
          const parent = s?.parentID;
          if (!parent) break;
          current = parent;
        }
      } catch {
        return sessionID;
      }
      ownerSession.set(sessionID, current);
      return current;
    }

    async function agentForSession(sessionID: string): Promise<string | undefined> {
      const cached = sessionAgent.get(sessionID);
      if (cached !== undefined) return cached;
      try {
        const s = await ctx.session.get({ sessionID });
        const agent = typeof s?.agent === "string" ? s.agent : undefined;
        if (agent) {
          sessionAgent.set(sessionID, agent);
          return agent;
        }
      } catch {
        /* fall through */
      }
      return undefined;
    }

    async function showEngineErrorToast(stdout: string): Promise<void> {
      let message: string | null = null;
      try {
        const parsed = JSON.parse(stdout) as { systemMessage?: unknown };
        if (typeof parsed.systemMessage === "string" && parsed.systemMessage.length > 0) {
          message = parsed.systemMessage;
        }
      } catch {
        return;
      }
      if (message === null) return;
      const showToast = ctx?.tui?.showToast ?? ctx?.client?.tui?.showToast;
      if (typeof showToast !== "function") return;
      try {
        await showToast.call(ctx?.tui ?? ctx?.client?.tui, {
          body: { title: "AI-DLC", message, variant: "error" },
        });
      } catch {
        /* no TUI attached (headless run) - the toast is best-effort */
      }
    }

    // ── chat.message (first per session → session-start; every turn → human turn)
    if (ctx?.session?.hook) {
      await ctx.session.hook("prompt", async (event: any) => {
        const sessionID: string = event?.sessionID ?? "";
        if (event?.agent) sessionAgent.set(sessionID, event.agent);
        const text: string = event?.prompt?.text ?? "";
        if (typeof text === "string" && text.startsWith(NUDGE_SENTINEL)) return;
        if (!sessionID) return;
        if (!(await isMainSession(sessionID))) return;
        sawHumanTurn.add(sessionID);
        if (!started.has(sessionID)) {
          const result = await runCore("aidlc-session-start.ts", {
            hook_event_name: "SessionStart",
            source: "startup",
            session_id: sessionID,
          });
          // A fresh project has no state yet, so the core hook emits no context.
          // Retry on later human turns until an active workflow is available.
          if (sessionStartHandled(result.stdout)) started.add(sessionID);
        }
        await runCore("aidlc-record-human-turn.ts", {
          hook_event_name: "UserPromptSubmit",
          session_id: sessionID,
          prompt: text,
        });
      });

      // ── experimental.session.compacting → validate-state
      await ctx.session.hook("compaction", async () => {
        await runCore("aidlc-validate-state.ts", { hook_event_name: "PreCompact" });
      });
    }

    // ── tool.execute.before (PreToolUse guard set)
    if (ctx?.tool?.hook) {
      await ctx.tool.hook("execute.before", async (event: any) => {
        const tool: string = event?.tool ?? "";
        const args: Record<string, unknown> = event?.input ?? {};
        const sessionID: string = event?.sessionID ?? "";

        if (tool === "task") {
          const dispatch = await runCore("aidlc-deliver-stage-rules.ts", {
            hook_event_name: "PreToolUse",
            session_id: sessionID,
            tool_name: "task",
            tool_input: args,
            cwd: directory,
          });
          if (dispatch.code === 2) {
            throw new Error(
              dispatch.stderr.trim() ||
                "required active-stage rules could not be loaded for subagent dispatch",
            );
          }
          if (dispatch.stdout.trim()) {
            try {
              const parsed = JSON.parse(dispatch.stdout) as {
                hookSpecificOutput?: { updatedInput?: Record<string, unknown> };
              };
              if (parsed.hookSpecificOutput?.updatedInput) {
                event.input = parsed.hookSpecificOutput.updatedInput;
              }
            } catch {
              throw new Error(
                "AIDLC deliver-stage-rules hook returned invalid rewrite output",
              );
            }
          }
        }

        const namedAgent =
          sessionAgent.get(sessionID) ?? (await agentForSession(sessionID));
        const delegatedAgent =
          namedAgent?.startsWith("aidlc-") && namedAgent.endsWith("-agent")
            ? namedAgent
            : null;

        if (tool === "bash") {
          const command = (args.command as string) ?? "";
          const violation = aidlcBashBoundaryViolation(command, shippedAidlcEntrypoints);
          if (violation) throw new Error(violation);
          const guard = await runCore("aidlc-state-transition-guard.ts", {
            hook_event_name: "PreToolUse",
            tool_name: "Bash",
            tool_input: { command },
            cwd: directory,
            ...(delegatedAgent ? { agent_type: delegatedAgent } : {}),
          });
          if (guard.code === 2) {
            throw new Error(
              guard.stderr.trim() ||
                "stage status is changed by the workflow tools, not by hand: use aidlc-orchestrate.ts report instead of calling aidlc-state.ts directly",
            );
          }
        }

        // Review-freeze (§12a terminal-receipt write-freeze): runs for EVERY
        // agent - unlike reviewer-scope there is no identity gate, because any
        // produces[] write voids a fresh READY receipt regardless of who makes
        // it. The core hook self-filters to write tools and fails open.
        if (
          tool === "bash" ||
          tool === "write" ||
          tool === "edit" ||
          tool === "apply_patch"
        ) {
          const freezeCalls =
            tool === "bash"
              ? [{ toolName: "Bash", toolInput: { command: (args.command as string) ?? "" } }]
              : (tool === "apply_patch" ? applyPatchPaths(args) : [
                  (args.filePath as string) ?? (args.path as string) ?? "",
                ])
                  .filter((filePath) => filePath.length > 0)
                  .map((filePath) => ({
                    toolName: tool === "edit" ? "Edit" : "Write",
                    toolInput: { file_path: filePath },
                  }));
          for (const call of freezeCalls) {
            const freeze = await runCore("aidlc-review-freeze.ts", {
              hook_event_name: "PreToolUse",
              tool_name: call.toolName,
              tool_input: call.toolInput,
              cwd: directory,
            });
            if (freeze.code === 2) {
              throw new Error(
                freeze.stderr.trim() ||
                  "review-freeze: this write would invalidate a fresh READY review receipt",
              );
            }
          }
        }

        // Plan-approval guard: workspace mutations share the same normalized
        // calls as review-freeze, while task dispatches carry the explicit
        // approval target and Testing Contract markers.
        if (
          tool === "bash" ||
          tool === "write" ||
          tool === "edit" ||
          tool === "apply_patch"
        ) {
          const owner = await owningSession(sessionID);
          const planCalls =
            tool === "bash"
              ? [{ toolName: "Bash", toolInput: { command: (args.command as string) ?? "" } }]
              : (tool === "apply_patch" ? applyPatchPaths(args) : [
                  (args.filePath as string) ?? (args.path as string) ?? "",
                ])
                  .filter((filePath) => filePath.length > 0)
                  .map((filePath) => ({
                    toolName: tool === "edit" ? "Edit" : "Write",
                    toolInput: { file_path: filePath },
                  }));
          for (const call of planCalls) {
            const guard = await runCore("aidlc-plan-approval-guard.ts", {
              hook_event_name: "PreToolUse",
              tool_name: call.toolName,
              tool_input: call.toolInput,
              session_id: owner,
              cwd: directory,
            });
            if (guard.code === 2) {
              throw new Error(
                guard.stderr.trim() ||
                  "code-generation requires an approved plan before workspace mutation",
              );
            }
          }
        }

        if (tool === "task") {
          const target =
            (args.subagent_type as string) ?? (args.agent as string) ?? "";
          if (target === "aidlc-developer-agent") {
            const owner = await owningSession(sessionID);
            const guard = await runCore("aidlc-plan-approval-guard.ts", {
              hook_event_name: "PreToolUse",
              tool_name: "Task",
              tool_input: {
                subagent_type: target,
                prompt: [(args.prompt as string) ?? "", (args.description as string) ?? ""]
                  .filter((t) => t.length > 0)
                  .join("\n"),
              },
              session_id: owner,
              cwd: directory,
            });
            if (guard.code === 2) {
              throw new Error(
                guard.stderr.trim() ||
                  "code-generation requires an approved plan before dispatching the developer agent",
              );
            }
          }
        }

        const calls = reviewerCalls(tool, args);
        if (calls.length === 0) return;

        const agent = namedAgent;
        const identity =
          agent
            ? { agent_type: agent }
            : (await isMainSession(sessionID))
              ? null
              : { scoped_registration: true };
        if (identity === null) return;

        for (const call of calls) {
          const result = await runCore("aidlc-reviewer-scope.ts", {
            hook_event_name: "PreToolUse",
            tool_name: call.toolName,
            tool_input: call.toolInput,
            cwd: directory,
            ...identity,
          });
          if (result.code === 2) {
            throw new Error(result.stderr.trim() || "reviewer read-scope refused this tool call");
          }
        }
      });

      // ── tool.execute.after (PostToolUse bookkeeping)
      await ctx.tool.hook("execute.after", async (event: any) => {
        const tool: string = event?.tool ?? "";
        const args: Record<string, unknown> = event?.input ?? {};
        const sessionID: string = event?.sessionID ?? "";
        const callID: string = event?.callID ?? "";
        const result = event?.result ?? event?.output;

        if (tool === "write" || tool === "edit" || tool === "apply_patch") {
          const paths =
            tool === "apply_patch"
              ? applyPatchPaths(args)
              : [((args.filePath as string) ?? (args.path as string) ?? "")];
          for (const filePath of paths) {
            if (!filePath) continue;
            const absolutePath = isAbsolute(filePath) ? filePath : join(directory, filePath);
            const payload = {
              hook_event_name: "PostToolUse",
              tool_name: "Write",
              tool_input: { file_path: absolutePath },
            };
            // audit THEN sensors, mirroring the Claude settings.json order.
            await runCore("aidlc-write-audit-log.ts", payload);
            await runCore("aidlc-run-sensors.ts", payload);
          }
          return;
        }
        if (tool === "bash") {
          const toolResponse =
            typeof result === "string"
              ? result
              : ((result as any)?.output ?? "");
          const payload = {
            hook_event_name: "PostToolUse",
            tool_name: "Bash",
            tool_input: { command: (args.command as string) ?? "" },
            session_id: sessionID,
            tool_response: toolResponse,
          };
          const out = await runCore("aidlc-rebuild-stage-graph.ts", payload);
          await showEngineErrorToast(out.stdout);
          return;
        }
        if (tool === "todowrite") {
          // The core hook keys on Claude's TaskUpdate in_progress transition;
          // map the first in-progress todo's content onto activeForm.
          const todos = (args.todos as Array<{ content?: string; status?: string }>) ?? [];
          const active = todos.find((t) => t.status === "in_progress");
          if (!active?.content) return;
          await runCore("aidlc-sync-workflow-state.ts", {
            hook_event_name: "PostToolUse",
            tool_name: "TaskUpdate",
            tool_input: { status: "in_progress", activeForm: active.content },
          });
          return;
        }
        if (tool === "task") {
          await runCore("aidlc-log-subagent.ts", {
            hook_event_name: "SubagentStop",
            session_id: sessionID,
            agent_type:
              (args.subagent_type as string) ?? (args.agent as string) ?? "unknown",
            agent_id: callID,
          });
        }
      });
    }

    // ── session.idle → continue-workflow nudge
    if (ctx?.event?.subscribe) {
      const controller = new AbortController();
      void (async () => {
        try {
          for await (const raw of ctx.event.subscribe({ signal: controller.signal })) {
            const event: any = raw;
            if (event?.type !== "session.idle") continue;
            const sessionID: string =
              event?.properties?.sessionID ?? event?.sessionID ?? "";
            // A workflow can be created during the first turn, after session-start
            // saw no state. Let the core Stop hook's own state-file guard decide.
            if (!sessionID || !sawHumanTurn.has(sessionID)) continue;
            if (!(await isMainSession(sessionID))) continue;
            if (idleInFlight.has(sessionID)) continue;
            idleInFlight.add(sessionID);
            let nudgeReason: string | null = null;
            try {
              const res = await runCore("aidlc-continue-workflow.ts", {
                hook_event_name: "Stop",
                stop_hook_active: false,
                session_id: sessionID,
              });
              try {
                const parsed = JSON.parse(res.stdout) as {
                  decision?: string;
                  reason?: string;
                };
                if (parsed.decision === "block" && parsed.reason) {
                  nudgeReason = parsed.reason;
                }
              } catch {
                /* no/unparseable output → allow the continue-workflow (advisory) */
              }
            } finally {
              idleInFlight.delete(sessionID);
            }
            if (nudgeReason) {
              try {
                await ctx.session.prompt({
                  sessionID,
                  text: `${NUDGE_SENTINEL} ${nudgeReason}`,
                });
              } catch {
                /* best-effort re-engagement */
              }
            }
          }
        } catch {
          /* subscription ended / aborted */
        }
      })();
      return () => controller.abort();
    }

    return undefined;
  },
};
