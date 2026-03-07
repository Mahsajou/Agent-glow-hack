"use client";

import { Palette } from "lucide-react";
import { Vibe } from "@/lib/types";

interface Props {
  vibe: Vibe;
}

export default function VibeCard({ vibe }: Props) {
  const colors = vibe.color_palette;

  return (
    <div className="border border-[#1a1a1a] rounded-sm p-4 animate-slide-up">
      <div className="flex items-center gap-2 mb-3">
        <Palette size={13} className="text-[#c8f050]" />
        <span className="text-xs text-[#c8f050] tracking-widest uppercase">
          Aesthetic inferred
        </span>
      </div>

      {/* Vibe summary */}
      <p className="text-xs text-[#888] leading-relaxed mb-4">
        {vibe.vibe_summary}
      </p>

      {/* Color swatches */}
      <div className="flex gap-1.5 mb-3">
        {Object.entries(colors).map(([key, hex]) => (
          <div key={key} className="group relative">
            <div
              className="w-7 h-7 rounded-sm border border-[#222] cursor-default"
              style={{ backgroundColor: hex }}
            />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-[#1a1a1a] text-[9px] text-[#888] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              {hex}
            </div>
          </div>
        ))}
      </div>

      {/* Font + layout tags */}
      <div className="flex flex-wrap gap-1.5">
        {[
          vibe.font_suggestions?.display,
          vibe.layout_style,
          vibe.motion_style,
        ]
          .filter(Boolean)
          .map((tag) => (
            <span
              key={tag}
              className="text-[10px] px-2 py-0.5 bg-[#111] border border-[#222] rounded-sm text-[#555]"
            >
              {tag}
            </span>
          ))}
      </div>

      {/* Personality */}
      <p className="mt-3 text-[10px] text-[#c8f050] tracking-wide">
        ↳ {vibe.personality_match}
      </p>
    </div>
  );
}
