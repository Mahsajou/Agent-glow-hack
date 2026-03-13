"use client";

import { Download, ExternalLink, Monitor } from "lucide-react";

interface Props {
  html: string;
  isLoading?: boolean;
}

export default function PortfolioPreview({ html, isLoading }: Props) {
  const handleDownload = () => {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "portfolio.jsx";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleOpenNew = () => {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Preview header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#1a1a1a] flex-shrink-0">
        <div className="flex items-center gap-2">
          <Monitor size={13} className="text-[#444]" />
          <span className="text-xs text-[#444] tracking-widest uppercase">Preview</span>
          {isLoading && (
            <span className="text-xs text-[#c8f050] animate-pulse">updating...</span>
          )}
        </div>
        {html && (
          <div className="flex gap-2">
            <button
              onClick={handleOpenNew}
              className="flex items-center gap-1.5 text-xs text-[#555] hover:text-[#e8e4dc] transition-colors"
            >
              <ExternalLink size={11} />
              Open
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 text-xs px-3 py-1 border border-[#222] rounded-sm text-[#888] hover:border-[#c8f050] hover:text-[#c8f050] transition-colors"
            >
              <Download size={11} />
              Download
            </button>
          </div>
        )}
      </div>

      {/* Preview area */}
      <div className="flex-1 relative bg-[#0d0d0d]">
        {html ? (
          <iframe
            key={html.slice(0, 100)} // re-mount on significant changes
            srcDoc={html}
            sandbox="allow-scripts allow-same-origin"
            className={`w-full h-full border-0 transition-opacity duration-300 ${isLoading ? "opacity-50" : "opacity-100"}`}
            title="Portfolio preview"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <div className="w-12 h-12 border border-[#1a1a1a] rounded-sm flex items-center justify-center">
              <Monitor size={20} className="text-[#2a2a2a]" />
            </div>
            <p className="text-xs text-[#2a2a2a] text-center">
              Portfolio will appear here
              <br />
              once generation is complete
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
