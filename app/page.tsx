"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Minus, ArrowRight, Sparkles } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [context, setContext] = useState("");
  const [urls, setUrls] = useState(["", "", ""]);

  const addUrl = () => setUrls([...urls, ""]);
  const removeUrl = (i: number) => setUrls(urls.filter((_, idx) => idx !== i));
  const setUrl = (i: number, val: string) => setUrls(urls.map((u, idx) => (idx === i ? val : u)));

  const validUrls = urls.filter((u) => u.trim().length > 0);
  const canSubmit = name.trim() && validUrls.length > 0;

  const handleGenerate = () => {
    const params = new URLSearchParams({
      name: name.trim(),
      context: context.trim(),
      urls: validUrls.join(","),
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
              Drop your links.<br />
              We figure out<br />
              the rest.
            </h1>
            <p className="text-sm text-[#555] leading-relaxed mt-4">
              Our agent scrapes your presence across the web, infers your aesthetic,
              and generates a portfolio that actually sounds like you.
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

            {/* Links */}
            <div>
              <label className="block text-xs text-[#555] tracking-widest uppercase mb-2">
                Your links
              </label>
              <div className="space-y-2">
                {urls.map((url, i) => (
                  <div key={i} className="flex gap-2 items-center">
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(i, e.target.value)}
                      placeholder={
                        i === 0
                          ? "https://github.com/you"
                          : i === 1
                          ? "https://linkedin.com/in/you"
                          : "https://yoursite.com"
                      }
                      className="flex-1 bg-[#111] border border-[#222] rounded-sm px-4 py-3 text-sm text-[#e8e4dc] placeholder-[#333] focus:outline-none focus:border-[#c8f050] transition-colors"
                    />
                    {urls.length > 1 && (
                      <button
                        onClick={() => removeUrl(i)}
                        className="p-3 border border-[#222] rounded-sm text-[#444] hover:text-[#e8e4dc] hover:border-[#444] transition-colors"
                      >
                        <Minus size={14} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button
                onClick={addUrl}
                className="mt-2 flex items-center gap-1.5 text-xs text-[#444] hover:text-[#c8f050] transition-colors"
              >
                <Plus size={12} />
                Add another link
              </button>
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
            5 Exa APIs · GMI · ~90 seconds
          </p>
        </div>
      </div>
    </main>
  );
}
