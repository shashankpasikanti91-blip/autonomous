/**
 * Orchestrator Page
 * Master AI agent — structured 3-step pipeline (Planner / Executor / Validator)
 */

import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { MainLayout } from "../components/layouts/MainLayout";
import { Card, Button } from "../components/common/UIComponents";
import { appService } from "../services";
import { isOpenAIConfigured } from "../services/openai";
import { runOrchestratorChat } from "../services/orchestrator";
import type { ReasoningTrace } from "../services/orchestrator";
import { dbLogExecution } from "../services/supabase";
import type { App } from "../types";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  tokens?: number;
  trace?: ReasoningTrace;
  created_app?: App;
}

export const OrchestratorPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [apps, setApps] = useState<App[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [aiReady] = useState(isOpenAIConfigured());
  const bottomRef = useRef<HTMLDivElement>(null);
  const totalTokens = messages.reduce((s, m) => s + (m.tokens || 0), 0);

  // Pre-fill prompt from dashboard navigation state
  useEffect(() => {
    const navState = location.state as { prompt?: string } | null;
    if (navState?.prompt) {
      setInput(navState.prompt);
      // Clear the navigation state so back-navigation doesn't re-apply it
      window.history.replaceState({}, "");
    }
  }, [location.state]);

  useEffect(() => {
    appService.listApps(undefined, 50).then((r) => setApps(r.items));
  }, []);

  useEffect(() => {
    if (messages.length === 0 && aiReady) {
      setMessages([{
        id: "welcome",
        role: "assistant",
        content: `Emergentic AI Orchestrator — ready.\n\nDescribe what you want to build or automate and I will generate a structured execution plan.\n\nSupports payroll rules for Malaysia, Singapore, India, Australia, UK, USA, Canada, Germany, Philippines, Indonesia, Sri Lanka, Nepal and more.\n\nExamples:\n  • Build a payroll processor for 50 employees\n  • Create an invoice generation system with PDF export\n  • Design a candidate screening pipeline with scoring\n  • Create an AI-powered visa tracking system with email reminders`,
        timestamp: new Date().toLocaleTimeString(),
      }]);
    }
  }, [aiReady]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = {
      id: `u_${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const userPrompt = input.trim();
      const result = await runOrchestratorChat(
        apps.map((a) => ({
          name: a.name,
          description: (a as any).description || a.name,
          status: a.status,
        })),
        userPrompt
      );

      // Register the new app in the system (writes to PostgreSQL)
      const newApp = await appService.createApp({
        name: result.app_name || userPrompt.slice(0, 60),
        description: result.app_summary || userPrompt,
        user_prompt: userPrompt,
      });
      setApps((prev) => [newApp, ...prev]);

      // Log execution to PostgreSQL
      await dbLogExecution(
        newApp.app_id,
        "orchestration_run",
        result.reasoning_trace.validation.passed ? "success" : "error",
        {
          input: userPrompt,
          tokens_used: result.tokens_used,
          model: result.model,
          duration_ms: result.reasoning_trace.duration_ms,
          score: result.reasoning_trace.validation.score,
          steps: result.reasoning_trace.execution_steps.length,
        }
      ).catch(() => { /* non-fatal */ });

      const assistantMsg: Message = {
        id: `a_${Date.now()}`,
        role: "assistant",
        content: result.final_output,
        timestamp: new Date().toLocaleTimeString(),
        tokens: result.tokens_used,
        trace: result.reasoning_trace,
        created_app: newApp,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: "system",
          content: `❌ Error: ${err instanceof Error ? err.message : "Unknown error"}`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <MainLayout>
      <div className="flex flex-col h-full max-w-5xl mx-auto w-full px-4 space-y-3">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">🧠 Orchestrator</h1>
            <p className="text-gray-400 text-sm mt-1">
              Master AI agent coordinating {apps.length} app{apps.length !== 1 ? "s" : ""} — powered by GPT-4o-mini
            </p>
          </div>
          <div className="flex items-center gap-3">
            {aiReady ? (
              <span className="flex items-center gap-2 text-sm text-green-400 bg-green-900/30 px-3 py-1 rounded-full">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                AI Online
              </span>
            ) : (
              <span className="text-sm text-red-400 bg-red-900/30 px-3 py-1 rounded-full">⚠ No API Key</span>
            )}
            {totalTokens > 0 && (
              <span className="text-xs text-gray-500">{totalTokens.toLocaleString()} tokens used</span>
            )}
          </div>
        </div>

        {/* Active agents */}
        <div className="flex gap-2 flex-wrap">
          {apps.map((a) => (
            <button
              key={a.app_id}
              onClick={() => navigate(`/apps/${a.app_id}`)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors hover:border-blue-500 ${
                a.status === "deployed"
                  ? "bg-green-900/20 border-green-800 text-green-300"
                  : "bg-gray-800 border-gray-700 text-gray-400"
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${a.status === "deployed" ? "bg-green-400" : "bg-gray-500"}`} />
              {a.name}
            </button>
          ))}
          <button
            onClick={() => navigate("/apps")}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-dashed border-gray-700 text-gray-500 hover:border-blue-500 hover:text-blue-400 transition-colors"
          >
            + Add App
          </button>
        </div>

        {/* Chat window */}
        <Card className="flex-1 min-h-0 flex flex-col overflow-hidden">
          <div className="flex-1 min-h-0 overflow-y-auto space-y-4 pr-1">
            {messages.length === 0 && !aiReady && (
              <div className="text-center py-16 space-y-3">
                <p className="text-4xl">🔑</p>
                <p className="text-white font-semibold">OpenAI key not configured</p>
                <p className="text-gray-400 text-sm">The orchestrator needs a valid key in <code className="text-yellow-300">.env</code> → <code className="text-yellow-300">VITE_OPENAI_API_KEY</code></p>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-3xl w-full rounded-xl px-4 py-3 text-sm break-words ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : msg.role === "system"
                    ? "bg-red-900/40 border border-red-800 text-red-300"
                    : "bg-gray-800 border border-gray-700 text-gray-100"
                }`}>
                  {msg.role === "assistant" && (
                    <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
                      <span>🧠 Orchestrator</span>
                      <span>{msg.timestamp}</span>
                      {msg.tokens ? <span>{msg.tokens.toLocaleString()} tokens</span> : null}
                    </div>
                  )}
                  <pre className="whitespace-pre-wrap break-words font-sans leading-relaxed">{msg.content}</pre>
                  {msg.role === "user" && (
                    <p className="text-xs text-blue-300 mt-1 text-right">{msg.timestamp}</p>
                  )}

                  {/* ─── App Created Banner ─── */}
                  {msg.created_app && (
                    <div className="mt-3 border border-green-700 bg-green-900/20 rounded-lg px-3 py-2 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 text-green-300 text-xs">
                        <span>✅</span>
                        <span className="font-semibold">App created:</span>
                        <span className="text-green-200">{msg.created_app.name}</span>
                      </div>
                      <button
                        onClick={() => navigate(`/apps/${msg.created_app!.app_id}`)}
                        className="shrink-0 text-xs px-3 py-1 rounded-md bg-green-700 hover:bg-green-600 text-white font-medium transition-colors"
                      >
                        Open App →
                      </button>
                    </div>
                  )}

                  {/* ─── Reasoning Trace Viewer ─── */}
                  {msg.trace && (
                    <details className="mt-3 border-t border-gray-700 pt-2">
                      <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-300 select-none flex items-center gap-1">
                        <span>🔍</span>
                        <span>Reasoning Trace</span>
                        <span className="ml-1 text-gray-600">—
                          {msg.trace.plan.length} steps ·
                          score {msg.trace.validation.score}/10 ·
                          {msg.trace.duration_ms}ms
                        </span>
                      </summary>

                      <div className="mt-2 space-y-3 text-xs">
                        {/* Plan */}
                        <div>
                          <p className="text-gray-500 font-semibold uppercase tracking-wide mb-1">Planner</p>
                          <div className="space-y-1">
                            {msg.trace.plan.map((step) => (
                              <div key={step.id} className="flex gap-2 text-gray-400">
                                <span className="text-gray-600 w-4 shrink-0">{step.step}.</span>
                                <span>{step.task}</span>
                                <span className="text-gray-600 ml-auto shrink-0">→ {step.expected_output}</span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Execution */}
                        <div>
                          <p className="text-gray-500 font-semibold uppercase tracking-wide mb-1">Executor</p>
                          <div className="space-y-2">
                            {msg.trace.execution_steps.map((step) => (
                              <div key={step.task_id} className="bg-gray-900 rounded p-2">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={step.status === "success" ? "text-green-400" : step.status === "error" ? "text-red-400" : "text-gray-500"}>
                                    {step.status === "success" ? "✓" : step.status === "error" ? "✕" : "—"}
                                  </span>
                                  <span className="text-gray-300 font-medium">{step.task}</span>
                                </div>
                                {step.output && (
                                  <p className="text-gray-500 pl-4 line-clamp-2">{step.output.slice(0, 120)}{step.output.length > 120 ? "…" : ""}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Validation */}
                        <div className={`rounded p-2 ${
                          msg.trace.validation.passed
                            ? "bg-green-950/40 border border-green-900/50"
                            : "bg-yellow-950/40 border border-yellow-900/50"
                        }`}>
                          <p className={`font-semibold uppercase tracking-wide mb-1 ${msg.trace.validation.passed ? "text-green-400" : "text-yellow-400"}`}>
                            Validator — {msg.trace.validation.passed ? "✅ Passed" : "⚠ Issues"}
                            <span className="ml-2 font-normal text-gray-400">({msg.trace.validation.score}/10)</span>
                          </p>
                          <p className="text-gray-400">{msg.trace.validation.feedback}</p>
                          {msg.trace.validation.issues.length > 0 && (
                            <ul className="mt-1 space-y-0.5">
                              {msg.trace.validation.issues.map((issue, i) => (
                                <li key={i} className="text-yellow-500/80">• {issue}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    </details>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    <span className="ml-1">Orchestrator thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input area */}
          <div className="mt-4 flex gap-2 border-t border-gray-700 pt-4">
            <textarea
              className="flex-1 px-4 py-3 bg-gray-900 border border-gray-600 rounded-xl text-white text-sm focus:outline-none focus:border-blue-500 resize-none"
              rows={2}
              placeholder="Ask the orchestrator anything... e.g. 'Process payroll for John Doe, salary 80000, 160 hours worked'"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <Button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-6 self-end"
            >
              {loading ? "⏳" : "Send ↵"}
            </Button>
          </div>
          <p className="text-xs text-gray-600 mt-1">Press Enter to send · Shift+Enter for new line</p>
        </Card>

      </div>
    </MainLayout>
  );
};

export default OrchestratorPage;
