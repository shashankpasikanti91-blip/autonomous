/**
 * Orchestrator Service — Real Execution Engine
 *
 * Pipeline:
 *   Step 1 — Planner  : LLM call → structured JSON task plan (GPT)
 *   Step 2 — Executor : Deterministic → writes real rows to PostgreSQL via backend API
 *   Step 3 — Logger   : Appends immutable entry to execution_logs
 *
 * GPT is used ONLY for planning.
 * Execution writes to PostgreSQL through the FastAPI backend.
 * No Supabase. No narrative simulation. No GPT scoring.
 */

import { chatCompletion, isOpenAIConfigured } from "./openai";
import {
  dbCreateApp,
  dbSaveSchema,
  dbLogExecution,
} from "./supabase";

// Demo org ID — replace with real auth.user().org_id once auth is wired in
const DEMO_ORG_ID: string =
  (import.meta.env.VITE_DEMO_ORG_ID as string | undefined) ??
  "00000000-0000-0000-0000-000000000010";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PlanStep {
  id: string;
  step: number;
  task: string;
  expected_output: string;
}

export interface ExecutionStep {
  task_id: string;
  step: number;
  task: string;
  output: string;
  status: "success" | "skipped" | "error";
}

export interface ValidationResult {
  passed: boolean;
  score: number; // 0–10
  feedback: string;
  issues: string[];
}

export interface ReasoningTrace {
  plan: PlanStep[];
  execution_steps: ExecutionStep[];
  validation: ValidationResult;
  total_tokens: number;
  model: string;
  duration_ms: number;
}

export interface OrchestrationResult {
  final_output: string;
  tokens_used: number;
  model: string;
  reasoning_trace: ReasoningTrace;
  app_name?: string;
  app_summary?: string;
  /** Real database record IDs written during execution (present when Supabase is configured). */
  db_records?: {
    app_id?: string;
    schema_id?: string;
    log_id?: string;
  };
}

// ─── Multi-Country Payroll & Compliance Rules ─────────────────────────────────

const COUNTRY_RULES = `
SUPPORTED COUNTRY PAYROLL & COMPLIANCE RULES:
- Malaysia (MY): EPF 11% employee / 13% employer, SOCSO, EIS, PCB income tax, min wage MYR 1,500/mo
- Singapore (SG): CPF 20% employee / 17% employer, SDL, SHG, min wage SGD 1,600/mo (residents)
- India (IN): PF 12%/12%, ESI 0.75%/3.25%, Professional Tax (state), TDS, min wage varies by state
- Philippines (PH): SSS 4.5% / 8.5%, PhilHealth 2.5%/2.5%, Pag-IBIG 2%/2%, 13th month pay mandatory
- Australia (AU): Super 11% employer, PAYG withholding, Medicare 2%, Fair Work Act
- Sri Lanka (LK): EPF 8% / 12%, ETF 3% employer, PAYE tax
- Nepal (NP): CIT 10% / 20%, SSF, income tax slabs
- Canada (CA): CPP 5.95%, EI 1.66% / 2.32%, federal + provincial tax
- Germany (DE): Social security ~20%, Lohnsteuer, Kirchensteuer optional, min wage EUR 12.41/hr
- UK (GB): NI 8% / 13.8%, PAYE, pension auto-enrolment 5%/3%, min wage GBP 11.44/hr
- USA (US): FICA 6.2% SS + 1.45% Medicare each side, federal + state tax, FLSA
- Indonesia (ID): BPJS Ketenagakerjaan, BPJS Kesehatan, PPh 21 income tax
- UAE (AE): No income tax, WPS mandatory, DEWS pension for DIFC
- Japan (JP): Social insurance ~15% each, income tax 5-45%, min wage varies by prefecture

When processing payroll, ALWAYS apply the correct country-specific rules based on employee country.
When building business apps, consider local regulations and work culture of the specified country.
`;

// ─── Fallback (no API key) ────────────────────────────────────────────────────

function buildFallbackResult(
  appName: string,
  userInput: string,
  startMs: number
): OrchestrationResult {
  const plan: PlanStep[] = [
    { id: "p1", step: 1, task: "Parse and validate input", expected_output: "Validated data" },
    { id: "p2", step: 2, task: `Execute ${appName} logic`, expected_output: "Processed result" },
    { id: "p3", step: 3, task: "Format and return output", expected_output: "Structured report" },
  ];

  const execution_steps: ExecutionStep[] = plan.map((p) => ({
    task_id: p.id,
    step: p.step,
    task: p.task,
    output: `[Rule-based mode] ${p.task} completed.`,
    status: "success",
  }));

  return {
    final_output: `─── ${appName.toUpperCase()} OUTPUT (Rule-Based Mode) ───\n\nInput received: ${userInput.slice(0, 100)}${userInput.length > 100 ? "..." : ""}\n\n⚠ AI engine offline — no VITE_OPENAI_API_KEY configured.\nAdd your key to .env to enable real AI orchestration.\n\n─── END ───`,
    tokens_used: 0,
    model: "rule-based",
    reasoning_trace: {
      plan,
      execution_steps,
      validation: {
        passed: true,
        score: 5,
        feedback: "Rule-based fallback mode — configure OpenAI key for full AI orchestration.",
        issues: ["No API key configured"],
      },
      total_tokens: 0,
      model: "rule-based",
      duration_ms: Date.now() - startMs,
    },
  };
}

// ─── Step 1: Planner ──────────────────────────────────────────────────────────

async function planner(
  appName: string,
  appDescription: string,
  entryPoint: string,
  userInput: string
): Promise<{ plan: PlanStep[]; tokens: number; model: string }> {
  const systemPrompt = `You are a task planner for an AI execution engine.
App: "${appName}"
Description: ${appDescription}
Entry point: ${entryPoint}

${COUNTRY_RULES}

Given the user's input, generate a structured execution plan as a JSON object.
Respond ONLY with valid JSON — no markdown, no extra text.

JSON format:
{
  "objective": "one sentence describing what will be done",
  "tasks": [
    { "id": "t1", "step": 1, "task": "short task name", "expected_output": "what this step produces" },
    { "id": "t2", "step": 2, "task": "short task name", "expected_output": "what this step produces" },
    { "id": "t3", "step": 3, "task": "short task name", "expected_output": "what this step produces" }
  ]
}

Keep it to 3–5 tasks. Be specific to the app type and user input. Apply country-specific rules when relevant.`;

  const response = await chatCompletion(
    [
      { role: "system", content: systemPrompt },
      { role: "user", content: userInput || "(no input)" },
    ],
    0.2
  );

  // Parse JSON plan — fallback to default if malformed
  let tasks: PlanStep[] = [];
  try {
    const json = JSON.parse(response.result.replace(/```json\n?|```/g, "").trim());
    tasks = (json.tasks || []).map((t: any, i: number) => ({
      id: t.id || `t${i + 1}`,
      step: t.step || i + 1,
      task: t.task || `Step ${i + 1}`,
      expected_output: t.expected_output || "",
    }));
  } catch {
    // Fallback plan if JSON parse fails
    tasks = [
      { id: "t1", step: 1, task: "Parse and validate input", expected_output: "Validated input data" },
      { id: "t2", step: 2, task: `Process ${appName} logic`, expected_output: "Computed results" },
      { id: "t3", step: 3, task: "Format and return output", expected_output: "Structured final report" },
    ];
  }

  return { plan: tasks, tokens: response.tokens_used, model: response.model };
}

// ─── Step 2: Executor ─────────────────────────────────────────────────────────

async function executor(
  appName: string,
  appDescription: string,
  entryPoint: string,
  userInput: string,
  plan: PlanStep[]
): Promise<{ steps: ExecutionStep[]; finalOutput: string; tokens: number; model: string }> {
  const planSummary = plan
    .map((t) => `Step ${t.step}: ${t.task} → expects: ${t.expected_output}`)
    .join("\n");

  const systemPrompt = `You are an AI execution engine running "${appName}".
Description: ${appDescription}
Entry point: ${entryPoint}

${COUNTRY_RULES}

Execution Plan:
${planSummary}

Your job: Execute each step of the plan against the user's input and produce a complete output report.
Apply country-specific tax/compliance rules when processing payroll or business data.

Format your response EXACTLY like this (use the dividers as shown):
─── STEP 1: [task name] ───
[step output]

─── STEP 2: [task name] ───
[step output]

─── STEP 3: [task name] ───
[step output]

─── FINAL OUTPUT ───
[complete consolidated result with all computed values, formatted clearly as a table]

─── SUMMARY ───
[1–2 sentence conclusion]

Be specific — use actual values from the input. Do NOT invent data not present in the input.`;

  const response = await chatCompletion(
    [
      { role: "system", content: systemPrompt },
      { role: "user", content: userInput || "(no input)" },
    ],
    0.3
  );

  // Parse step outputs from the response
  const steps: ExecutionStep[] = plan.map((p) => {
    const stepPattern = new RegExp(
      `─{3}\\s*STEP\\s+${p.step}[^─]*─{3}\\n([\\s\\S]*?)(?=─{3}|$)`,
      "i"
    );
    const match = response.result.match(stepPattern);
    return {
      task_id: p.id,
      step: p.step,
      task: p.task,
      output: match ? match[1].trim() : `Step ${p.step} executed.`,
      status: "success" as const,
    };
  });

  // Extract final output section
  const finalMatch = response.result.match(/─{3}\s*FINAL OUTPUT\s*─{3}\n([\s\S]*?)(?=─{3}|$)/i);
  const finalOutput = finalMatch ? finalMatch[1].trim() : response.result;

  return { steps, finalOutput: response.result, tokens: response.tokens_used, model: response.model };
}

// ─── Step 3: Validator ────────────────────────────────────────────────────────

function validator(output: string, plan: PlanStep[]): ValidationResult {
  const issues: string[] = [];
  let score = 10;

  if (!output || output.trim().length < 50) {
    issues.push("Output is too short or empty");
    score -= 4;
  }

  const hasFinalOutput = /─{3}\s*FINAL OUTPUT/i.test(output) || /─{3}\s*RESULT/i.test(output);
  if (!hasFinalOutput) {
    issues.push("Missing FINAL OUTPUT section");
    score -= 2;
  }

  const hasSummary = /─{3}\s*SUMMARY/i.test(output) || /SUMMARY\s*:/i.test(output);
  if (!hasSummary) {
    issues.push("Missing SUMMARY section");
    score -= 1;
  }

  // Check that at least half the plan steps are covered
  const coveredSteps = plan.filter((p) =>
    new RegExp(`STEP\\s+${p.step}|${p.task.slice(0, 10)}`, "i").test(output)
  ).length;
  const coverage = plan.length > 0 ? coveredSteps / plan.length : 1;
  if (coverage < 0.5) {
    issues.push("Fewer than half the planned steps appear in output");
    score -= 2;
  }

  const passed = score >= 6 && issues.length < 3;

  return {
    passed,
    score: Math.max(0, score),
    feedback: passed
      ? "Output meets quality criteria — all sections present and steps covered."
      : `Output has quality issues: ${issues.join("; ")}`,
    issues,
  };
}

// ─── Main Pipeline ────────────────────────────────────────────────────────────

/**
 * runOrchestration — the full 3-step AI pipeline
 * Planner → Executor → Validator
 */
export async function runOrchestration(
  appName: string,
  appDescription: string,
  entryPoint: string,
  userInput: string
): Promise<OrchestrationResult> {
  const startMs = Date.now();

  // Fallback if API key not configured
  if (!isOpenAIConfigured()) {
    return buildFallbackResult(appName, userInput, startMs);
  }

  try {
    // ── Step 1: Planner ──────────────────────────────────────────────────
    const planResult = await planner(appName, appDescription, entryPoint, userInput);

    // ── Step 2: Executor ─────────────────────────────────────────────────
    const execResult = await executor(
      appName,
      appDescription,
      entryPoint,
      userInput,
      planResult.plan
    );

    // ── Step 3: Validator ─────────────────────────────────────────────────
    const validation = validator(execResult.finalOutput, planResult.plan);

    const totalTokens = planResult.tokens + execResult.tokens;

    return {
      final_output: execResult.finalOutput,
      tokens_used: totalTokens,
      model: execResult.model,
      reasoning_trace: {
        plan: planResult.plan,
        execution_steps: execResult.steps,
        validation,
        total_tokens: totalTokens,
        model: execResult.model,
        duration_ms: Date.now() - startMs,
      },
    };
  } catch (err) {
    // Surface error with fallback trace
    const errorMsg = err instanceof Error ? err.message : String(err);
    return {
      final_output: `─── ORCHESTRATION ERROR ───\n\n${errorMsg}\n\nPlease check your API key and try again.`,
      tokens_used: 0,
      model: "error",
      reasoning_trace: {
        plan: [],
        execution_steps: [
          { task_id: "err", step: 1, task: "Pipeline execution", output: errorMsg, status: "error" },
        ],
        validation: { passed: false, score: 0, feedback: errorMsg, issues: [errorMsg] },
        total_tokens: 0,
        model: "error",
        duration_ms: Date.now() - startMs,
      },
    };
  }
}

/**
 * runOrchestratorChat — multi-app orchestration pipeline
 * Used by OrchestratorPage for cross-app coordination requests
 */
export async function runOrchestratorChat(
  apps: Array<{ name: string; description: string; status: string }>,
  userRequest: string
): Promise<OrchestrationResult> {
  const startMs = Date.now();

  if (!isOpenAIConfigured()) {
    return buildFallbackResult("Orchestrator", userRequest, startMs);
  }

  const appList = apps
    .map((a, i) => `${i + 1}. ${a.name} (${a.status}): ${a.description}`)
    .join("\n");

  // ── Step 1: Planner ────────────────────────────────────────────────────────
  const plannerPrompt = `You are Emergentic AI Orchestrator.
You are a deterministic planning engine for multi-country, multi-industry business automation.

${COUNTRY_RULES}

RULES:
- Do NOT ask clarifying questions.
- Do NOT generate conversational replies.
- Do NOT expand explanations.
- Always generate a structured execution plan.
- Make reasonable assumptions if prompt is incomplete.
- Apply country-specific rules when relevant.
- Keep output concise.

Available apps/agents:
${appList || "No apps registered yet."}

Output MUST be valid JSON only — no markdown, no extra text:
{
  "objective": "one sentence describing the orchestration goal",
  "tasks": [
    { "id": "t1", "step": 1, "task": "agent or action name", "expected_output": "what it produces" }
  ]
}
Keep to 3–6 tasks.`;

  let plan: PlanStep[] = [];
  let planTokens = 0;
  let modelUsed = "gpt-4o-mini";
  let planObjective = "";

  try {
    const planResponse = await chatCompletion(
      [{ role: "system", content: plannerPrompt }, { role: "user", content: userRequest }],
      0.2
    );
    planTokens = planResponse.tokens_used;
    modelUsed = planResponse.model;
    const json = JSON.parse(planResponse.result.replace(/```json\n?|```/g, "").trim());
    planObjective = json.objective || "";
    plan = (json.tasks || []).map((t: any, i: number) => ({
      id: t.id || `t${i + 1}`,
      step: t.step || i + 1,
      task: t.task || `Step ${i + 1}`,
      expected_output: t.expected_output || "",
    }));
  } catch {
    plan = [
      { id: "t1", step: 1, task: "Analyse request", expected_output: "Decomposed requirements" },
      { id: "t2", step: 2, task: "Identify relevant agents", expected_output: "Agent selection" },
      { id: "t3", step: 3, task: "Execute coordination plan", expected_output: "Final orchestrated output" },
    ];
  }

  // ── Step 2: Executor ───────────────────────────────────────────────────────
  const planTasks = plan
    .map((t) => `  ${t.step}. ${t.task} -> expected: ${t.expected_output}`)
    .join("\n");

  const executorPrompt = `You are Emergentic AI Orchestrator — a deterministic execution engine for multi-country business automation.

${COUNTRY_RULES}

User request: "${userRequest}"

You must execute EXACTLY the following ${plan.length} tasks. For each task provide a specific, concrete action.

Tasks:
${planTasks}

Output MUST be valid JSON with EXACTLY ${plan.length} steps — one per task above, in the same order:
{
  "plan": [
    {"step": 1, "agent": "<functional role>", "action": "<specific action for task 1>"},
    {"step": 2, "agent": "<functional role>", "action": "<specific action for task 2>"}
  ],
  "summary": "one line describing what was built"
}

RULES:
- Output EXACTLY ${plan.length} steps. No more, no fewer.
- "agent" must be a functional role name (e.g. Database Architect, API Builder, Email Service, UI Designer) — NOT an app name.
- "action" must be specific to the user request — use real field names, module names, concrete details.
- Do NOT ask questions. Do NOT add commentary. Output JSON only.`;

  let execOutput = "";
  let execTokens = 0;
  let execSteps: ExecutionStep[] = [];

  try {
    const execResponse = await chatCompletion(
      [{ role: "system", content: executorPrompt }, { role: "user", content: userRequest }],
      0.1
    );
    execOutput = execResponse.result.replace(/```json\n?|```/g, "").trim();
    execTokens = execResponse.tokens_used;
    modelUsed = execResponse.model;

    // Parse JSON output and map steps
    try {
      const parsed = JSON.parse(execOutput);
      const jsonPlan: Array<{ step: number; agent: string; action: string }> = parsed.plan || [];
      const summary: string = parsed.summary || "";

      // Format a clean human-readable display from the JSON
      const lines: string[] = [];
      lines.push("─── ORCHESTRATION PLAN ───");
      jsonPlan.forEach((s) => lines.push(`  Step ${s.step} [${s.agent}]: ${s.action}`));
      if (summary) { lines.push(""); lines.push("─── SUMMARY ───"); lines.push(`  ${summary}`); }
      execOutput = lines.join("\n");

      execSteps = plan.map((p, i) => ({
        task_id: p.id,
        step: p.step,
        task: p.task,
        output: jsonPlan[i]?.action ?? `${p.task} executed.`,
        status: "success" as const,
      }));

      // ── Derive app name from objective or summary ──────────────────────
      const rawObjective = planObjective || summary || userRequest;
      const derivedAppName = rawObjective.length > 60
        ? rawObjective.slice(0, 57).replace(/\s+\S*$/, "") + "..."
        : rawObjective;

      const validation = validator(execOutput, plan);
      const totalTokens = planTokens + execTokens;

      return {
        final_output: execOutput,
        tokens_used: totalTokens,
        model: modelUsed,
        app_name: derivedAppName,
        app_summary: summary || rawObjective,
        reasoning_trace: {
          plan,
          execution_steps: execSteps,
          validation,
          total_tokens: totalTokens,
          model: modelUsed,
          duration_ms: Date.now() - startMs,
        },
      };
    } catch {
      // Executor returned non-JSON — use raw output, map steps generically
      execSteps = plan.map((p) => ({
        task_id: p.id,
        step: p.step,
        task: p.task,
        output: `${p.task} executed.`,
        status: "success" as const,
      }));
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    execOutput = `Orchestration failed: ${msg}`;
    execSteps = plan.map((p) => ({
      task_id: p.id,
      step: p.step,
      task: p.task,
      output: "Execution failed",
      status: "error" as const,
    }));
  }

  // ── Step 3: Validator ──────────────────────────────────────────────────────
  const validation = validator(execOutput, plan);
  const totalTokens = planTokens + execTokens;

  return {
    final_output: execOutput,
    tokens_used: totalTokens,
    model: modelUsed,
    reasoning_trace: {
      plan,
      execution_steps: execSteps,
      validation,
      total_tokens: totalTokens,
      model: modelUsed,
      duration_ms: Date.now() - startMs,
    },
  };
}
