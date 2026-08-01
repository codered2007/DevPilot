import { Link } from "react-router-dom";
import Button from "../ui/Button";
import Container from "../ui/Container";

function Navbar() {
  return (
    <header className="border-b border-zinc-800">
      <Container>
        <nav className="flex h-16 items-center justify-between">
          <Link
            to="/"
            className="text-2xl font-bold tracking-tight text-white"
          >
            DevPilot
          </Link>

          <div className="flex items-center gap-3">
            <Button variant="ghost">Features</Button>
            <Button variant="ghost">Docs</Button>

            <Link to="/login">
              <Button>Login</Button>
            </Link>
          </div>
        </nav>
      </Container>
    </header>
  );
}

export default Navbar;