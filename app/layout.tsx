import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Persona — Your portfolio, generated",
  description: "Drop your links. We figure out the rest.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Syne:wght@400;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#080808] text-[#e8e4dc] font-mono antialiased">
        {children}
      </body>
    </html>
  );
}
