import { useState } from 'react';
import apiService from '../services/api';
import './Upload.css';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [artist, setArtist] = useState('');
  const [album, setAlbum] = useState('');
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file || !title || !artist) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      setUploading(true);
      setSuccess(false);

      await apiService.uploadSong(file, {
        title,
        artist,
        album,
      });

      setSuccess(true);
      // Reset form
      setFile(null);
      setTitle('');
      setArtist('');
      setAlbum('');
      e.target.reset();

      setTimeout(() => setSuccess(false), 5000);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload song. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-page">
      <div className="page-header">
        <h1>📤 Upload Song</h1>
        <p>Add a new song to the database</p>
      </div>

      {success && (
        <div className="success-message">
          ✓ Song uploaded successfully!
        </div>
      )}

      <form className="upload-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="file">Audio File *</label>
          <input
            type="file"
            id="file"
            accept=".mp3,.wav,.flac,.ogg,.m4a"
            onChange={handleFileChange}
            required
          />
          <small>Supported formats: MP3, WAV, FLAC, OGG, M4A</small>
        </div>

        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter song title"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="artist">Artist *</label>
          <input
            type="text"
            id="artist"
            value={artist}
            onChange={(e) => setArtist(e.target.value)}
            placeholder="Enter artist name"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="album">Album (Optional)</label>
          <input
            type="text"
            id="album"
            value={album}
            onChange={(e) => setAlbum(e.target.value)}
            placeholder="Enter album name"
          />
        </div>

        <button 
          type="submit" 
          className="btn-submit"
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : 'Upload Song'}
        </button>
      </form>
    </div>
  );
};

export default Upload;