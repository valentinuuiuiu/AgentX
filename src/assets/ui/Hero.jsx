import React from "react";

export default function Hero({ title, subtitle, ctaLabel, onCta }) {
  return (
    <section className="relative min-h-[70vh] bg-gradient-to-br from-indigo-600 to-purple-700 text-white flex items-center justify-center">
      <div className="max-w-2xl text-center p-8">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">{title}</h1>
        <p className="text-lg md:text-xl mb-6">{subtitle}</p>
        <button
          className="bg-amber-500 hover:bg-amber-600 text-white font-medium py-2 px-6 rounded"
          onClick={onCta}
        >
          {ctaLabel}
        </button>
      </div>
    </section>
  );
}
