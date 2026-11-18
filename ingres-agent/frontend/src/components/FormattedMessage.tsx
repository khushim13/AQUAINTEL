"use client";

import React from "react";

interface FormattedMessageProps {
  content: string;
}

export default function FormattedMessage({ content }: FormattedMessageProps) {
  if (!content) return null;

  // Split lines
  const lines = content.split("\n");

  const renderInlineFormatted = (text: string) => {
    // Parse bold **text** and `code`
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);

    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code
            key={i}
            className="rounded bg-sky-50 px-1.5 py-0.5 font-mono text-xs text-sky-800 border border-sky-100"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="space-y-2 text-sm text-slate-800 leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return <div key={idx} className="h-1.5" />;
        }

        // Bullet point lines starting with • or - or *
        if (trimmed.startsWith("•") || trimmed.startsWith("-") || trimmed.startsWith("* ")) {
          const bulletText = trimmed.replace(/^[•\-*]\s*/, "");
          return (
            <div key={idx} className="flex items-start gap-2 pl-1 my-1">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-500" />
              <div className="flex-1">{renderInlineFormatted(bulletText)}</div>
            </div>
          );
        }

        // Standard text lines
        return (
          <p key={idx} className="leading-relaxed">
            {renderInlineFormatted(line)}
          </p>
        );
      })}
    </div>
  );
}
