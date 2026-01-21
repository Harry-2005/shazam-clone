import axios from 'axios';

// Base URL for your API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * API Service
 * Handles all communication with the backend API
 */
const apiService = {
  /**
   * Upload a song to the database
   */
  uploadSong: async (audioFile, metadata) => {
    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('title', metadata.title);
    formData.append('artist', metadata.artist);
    if (metadata.album) {
      formData.append('album', metadata.album);
    }

    const response = await api.post('/songs/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Identify a song from audio recording
   */
  identifySong: async (audioBlob) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');

    const response = await api.post('/identify', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Get list of all songs
   */
  getSongs: async () => {
    const response = await api.get('/songs');
    return response.data;
  },

  /**
   * Get details of a specific song
   */
  getSong: async (songId) => {
    const response = await api.get(`/songs/${songId}`);
    return response.data;
  },

  /**
   * Delete a song from database
   */
  deleteSong: async (songId) => {
    const response = await api.delete(`/songs/${songId}`);
    return response.data;
  },

  /**
   * Get database statistics
   */
  getStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },

  /**
   * Health check
   */
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default apiService;