"use client";

import { useEffect, useRef, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, Sparkles } from "lucide-react";
import AgentTimeline from "@/components/AgentTimeline";
import VibeCard from "@/components/VibeCard";
import NudgePanel from "@/components/NudgePanel";
import PortfolioPreview from "@/components/PortfolioPreview";
import { AgentEvent, INITIAL_STEPS, Step, Vibe } from "@/lib/types";

function GeneratePage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const name    = searchParams.get("name") || "";
  const context = searchParams.get("context") || "";
  const urls    = (searchParams.get("urls") || "").split(",").filter(Boolean);

  const [steps, setSteps]             = useState<Step[]>(INITIAL_STEPS);
  const [vibe, setVibe]               = useState<Vibe | null>(null);
  const [portfolioHtml, setPortfolioHtml] = useState<string>("");
  const [isDone, setIsDone]           = useState(false);
  const [activeNudge, setActiveNudge] = useState<string | null>(null);
  const [nudgeLoading, setNudgeLoading] = useState(false);
  const [error, setError]             = useState<string | null>(null);
  const hasStarted = useRef(false);

  const updateStep = (id: string, patch: Partial<Step>) => {
    setSteps((prev) =>
      prev.map((s) => (s.id === id ? { ...s, ...patch } : s))
    );
  };

  const handleEvent = (evt: AgentEvent) => {
    switch (evt.event) {
      case "step_start":
        updateStep(evt.step!, {
          status: "running",
          label: evt.label || "",
          detail: evt.detail || "",
        });
        break;

      case "step_done":
        updateStep(evt.step!, {
          status: "done",
          summary: evt.summary || "",
        });
        break;

      case "step_error":
        updateStep(evt.step!, {
          status: "error",
          summary: evt.error || "Error",
        });
        break;

      case "vibe_inferred":
        if (evt.vibe) setVibe(evt.vibe);
        break;

      case "portfolio_ready":
        if (evt.html) setPortfolioHtml(evt.html);
        break;

      case "agent_done":
        setIsDone(true);
        break;

      case "nudge_done":
        if (evt.html) setPortfolioHtml(evt.html);
        setActiveNudge(null);
        setNudgeLoading(false);
        break;

      case "nudge_error":
        setActiveNudge(null);
        setNudgeLoading(false);
        setError(evt.error || "Nudge failed");
        break;

      case "stderr":
      case "process_error":
        setError(evt.message || "Agent error");
        break;
    }
  };

  // Start generation
  useEffect(() => {
    if (hasStarted.current || !name || urls.length === 0) return;
    hasStarted.current = true;

    const run = async () => {
      try {
        const res = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, context, urls }),
        });

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const evt = JSON.parse(line.slice(6)) as AgentEvent;
                handleEvent(evt);
              } catch {
                // skip malformed
              }
            }
          }
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Connection error");
      }
    };

    run();
  }, []);

  // Handle nudge
  const handleNudge = async (nudgeId: string) => {
    setActiveNudge(nudgeId);
    setNudgeLoading(true);

    try {
      const res = await fetch("/api/nudge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nudgeId }),
      });

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              handleEvent(JSON.parse(line.slice(6)));
            } catch {
              // skip
            }
          }
        }
      }
    } catch (e: unknown) {
      setActiveNudge(null);
      setNudgeLoading(false);
      setError(e instanceof Error ? e.message : "Nudge failed");
    }
  };

  const doneCount = steps.filter((s) => s.status === "done").length;
  const totalCount = steps.length;

  return (
    <div className="min-h-screen flex flex-col bg-[#080808]">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-[#1a1a1a] flex-shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-1.5 text-xs text-[#444] hover:text-[#888] transition-colors"
          >
            <ArrowLeft size={13} />
            Back
          </button>
          <div className="w-px h-4 bg-[#1a1a1a]" />
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-[#c8f050] rounded-sm flex items-center justify-center">
              <Sparkles size={11} className="text-black" />
            </div>
            <span className="font-display text-sm font-700 text-[#e8e4dc] tracking-widest uppercase">
              Persona
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-[#333]">{name}</span>
          {!isDone && (
            <span className="text-xs text-[#444]">
              {doneCount}/{totalCount} steps
            </span>
          )}
          {isDone && (
            <span className="text-xs text-[#c8f050] tracking-wide">
              ✓ Complete
            </span>
          )}
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="px-6 py-2 bg-red-950 border-b border-red-900 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Main layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel — Agent */}
        <div className="w-72 flex-shrink-0 border-r border-[#1a1a1a] flex flex-col overflow-y-auto">
          <div className="p-5 flex-1">
            {/* Agent timeline */}
            <AgentTimeline steps={steps} currentStep={null} />

            {/* Vibe card */}
            {vibe && (
              <div className="mt-6 pt-5 border-t border-[#1a1a1a]">
                <VibeCard vibe={vibe} />
              </div>
            )}

            {/* Nudge panel */}
            {isDone && (
              <div className="mt-6 pt-5 border-t border-[#1a1a1a]">
                <NudgePanel onNudge={handleNudge} activeNudge={activeNudge} />
              </div>
            )}
          </div>
        </div>

        {/* Right panel — Portfolio preview */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <PortfolioPreview html={portfolioHtml} isLoading={nudgeLoading} />
        </div>
      </div>
    </div>
  );
}

export default function GeneratePageWrapper() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#080808]" />}>
      <GeneratePage />
    </Suspense>
  );
}
