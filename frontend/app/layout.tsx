import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Battery-RAG Agent",
  description: "Bootstrap shell for the Battery-RAG Agent web platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
              <Link href="/" className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-900">
                Battery-RAG Agent
              </Link>
              <nav className="flex items-center gap-6 text-sm text-slate-600">
                <Link href="/">Home</Link>
                <Link href="/login">Login</Link>
                <Link href="/register">Register</Link>
                <Link href="/dashboard">Dashboard</Link>
                <Link href="/projects">Projects</Link>
              </nav>
            </div>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
