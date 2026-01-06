import numpy as np
import librosa
from scipy.ndimage import maximum_filter
from scipy.ndimage import generate_binary_structure, binary_erosion
import hashlib
from typing import List, Tuple


class AudioFingerprinter:
    """
    Audio fingerprinting engine that converts audio into unique hashes.
    
    The process:
    1. Load audio file
    2. Convert to spectrogram (frequency vs time representation)
    3. Find peaks (loud points in the spectrogram)
    4. Create hashes from peak pairs
    5. Store hashes with time offsets
    """
    
    def __init__(self, 
                 sample_rate: int = 22050,
                 n_fft: int = 2048,
                 hop_length: int = 512,
                 freq_min: int = 20,
                 freq_max: int = 8000):
        """
        Initialize the fingerprinter with audio processing parameters.
        
        Args:
            sample_rate: Audio sample rate in Hz (22050 is good for music)
            n_fft: FFT window size (larger = better frequency resolution)
            hop_length: Number of samples between successive frames
            freq_min: Minimum frequency to consider (Hz)
            freq_max: Maximum frequency to consider (Hz)
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.freq_min = freq_min
        self.freq_max = freq_max
        
        # Peak finding parameters
        self.peak_neighborhood_size = 10  # Look for peaks in this radius
        self.min_amplitude = 10  # Minimum amplitude to consider a peak
        
        # Fingerprint parameters
        self.fan_value = 5  # How many peaks to pair with each peak
        self.target_zone_width = 50  # Time frames to look ahead
        self.target_zone_start = 10  # Where target zone starts
    
    def load_audio(self, filepath: str) -> np.ndarray:
        """
        Load audio file and convert to mono at our sample rate.
        
        Args:
            filepath: Path to audio file (mp3, wav, etc.)
            
        Returns:
            Audio time series as numpy array
        """
        # librosa.load automatically:
        # - Converts to mono
        # - Resamples to target sample rate
        # - Returns float array normalized to [-1, 1]
        audio, _ = librosa.load(filepath, sr=self.sample_rate, mono=True)
        return audio
    
    def compute_spectrogram(self, audio: np.ndarray) -> np.ndarray:
        """
        Convert audio signal to spectrogram.
        
        A spectrogram is a 2D representation where:
        - X-axis: Time
        - Y-axis: Frequency
        - Value: Amplitude (loudness)
        
        Args:
            audio: Audio time series
            
        Returns:
            Spectrogram as 2D numpy array
        """
        # STFT: Short-Time Fourier Transform
        # Breaks audio into small chunks and applies FFT to each
        stft = librosa.stft(audio, 
                           n_fft=self.n_fft, 
                           hop_length=self.hop_length)
        
        # Convert complex numbers to magnitude (amplitude)
        spectrogram = np.abs(stft)
        
        # Convert amplitude to decibels (logarithmic scale)
        # This matches how humans perceive loudness
        spectrogram_db = librosa.amplitude_to_db(spectrogram, ref=np.max)
        
        return spectrogram_db
    
    def find_peaks(self, spectrogram: np.ndarray) -> List[Tuple[int, int]]:
        """
        Find peaks (local maxima) in the spectrogram.
        
        Peaks represent distinctive frequency-time points in the audio.
        These are the "landmarks" we'll use for fingerprinting.
        
        Args:
            spectrogram: 2D spectrogram array
            
        Returns:
            List of (time_index, frequency_index) tuples
        """
        # Create a structure for finding local maxima
        # A point is a peak if it's the maximum in its neighborhood
        struct = generate_binary_structure(2, 1)
        neighborhood = binary_erosion(
            maximum_filter(spectrogram, footprint=struct) == spectrogram,
            structure=struct
        )
        
        # Get coordinates where peaks are located
        peaks = np.where(
            (neighborhood) & 
            (spectrogram > self.min_amplitude)
        )
        
        # Convert to list of (time, frequency) tuples
        peak_list = list(zip(peaks[1], peaks[0]))  # Note: reversed for (time, freq)
        
        # Sort by time
        peak_list.sort(key=lambda x: x[0])
        
        return peak_list
    
    def generate_hashes(self, peaks: List[Tuple[int, int]]) -> List[Tuple[str, int]]:
        """
        Generate fingerprint hashes from peak pairs.
        
        For each peak, we pair it with several nearby peaks in the future.
        Each pair creates a hash: (freq1, freq2, time_delta)
        
        Why this works:
        - The combination is unique to the song
        - Time delta makes it time-shift invariant
        - Multiple pairs provide redundancy
        
        Args:
            peaks: List of (time, frequency) peak coordinates
            
        Returns:
            List of (hash_string, time_offset) tuples
        """
        hashes = []
        
        for i, peak1 in enumerate(peaks):
            # For each peak, look at future peaks within target zone
            for j in range(i + self.target_zone_start, 
                          min(i + self.target_zone_width, len(peaks))):
                
                peak2 = peaks[j]
                
                # Create a hash from the two peaks
                time1, freq1 = peak1
                time2, freq2 = peak2
                
                time_delta = time2 - time1
                
                # Hash format: "freq1|freq2|time_delta"
                hash_string = f"{freq1}|{freq2}|{time_delta}"
                
                # Use SHA-1 for consistent hash length
                hash_value = hashlib.sha1(hash_string.encode()).hexdigest()
                
                # Store hash with the absolute time of first peak
                hashes.append((hash_value, time1))
                
                # Limit number of hashes per peak to avoid explosion
                if j - i >= self.fan_value:
                    break
        
        return hashes
    
    def fingerprint_audio(self, audio: np.ndarray) -> List[Tuple[str, int]]:
        """
        Complete fingerprinting pipeline for audio data.
        
        Args:
            audio: Audio time series
            
        Returns:
            List of (hash, time_offset) tuples
        """
        # Step 1: Compute spectrogram
        spectrogram = self.compute_spectrogram(audio)
        
        # Step 2: Find peaks
        peaks = self.find_peaks(spectrogram)
        
        # Step 3: Generate hashes from peaks
        hashes = self.generate_hashes(peaks)
        
        return hashes
    
    def fingerprint_file(self, filepath: str) -> List[Tuple[str, int]]:
        """
        Complete fingerprinting pipeline for audio file.
        
        Args:
            filepath: Path to audio file
            
        Returns:
            List of (hash, time_offset) tuples
        """
        # Load audio
        audio = self.load_audio(filepath)
        
        # Fingerprint it
        return self.fingerprint_audio(audio)
    
    def time_to_frames(self, seconds: float) -> int:
        """Convert time in seconds to frame index."""
        return int(seconds * self.sample_rate / self.hop_length)
    
    def frames_to_time(self, frames: int) -> float:
        """Convert frame index to time in seconds."""
        return frames * self.hop_length / self.sample_rate
