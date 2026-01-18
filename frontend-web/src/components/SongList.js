import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './SongList.css';

/**
 * SongList Component
 * 
 * Displays list of all songs in the database.
 */
const SongList = () => {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load songs when component mounts
  useEffect(() => {
    loadSongs();
  }, []);

  const loadSongs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getSongs();
      setSongs(data.songs);
    } catch (err) {
      setError('Failed to load songs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (songId, title) => {
    if (window.confirm(`Delete "${title}"?`)) {
      try {
        await apiService.deleteSong(songId);
        // Reload songs list
        loadSongs();
      } catch (err) {
        alert('Failed to delete song');
        console.error(err);
      }
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'Unknown';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return <div className="loading">Loading songs...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (songs.length === 0) {
    return (
      <div className="empty-state">
        <h3>No songs in database</h3>
        <p>Upload some songs to get started!</p>
      </div>
    );
  }

  return (
    <div className="song-list">
      <h2>Song Library ({songs.length})</h2>
      
      <div className="songs-grid">
        {songs.map((song) => (
          <div key={song.id} className="song-card">
            <div className="song-icon">🎵</div>
            <div className="song-details">
              <h3>{song.title}</h3>
              <p className="artist">{song.artist}</p>
              {song.album && <p className="album">{song.album}</p>}
              <p className="duration">
                Duration: {formatDuration(song.duration)}
              </p>
            </div>
            <button 
              className="btn-delete"
              onClick={() => handleDelete(song.id, song.title)}
              title="Delete song"
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SongList;