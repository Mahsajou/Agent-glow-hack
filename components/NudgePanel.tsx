"use client";

import {
  Sparkles, FolderOpen, Sun, Palette, Minus, Zap, Code, Loader
} from "lucide-react";

const ICON_MAP: Record<string, React.ReactNode> = {
  Sparkles:   <Sparkles size={12} />,
  FolderOpen: <FolderOpen size={12} />,
  Sun:        <Sun size={12} />,
  Palette:    <Palette size={12} />,
  Minus:      <Minus size={12} />,
  Zap:        <Zap size={12} />,
  Code:       <Code size={12} />,
};

const NUDGES = [
  { id: "hero",       label: "Regenerate hero",         icon: "Sparkles"   },
  { id: "projects",   label: "Emphasize projects",      icon: "FolderOpen" },
  { id: "tone_warm",  label: "Warmer tone",             icon: "Sun"        },
  { id: "colors",     label: "New color scheme",        icon: "Palette"    },
  { id: "minimal",    label: "More minimal",            icon: "Minus"      },
  { id: "bold",       label: "Bolder & dramatic",       icon: "Zap"        },
  { id: "skills",     label: "Redesign skills",         icon: "Code"       },
];

interface Props {
  onNudge: (id: string) => void;
  activeNudge: string | null;
}

export default function NudgePanel({ onNudge, activeNudge }: Props) {
  return (
    <div>
      <p className="text-xs text-[#444] tracking-widest uppercase mb-3">
        Refine
      </p>
      <div className="grid grid-cols-2 gap-1.5">
        {NUDGES.map((nudge) => {
          const isActive = activeNudge === nudge.id;
          return (
            <button
              key={nudge.id}
              onClick={() => !activeNudge && onNudge(nudge.id)}
              disabled={!!activeNudge}
              className={`flex items-center gap-2 px-3 py-2.5 border rounded-sm text-xs transition-all text-left
                ${isActive
                  ? "border-[#c8f050] text-[#c8f050] bg-[#c8f05010]"
                  : "border-[#1e1e1e] text-[#555] hover:border-[#333] hover:text-[#888] disabled:opacity-40 disabled:cursor-not-allowed"
                }`}
            >
              {isActive
                ? <Loader size={12} className="animate-spin flex-shrink-0" />
                : <span className="flex-shrink-0">{ICON_MAP[nudge.icon]}</span>
              }
              <span className="truncate">{nudge.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
