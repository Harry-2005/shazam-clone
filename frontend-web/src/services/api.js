import axios from 'axios';

// Base URL for your API
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * API Service
 * 
 * This module handles all communication with the backend API.
 * Each function corresponds to an API endpoint.
 */

const apiService = {
  /**
   * Upload a song to the database
   * @param {File} audioFile - Audio file to upload
   * @param {Object} metadata - Song metadata (title, artist, album)
   * @returns {Promise} Response with song_id and fingerprint count
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
   * @param {Blob|File} audioBlob - Audio recording to identify
   * @returns {Promise} Match result with song details
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
   * @returns {Promise} Array of songs
   */
  getSongs: async () => {
    const response = await api.get('/songs');
    return response.data;
  },

  /**
   * Get details of a specific song
   * @param {number} songId - Song ID
   * @returns {Promise} Song details
   */
  getSong: async (songId) => {
    const response = await api.get(`/songs/${songId}`);
    return response.data;
  },

  /**
   * Delete a song from database
   * @param {number} songId - Song ID
   * @returns {Promise} Delete confirmation
   */
  deleteSong: async (songId) => {
    const response = await api.delete(`/songs/${songId}`);
    return response.data;
  },

  /**
   * Get database statistics
   * @returns {Promise} Stats object
   */
  getStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },

  /**
   * Health check
   * @returns {Promise} Health status
   */
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default apiService;