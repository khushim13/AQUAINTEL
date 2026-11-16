import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "INGRES-Agent | Groundwater Virtual Assistant (SIH25066)",
  description: "Virtual assistant for India's Groundwater Resource Estimation System (INGRES / CGWB)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}
