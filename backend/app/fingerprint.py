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
            sample_rate: Audio sample rate in Hz (22050 is good for music)--we capture 22,050 samples per second
            n_fft: FFT window size (larger = better frequency resolution)--we analyze 2048 samples at a time, ~93ms per frame
            hop_length: Number of samples between successive frames--this creates overlapping windows, 512 samples = ~23ms
            freq_min: Minimum frequency to consider (Hz) -- human hearing above 20Hz
            freq_max: Maximum frequency to consider (Hz) -- Music information is mostly below 8kHz
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.freq_min = freq_min
        self.freq_max = freq_max
        
        # Peak finding parameters
        self.peak_neighborhood_size = 10  # When looking for peaks check 10x10 pixel area (smaller = more peaks)
        self.min_amplitude = None  # We'll calculate adaptively
        
        # Fingerprint parameters
        self.fan_value = 5 # Each peak pairs with next 5 peaks (reduced from 30 - was generating too many)
        self.target_zone_width = 75 # Look ahead 75 time frames (reduced from 250)
        self.target_zone_start = 1 # Start pairing from 1 frame ahead (capture nearby peaks)
    
    def load_audio(self, filepath: str, preprocess: bool = False) -> np.ndarray:
        """
        Load audio file and convert to mono at our sample rate.
        Returns audio time series as numpy array.
        
        Args:
            filepath: Path to audio file (mp3, wav, etc.)
            preprocess: If True, apply trim silence and normalization (slower but better matching)
            
        Returns:
            Audio time series as numpy array
        """
        # librosa.load automatically:
        # - Converts to mono
        # - Resamples to target sample rate
        # - Returns float array normalized to [-1, 1]
        audio, _ = librosa.load(filepath, sr=self.sample_rate, mono=True)
        
        if preprocess:
            # Preprocessing steps for better matching (optional, slower)
            # 1. Trim silence from beginning and end
            audio, _ = librosa.effects.trim(audio, top_db=20)
            
            # 2. Normalize audio to consistent volume level
            audio = librosa.util.normalize(audio)
        
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
        # What this does:
        # 1. Takes the audio wave (time-domain)
        # 2. Splits it into overlapping windows of n_fft(2048) samples
        # 3. Applies Fourier Transform to each window
        # 4. Converts time domain -> frequency domain

        # Result Shape:
        # If audio is 66,150 samples (3 seconds at 22,050Hz)
        # Windows: 66,150/512 ≈ 129 frames
        # Frequencies: 2048/2 + 1 = 1025 frequency bins
        # So stft shape = (1025, 129)
        
        # STFT returns complex numbers -> Convert complex numbers to magnitude (amplitude)
        spectrogram = np.abs(stft)
        # Why decibels? -> Human hearing is logarithmic
        # This results in Maximum amplitude of 0 dB and everything else as negative values (-80 dB to 0 dB)
        
        # Convert amplitude to decibels (logarithmic scale)
        # This matches how humans perceive loudness
        spectrogram_db = librosa.amplitude_to_db(spectrogram, ref=np.max)
        
        return spectrogram_db
    
    def find_peaks(self, spectrogram: np.ndarray) -> List[Tuple[int, int]]:
        """
        Find peaks (local maxima) in the spectrogram using adaptive threshold.
        """
        
        # Dilate the structure to increase neighborhood size
        neighborhood_size = self.peak_neighborhood_size
        local_max = maximum_filter(spectrogram, size=neighborhood_size) # For every pixel, look at a 20x20 neighborhood and find the max value
        
        # A pixel is a peak if its value equals the local maximum (meaning it IS the maximum).
        is_peak = (spectrogram == local_max) 
        
        # Remove peaks at the border - edges can create false peaks due to incomplete windows
        is_peak[0] = False
        is_peak[-1] = False
        is_peak[:, 0] = False
        is_peak[:, -1] = False
        
        # Use percentile-based threshold for consistency (top 10% of values - very permissive)
        threshold = np.percentile(spectrogram, 90)
        
        # Get coordinates of peaks above threshold
        peaks = np.where(is_peak & (spectrogram >= threshold))
        
        # Convert to list of (time, frequency) tuples
        peak_list = list(zip(peaks[1], peaks[0]))
        
        # Sort by time
        peak_list.sort(key=lambda x: x[0])
        
        print(f"Debug: Threshold = {threshold:.2f} dB")
        print(f"Debug: Spectrogram range = [{spectrogram.min():.2f}, {spectrogram.max():.2f}] dB")
        print(f"Debug: Found {len(peak_list)} peaks")
        
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
    
    def fingerprint_file(self, filepath: str, preprocess: bool = False) -> List[Tuple[str, int]]:
        """
        Complete fingerprinting pipeline for audio file.
        
        Args:
            filepath: Path to audio file
            preprocess: If True, apply trim silence and normalization (slower but better matching)
            
        Returns:
            List of (hash, time_offset) tuples
        """
        # Load audio (with optional preprocessing)
        audio = self.load_audio(filepath, preprocess=preprocess)
        
        # Fingerprint it
        return self.fingerprint_audio(audio)
    
    def time_to_frames(self, seconds: float) -> int:
        """Convert time in seconds to frame index."""
        return int(seconds * self.sample_rate / self.hop_length)
    
    def frames_to_time(self, frames: int) -> float:
        """Convert frame index to time in seconds."""
        return frames * self.hop_length / self.sample_rate