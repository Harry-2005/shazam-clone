import React, { useState, useRef } from 'react';
import './AudioRecorder.css';

/**
 * AudioRecorder Component
 * 
 * Allows users to record audio from their microphone.
 * Uses Web Audio API (MediaRecorder).
 */
const AudioRecorder = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioURL, setAudioURL] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  /**
   * Start recording audio
   */
  const startRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true 
      });

      // Create MediaRecorder instance
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // Collect audio data chunks
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = () => {
        // Create blob from chunks
        const audioBlob = new Blob(chunksRef.current, { 
          type: 'audio/wav' 
        });
        
        // Create URL for playback
        const url = URL.createObjectURL(audioBlob);
        setAudioURL(url);

        // Pass blob to parent component
        if (onRecordingComplete) {
          onRecordingComplete(audioBlob);
        }

        // Stop all tracks (release microphone)
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((time) => time + 1);
      }, 1000);

    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  /**
   * Stop recording audio
   */
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  /**
   * Format time for display (MM:SS)
   */
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="audio-recorder">
      <h3>🎤 Record Audio</h3>
      
      <div className="recorder-controls">
        {!isRecording ? (
          <button 
            className="btn btn-record" 
            onClick={startRecording}
          >
            Start Recording
          </button>
        ) : (
          <>
            <div className="recording-indicator">
              <span className="recording-dot"></span>
              Recording: {formatTime(recordingTime)}
            </div>
            <button 
              className="btn btn-stop" 
              onClick={stopRecording}
            >
              Stop Recording
            </button>
          </>
        )}
      </div>

      {audioURL && !isRecording && (
        <div className="audio-preview">
          <p>✓ Recording complete!</p>
          <audio controls src={audioURL}></audio>
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;