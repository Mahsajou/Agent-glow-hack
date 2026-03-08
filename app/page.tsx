"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [context, setContext] = useState("");

  const canSubmit = name.trim().length > 0;

  const handleGenerate = () => {
    const params = new URLSearchParams({
      name: name.trim(),
      context: context.trim(),
    });
    router.push(`/generate?${params.toString()}`);
  };

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="px-8 py-6 flex items-center justify-between border-b border-[#1a1a1a]">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 bg-[#c8f050] rounded-sm flex items-center justify-center">
            <Sparkles size={14} className="text-black" />
          </div>
          <span className="font-display text-sm font-700 tracking-widest uppercase text-[#e8e4dc]">
            Persona
          </span>
        </div>
        <span className="text-xs text-[#444] tracking-wider">
          Powered by Exa + GMI
        </span>
      </header>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-20">
        <div className="w-full max-w-xl">
          {/* Title */}
          <div className="mb-12">
            <p className="text-xs text-[#c8f050] tracking-[0.3em] uppercase mb-4">
              Agent-powered portfolio generation
            </p>
            <h1 className="font-display text-5xl font-800 leading-[1.05] text-[#e8e4dc] mb-4">
              Just your name.<br />
              We search, research,<br />
              and build.
            </h1>
            <p className="text-sm text-[#555] leading-relaxed mt-4">
              Our agent searches the web, fetches content, researches your background,
              infers your aesthetic, and generates a portfolio that sounds like you.
            </p>
          </div>

          {/* Form */}
          <div className="space-y-6">
            {/* Name */}
            <div>
              <label className="block text-xs text-[#555] tracking-widest uppercase mb-2">
                Your name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Jane Doe"
                className="w-full bg-[#111] border border-[#222] rounded-sm px-4 py-3 text-sm text-[#e8e4dc] placeholder-[#333] focus:outline-none focus:border-[#c8f050] transition-colors"
              />
            </div>

            {/* Context */}
            <div>
              <label className="block text-xs text-[#555] tracking-widest uppercase mb-2">
                Additional context{" "}
                <span className="text-[#333] normal-case tracking-normal">(optional)</span>
              </label>
              <textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="e.g. ML engineer at a startup, 5 years exp, interested in developer tools and music production"
                rows={3}
                className="w-full bg-[#111] border border-[#222] rounded-sm px-4 py-3 text-sm text-[#e8e4dc] placeholder-[#333] focus:outline-none focus:border-[#c8f050] transition-colors resize-none"
              />
            </div>

            {/* Submit */}
            <button
              disabled={!canSubmit}
              onClick={handleGenerate}
              className="w-full flex items-center justify-between px-6 py-4 bg-[#c8f050] text-black font-display font-700 text-sm tracking-wide rounded-sm disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#d4f565] transition-colors group"
            >
              <span>Generate my portfolio</span>
              <ArrowRight
                size={16}
                className="group-hover:translate-x-1 transition-transform"
              />
            </button>
          </div>

          {/* Footer hint */}
          <p className="mt-8 text-xs text-[#2a2a2a] text-center">
            Search → Contents → Research → Vibe → Images → HTML
          </p>
        </div>
      </div>
    </main>
  );
}
