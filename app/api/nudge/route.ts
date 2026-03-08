import { NextRequest } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";
export const maxDuration = 120;

export async function POST(req: NextRequest) {
  const { nudgeId } = await req.json();

  const encoder = new TextEncoder();
  const stream = new TransformStream();
  const writer = stream.writable.getWriter();

  const send = (data: object) => {
    writer.write(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
  };

  const agentDir = path.join(process.cwd(), "agent");
  const pythonPath = path.join(process.cwd(), "venv", "bin", "python3");

  const proc = spawn(pythonPath, ["run.py", "nudge", nudgeId], {
    cwd: agentDir,
    env: {
      ...process.env,
      EXA_API_KEY: process.env.EXA_API_KEY!,
      GMI_API_KEY: process.env.GMI_API_KEY!,
      PYTHONPATH: agentDir,
    },
  });

  proc.stdout.on("data", (chunk: Buffer) => {
    const lines = chunk.toString().split("\n").filter(Boolean);
    for (const line of lines) {
      try {
        send(JSON.parse(line));
      } catch {
        // skip
      }
    }
  });

  proc.on("close", () => writer.close());
  proc.on("error", (err: Error) => {
    send({ event: "error", message: err.message });
    writer.close();
  });

  return new Response(stream.readable, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
