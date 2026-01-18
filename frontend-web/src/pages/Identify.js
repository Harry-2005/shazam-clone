import React, { useState } from 'react';
import AudioRecorder from '../components/AudioRecorder';
import IdentifyResult from '../components/IdentifyResult';
import apiService from '../services/api';
import './Identify.css';

const Identify = () => {
  const [identifying, setIdentifying] = useState(false);
  const [result, setResult] = useState(null);

  const handleRecordingComplete = async (audioBlob) => {
    try {
      setIdentifying(true);
      setResult(null);
      
      const matchResult = await apiService.identifySong(audioBlob);
      setResult(matchResult);
    } catch (error) {
      console.error('Identification failed:', error);
      alert('Failed to identify song. Please try again.');
    } finally {
      setIdentifying(false);
    }
  };

  const handleReset = () => {
    setResult(null);
  };

  return (
    <div className="identify-page">
      <div className="page-header">
        <h1>🎤 Identify Song</h1>
        <p>Record a few seconds of audio to identify the song</p>
      </div>

      {!result && (
        <div className="identify-content">
          <AudioRecorder onRecordingComplete={handleRecordingComplete} />
          
          {identifying && (
            <div className="identifying-loader">
              <div className="loader"></div>
              <p>Analyzing audio...</p>
            </div>
          )}
        </div>
      )}

      <IdentifyResult result={result} onReset={handleReset} />
    </div>
  );
};

export default Identify;