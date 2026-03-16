/**
 * OpenAI Service
 * Direct GPT-4o-mini integration for intelligent app execution
 */

const API_KEY = import.meta.env.VITE_OPENAI_API_KEY as string;
const MODEL = (import.meta.env.VITE_OPENAI_MODEL as string) || "gpt-4o-mini";
const ENDPOINT = "https://api.openai.com/v1/chat/completions";

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface OpenAIResponse {
  result: string;
  tokens_used: number;
  model: string;
}

/**
 * Core chat call — send messages, get response
 */
export async function chatCompletion(
  messages: ChatMessage[],
  temperature = 0.4
): Promise<OpenAIResponse> {
  if (!API_KEY) throw new Error("OpenAI API key not configured");

  const res = await fetch(ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      messages,
      temperature,
      max_tokens: 1024,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      err?.error?.message || `OpenAI error ${res.status}: ${res.statusText}`
    );
  }

  const data = await res.json();
  return {
    result: data.choices?.[0]?.message?.content?.trim() ?? "",
    tokens_used: data.usage?.total_tokens ?? 0,
    model: data.model ?? MODEL,
  };
}

/**
 * Run an app with AI — sends app context + user input to GPT
 * Returns a structured markdown-style analysis
 */
export async function runAppWithAI(
  appName: string,
  appDescription: string,
  entryPoint: string,
  userInput: string
): Promise<OpenAIResponse> {
  const systemPrompt = `You are an AI execution engine running inside "${appName}".

App description: ${appDescription}
Entry point: ${entryPoint}

Your job:
1. Read the user's input carefully
2. Process it according to what this app is supposed to do (based on its name and description)
3. Return a clear, structured output report with sections like:
   - PARSED INPUT (what you received)
   - PROCESSING STEPS (what you did)
   - RESULTS / OUTPUT (the actual output)
   - SUMMARY (1-2 sentence conclusion)

Be specific — use the actual values from the user's input in your output.
Format using plain text with clear section headers using ─── dividers.
Keep it concise but complete. Do NOT make up data not in the input.`;

  return chatCompletion([
    { role: "system", content: systemPrompt },
    { role: "user", content: userInput || "(no input provided)" },
  ]);
}

/**
 * Orchestrator call — ask GPT to coordinate multiple apps/agents
 */
export async function orchestratorChat(
  apps: Array<{ name: string; description: string; status: string }>,
  userRequest: string
): Promise<OpenAIResponse> {
  const appList = apps
    .map((a, i) => `${i + 1}. ${a.name} (${a.status}): ${a.description}`)
    .join("\n");

  const systemPrompt = `You are the Emergentic AI Orchestrator — a master AI agent that coordinates multiple apps and agents.

Available apps/agents:
${appList}

Your job when the user asks something:
1. Decide which app(s) should handle the request
2. Explain the execution plan (which agents to invoke and in what order)
3. Show the expected data flow between agents
4. Give a final consolidated result

Always structure your response with:
─── ORCHESTRATION PLAN ───
─── AGENT EXECUTION ───
─── DATA FLOW ───
─── FINAL OUTPUT ───`;

  return chatCompletion([
    { role: "system", content: systemPrompt },
    { role: "user", content: userRequest },
  ]);
}

export const isOpenAIConfigured = (): boolean =>
  Boolean(API_KEY && API_KEY.startsWith("sk-"));
