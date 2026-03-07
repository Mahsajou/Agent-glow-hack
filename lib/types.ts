export type StepId = "contents" | "search" | "answer" | "research" | "vibe" | "generate";
export type StepStatus = "idle" | "running" | "done" | "error";

export interface Step {
  id: StepId;
  label: string;
  detail: string;
  status: StepStatus;
  summary?: string;
  api: string;
}

export interface ColorPalette {
  background: string;
  surface: string;
  primary_text: string;
  secondary_text: string;
  accent: string;
  accent_secondary: string;
}

export interface Vibe {
  vibe_summary: string;
  theme: string;
  typography_style: string;
  color_palette: ColorPalette;
  layout_style: string;
  motion_style: string;
  personality_match: string;
  font_suggestions: { display: string; body: string; mono: string };
  tagline_style: string;
}

export interface NudgeOption {
  id: string;
  label: string;
  icon: string;
}

export interface AgentEvent {
  event: string;
  step?: StepId;
  label?: string;
  detail?: string;
  summary?: string;
  data?: Record<string, unknown>;
  vibe?: Vibe;
  html?: string;
  nudge_id?: string;
  options?: NudgeOption[];
  error?: string;
  message?: string;
  name?: string;
  urls?: string[];
}

export const INITIAL_STEPS: Step[] = [
  { id: "contents",  label: "Scraping your links",         detail: "Exa Contents API",  status: "idle", api: "Contents" },
  { id: "search",    label: "Mapping public presence",     detail: "Exa Search API",    status: "idle", api: "Search"   },
  { id: "answer",    label: "Answering targeted Q&A",      detail: "Exa Answer API",    status: "idle", api: "Answer"   },
  { id: "research",  label: "Deep profile extraction",     detail: "Exa Research API",  status: "idle", api: "Research" },
  { id: "vibe",      label: "Inferring your aesthetic",    detail: "GMI",               status: "idle", api: "GMI"      },
  { id: "generate",  label: "Generating your portfolio",   detail: "GMI",               status: "idle", api: "GMI"      },
];
