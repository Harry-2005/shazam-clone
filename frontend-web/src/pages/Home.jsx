import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/api';
import './Home.css';

const Home = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await apiService.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  return (
    <div className="home">
      <div className="hero">
        <h1>🎵 TuneTrace</h1>
        <p className="tagline">
          Identify any song in seconds
        </p>
      </div>

      <div className="features">
        <Link to="/identify" className="feature-card">
          <div className="feature-icon">🎤</div>
          <h3>Identify Song</h3>
          <p>Record audio and instantly identify the song</p>
        </Link>

        <Link to="/upload" className="feature-card">
          <div className="feature-icon">📤</div>
          <h3>Upload Song</h3>
          <p>Add new songs to the database</p>
        </Link>

        <Link to="/library" className="feature-card">
          <div className="feature-icon">📚</div>
          <h3>Song Library</h3>
          <p>Browse all songs in the database</p>
        </Link>
      </div>

      {stats && (
        <div className="stats">
          <div className="stat-item">
            <div className="stat-number">{stats.total_songs}</div>
            <div className="stat-label">Songs</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">
              {stats.total_fingerprints.toLocaleString()}
            </div>
            <div className="stat-label">Fingerprints</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;