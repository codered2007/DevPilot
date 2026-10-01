import Navbar from "../../components/layout/Navbar";
import Hero from "../../components/sections/Hero";
import Container from "../../components/ui/Container";

function Landing() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0D1117] text-white">
      {/* GitHub-inspired background texture */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.22]"
        style={{
          backgroundImage: `
            radial-gradient(
              circle at 20% 20%,
              rgba(88, 166, 255, 0.12) 1px,
              transparent 1px
            ),
            radial-gradient(
              circle at 80% 60%,
              rgba(139, 148, 158, 0.08) 1px,
              transparent 1px
            )
          `,
          backgroundSize: "32px 32px, 48px 48px",
        }}
      />

      {/* Subtle blue-gray glow */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-[500px]"
        style={{
          background:
            "radial-gradient(ellipse at 50% -20%, rgba(56, 139, 253, 0.10), transparent 65%)",
        }}
      />

      <div className="relative z-10">
        <Navbar />

        <Container>
          <Hero />
        </Container>
      </div>
    </div>
  );
}

export default Landing;