import { Link } from 'react-router-dom';
import './Header.css';

function Header() {
  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          <h1>🎵 TuneTrace</h1>
        </Link>
        <nav className="nav">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/identify" className="nav-link">Identify</Link>
          <Link to="/upload" className="nav-link">Upload</Link>
          <Link to="/library" className="nav-link">Library</Link>
        </nav>
      </div>
    </header>
  );
}

export default Header;
