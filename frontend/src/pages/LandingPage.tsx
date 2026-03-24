import { Link } from "react-router";
import { buttonVariants } from "@/components/ui/button";
import { Database, Layers, Brain, RefreshCw } from "lucide-react";
import bannerImg from "@/assets/banner.png";

export function LandingPage() {
  // -- How It Works data --
  const blocks = [
    { icon: Database, label: "Data", stat: "20 seasons, ~1.2M plays" },
    {
      icon: Layers,
      label: "Features",
      stat: "17 game-level features, temporal boundaries",
    },
    {
      icon: Brain,
      label: "Models",
      stat: "Pick-em 63.7% + spreads ~10pt MAE",
    },
    {
      icon: RefreshCw,
      label: "Pipeline",
      stat: "Automated weekly refresh + human approval gate",
    },
  ];

  return (
    <div className="mx-auto max-w-4xl px-6">
      {/* -- Section 1: Hero -- */}
      <section className="relative flex min-h-[50vh] md:min-h-[50vh] flex-col items-center justify-center py-16 text-center">
        {/* Gradient overlay */}
        <div className="pointer-events-none absolute inset-0 bg-radial-[at_50%_65%] from-primary/8 to-transparent" />

        <h1 className="relative text-4xl md:text-5xl font-bold tracking-tight text-foreground">
          NFL Nostradamus
        </h1>

        <p className="relative mt-8 max-w-xl text-base md:text-lg text-muted-foreground">
          20 seasons of play-by-play data. 17 engineered features. One question:
          who wins Sunday?
        </p>

        <p className="relative mt-8 text-5xl md:text-7xl font-bold text-primary font-display leading-none">
          62.9%
        </p>

        <p className="relative mt-3 text-sm text-muted-foreground uppercase tracking-widest">
          validation accuracy
        </p>
      </section>

      {/* -- Separator 1 -- */}
      <div className="border-t border-border" />

      {/* -- Section 2: How It Works -- */}
      <section className="py-16">
        <h2 className="mb-10 text-center text-2xl font-bold text-foreground">
          How It Works
        </h2>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {blocks.map((block) => (
            <div key={block.label} className="rounded-lg bg-secondary/50 p-6">
              <block.icon className="mb-3 h-6 w-6 text-primary" />
              <p className="text-sm font-bold uppercase tracking-wide text-muted-foreground">
                {block.label}
              </p>
              <p className="mt-1 text-base text-foreground">{block.stat}</p>
            </div>
          ))}
        </div>
      </section>

      {/* -- Separator 2 -- */}
      <div className="border-t border-border" />

      {/* -- Section 3: Banner Image -- */}
      <section className="py-8">
        <img
          src={bannerImg}
          alt="Crystal ball on football field with holographic data visualizations"
          className="w-full rounded-lg object-cover"
        />
      </section>

      {/* -- Separator 3 -- */}
      <div className="border-t border-border" />

      {/* -- Section 4: CTAs -- */}
      <section className="py-16 text-center">
        <Link
          to="/history"
          className={buttonVariants({
            size: "lg",
            className: "px-8 text-base",
          })}
        >
          Explore Prediction History
        </Link>

        <div className="mt-6 flex items-center justify-center gap-6">
          <Link
            to="/accuracy"
            className="text-sm text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
          >
            Accuracy
          </Link>
          <Link
            to="/experiments"
            className="text-sm text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
          >
            Experiments
          </Link>
        </div>
      </section>

      {/* -- Section 5: Footer -- */}
      <footer className="border-t border-border py-8 text-center">
        <p className="text-sm text-muted-foreground">
          Built by{" "}
          <a
            href="https://silverreyes.net"
            target="_blank"
            rel="noopener noreferrer"
            className="text-foreground underline-offset-4 hover:underline"
          >
            Silver Reyes
          </a>
        </p>
        <a
          href="https://github.com/NatoJenkins/GamePredictor"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block text-sm text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
        >
          GitHub
        </a>
      </footer>
    </div>
  );
}
