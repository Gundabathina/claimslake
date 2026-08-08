import { Nav } from "./components/Nav";
import { Hero } from "./components/Hero";
import { HowItWorks } from "./components/HowItWorks";
import { Architecture } from "./components/Architecture";
import { PipelineDemo } from "./components/PipelineDemo";
import { Evidence } from "./components/Evidence";
import { VerifiedResults } from "./components/VerifiedResults";
import { EngineeringDecisions } from "./components/EngineeringDecisions";
import { ExploreData } from "./components/ExploreData";
import { SqlAnalytics } from "./components/SqlAnalytics";
import { DemoVideo } from "./components/DemoVideo";
import { TechStack } from "./components/TechStack";
import { GithubCta } from "./components/GithubCta";
import { Footer } from "./components/Footer";

export default function App() {
  return (
    <div className="min-h-screen bg-bg text-text">
      <a
        href="#how-it-works"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[60] focus:m-3 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-bg"
      >
        Skip to content
      </a>
      <Nav />
      <main>
        <Hero />
        <HowItWorks />
        <Architecture />
        <PipelineDemo />
        <Evidence />
        <VerifiedResults />
        <EngineeringDecisions />
        <ExploreData />
        <SqlAnalytics />
        <DemoVideo />
        <TechStack />
        <GithubCta />
      </main>
      <Footer />
    </div>
  );
}
