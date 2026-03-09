import { NextRequest } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";
export const maxDuration = 300;

export async function POST(req: NextRequest) {
  const { name, context } = await req.json();

  const encoder = new TextEncoder();
  const stream = new TransformStream();
  const writer = stream.writable.getWriter();

  const send = (data: object) => {
    writer.write(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
  };

  const agentDir = path.join(process.cwd(), "agent");
  const pythonPath = path.join(process.cwd(), ".venv", "bin", "python3");
  const args = ["run_direct.py", name, context || ""];

  const proc = spawn(pythonPath, args, {
    cwd: agentDir,
    env: {
      ...process.env,
      EXA_API_KEY: process.env.EXA_API_KEY!,
      GMI_API_KEY: process.env.GMI_API_KEY!,
      PYTHONPATH: path.join(process.cwd()),
    },
  });

  let stdoutBuffer = "";
  proc.stdout.on("data", (chunk: Buffer) => {
    stdoutBuffer += chunk.toString();
    const lines = stdoutBuffer.split("\n");
    stdoutBuffer = lines.pop() ?? ""; // keep incomplete line for next chunk
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const parsed = JSON.parse(line);
        send(parsed);
      } catch {
        // not JSON, skip
      }
    }
  });

  proc.stderr.on("data", (chunk: Buffer) => {
    const msg = chunk.toString();
    // Only forward if it looks like an actual error, not Python warnings
    if (msg.includes("Error") || msg.includes("Traceback")) {
      send({ event: "stderr", message: msg });
    }
  });

  proc.on("close", (code: number) => {
    send({ event: "process_exit", code });
    writer.close();
  });

  proc.on("error", (err: Error) => {
    send({ event: "process_error", message: err.message });
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
