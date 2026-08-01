import Navbar from "../../components/layout/Navbar";
import Hero from "../../components/sections/Hero";
import Container from "../../components/ui/Container";
import Features from "../../components/sections/Features";

function Landing() {
  return (
    <div className="min-h-screen bg-[#0B0D10] text-white">
      <Navbar />

      <Container>
        <Hero />
        <Features />
      </Container>
    </div>
  );
}

export default Landing;