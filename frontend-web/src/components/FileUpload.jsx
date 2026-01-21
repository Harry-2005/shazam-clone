import { useState } from 'react';
import './FileUpload.css';

function FileUpload({ onFileSelect }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('audio/')) {
      setSelectedFile(file);
      onFileSelect(file);
    } else {
      alert('Please select a valid audio file');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('audio/')) {
      setSelectedFile(file);
      onFileSelect(file);
    } else {
      alert('Please select a valid audio file');
    }
  };

  return (
    <div className="file-upload">
      <div
        className={`upload-area ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          accept="audio/*"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-input" className="upload-label">
          <div className="upload-icon">📁</div>
          <p className="upload-text">
            {selectedFile ? selectedFile.name : 'Click to select or drag & drop an audio file'}
          </p>
          <p className="upload-hint">Supported formats: MP3, WAV, OGG, M4A</p>
        </label>
      </div>
    </div>
  );
}

export default FileUpload;
