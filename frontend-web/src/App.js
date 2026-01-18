import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Identify from './pages/Identify';
import Upload from './pages/Upload';
import Library from './pages/Library';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <Link to="/" className="nav-logo">
            🎵 Shazam Clone
          </Link>
          <div className="nav-links">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/identify" className="nav-link">Identify</Link>
            <Link to="/upload" className="nav-link">Upload</Link>
            <Link to="/library" className="nav-link">Library</Link>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/identify" element={<Identify />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/library" element={<Library />} />
          </Routes>
        </main>

        <footer className="footer