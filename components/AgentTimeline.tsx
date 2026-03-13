"use client";

import { Check, Circle, Loader, X, Terminal } from "lucide-react";
import { Step } from "@/agent/lib/types";

interface Props {
  steps: Step[];
  currentStep: string | null;
}

const API_COLORS: Record<string, string> = {
  "Search":    "text-[#34d399]",
  "Contents":  "text-[#60a5fa]",
  "Research":  "text-[#a78bfa]",
  "OpenAI":    "text-[#10a37f]",
  "GMI":       "text-[#c8f050]",
};

export default function AgentTimeline({ steps, currentStep }: Props) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 mb-5 pb-4 border-b border-[#1a1a1a]">
        <Terminal size={13} className="text-[#444]" />
        <span className="text-xs text-[#444] tracking-widest uppercase">Agent log</span>
      </div>

      {steps.map((step, i) => {
        const isRunning = step.status === "running";
        const isDone    = step.status === "done";
        const isError   = step.status === "error";
        const isIdle    = step.status === "idle";

        return (
          <div
            key={step.id}
            className={`flex gap-3 py-2.5 px-3 rounded-sm transition-all duration-300 ${
              isRunning ? "bg-[#111]" : ""
            }`}
          >
            {/* Icon */}
            <div className="flex-shrink-0 mt-0.5">
              {isRunning && (
                <Loader size={14} className="text-[#c8f050] animate-spin" />
              )}
              {isDone && (
                <Check size={14} className="text-[#c8f050]" />
              )}
              {isError && (
                <X size={14} className="text-red-500" />
              )}
              {isIdle && (
                <Circle size={14} className="text-[#2a2a2a]" />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className={`text-xs font-medium transition-colors ${
                    isDone
                      ? "text-[#e8e4dc]"
                      : isRunning
                      ? "text-[#e8e4dc]"
                      : isError
                      ? "text-red-400"
                      : "text-[#333]"
                  }`}
                >
                  {isDone && step.summary ? step.summary : step.label}
                </span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-sm border border-[#1a1a1a] ${
                    API_COLORS[step.api] || "text-[#444]"
                  } ${isIdle ? "opacity-30" : ""}`}
                >
                  {step.api}
                </span>
              </div>

              {isRunning && (
                <p className="text-[10px] text-[#444] mt-0.5 truncate">
                  {step.detail}
                  <span className="cursor-blink ml-0.5">_</span>
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
