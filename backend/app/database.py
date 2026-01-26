import datetime
from sqlalchemy import create_engine # Creates connection to PostgreSQL database
from sqlalchemy.orm import sessionmaker, Session, joinedload # sessionmaker creates sessions to interact with DB
from .models import Base, Song, Fingerprint
from typing import List, Tuple, Dict
import hashlib # For generating SHA-256 file hashes
import os
import time  # For timing operations
from dotenv import load_dotenv # To load environment variables like DATABASE_URL

load_dotenv()

class DatabaseManager:
    """
    Manages all database operations for the fingerprint system.
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection string
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")
        
        """
        What is an engine?
        - The power source that connects to PostgreSQL
        - Manages connection pool, handles communication
        - Handles low-level database communication
        """
        # Create engine with optimized connection pooling
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Test connections before using -> Prevents errors from stale/closed connections
            echo=False,  # Set True to see SQL queries (useful for debugging)
            pool_size=5,  # 5 persistent connections (one per concurrent user)
            max_overflow=10,  # Allow 10 more during traffic spikes (15 total max)
            pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections)
            pool_timeout=30  # Wait up to 30s for available connection
        )
        
        """
        What is a session?
        - A workspace for all DB operations
        - Tracks changes and commits them as a transaction
        - It's like openening a connection to the database
        - Multiple sessions can exist at once for concurrent operations
        """
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, # Changes aren't saved until we call session.commit()
            autoflush=False, # Don't automatically sync Python objects to DB until we call session.flush() or commit()
            bind=self.engine # Binds sessions to our engine
        )
        
        """
        Checks if songs and fingerprints tables exist; creates them based on models if not.
        If they exist it does nothing.
        Idempotent: Safe to call multiple times.
        """
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection and dispose of engine."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
    
    def add_song(self, title: str, artist: str, 
                 fingerprints: List[Tuple[str, int]],
                 album: str = None, duration: float = None,
                 filepath: str = None) -> int:
        """
        Add a song and its fingerprints to the database.
        
        Args:
            title: Song title
            artist: Artist name
            fingerprints: List of (hash, time_offset) tuples
            album: Album name (optional)
            duration: Song duration in seconds (optional)
            filepath: Path to audio file (to generate file hash)
            
        Returns:
            song_id of the inserted song
        """
        session = self.get_session()
        
        try:
            # Generate file hash to prevent duplicates
            file_hash = self._generate_file_hash(filepath) if filepath else None
            
            # Check if song already exists
            if file_hash:
                existing_song = session.query(Song).filter(
                    Song.file_hash == file_hash
                ).first()
                if existing_song:
                    print(f"Song already exists: {existing_song.title}")
                    return existing_song.id
            
            # Create song entry
            song = Song(
                title=title,
                artist=artist,
                album=album,
                duration=duration,
                file_hash=file_hash
            ) # Python object, not in database yet
            session.add(song) # Still not in databse, just staged for commit
            session.flush()  # Get the song ID without committing, Sends SQL INSERT to database
            """
            Why flush instead of commit?
            - We need the song ID to link fingerprints
            - Commit would finalize the transaction, we want to add fingerprints next
            - Flush sends the INSERT to DB but keeps transaction open
            - After adding fingerprints we will commit everything together
            """
            
            # Create fingerprint entries using bulk insert for maximum efficiency
            # Use bulk_insert_mappings for raw SQL INSERT - much faster than ORM
            fingerprint_dicts = [
                {
                    'hash_value': fp_hash,
                    'time_offset': int(time_offset),
                    'song_id': song.id
                }
                for fp_hash, time_offset in fingerprints
            ]
            
            # Bulk insert: Direct SQL INSERT, bypasses ORM overhead
            # For 30k+ fingerprints, this is 10-50x faster than add_all()
            session.bulk_insert_mappings(Fingerprint, fingerprint_dicts)
            
            session.commit() # Saves everthing to the database, If anything fails before this, nothing is saved (Rollback)
            
            print(f"✓ Added song: {title} by {artist}")
            print(f"  Fingerprints stored: {len(fingerprints)}")
            
            return song.id
            
        except Exception as e:
            session.rollback()
            print(f"✗ Error adding song: {e}")
            raise
        finally:
            session.close()
    
    def find_matches(self, query_fingerprints: List[Tuple[str, int]]) -> Dict:
        """
        Find matching songs for a set of query fingerprints.
        
        This is the core matching algorithm:
        1. Look up each query hash in the database
        2. For each match, calculate time difference
        3. Group matches by song
        4. Count matches with consistent time differences
        5. Return song with most consistent matches
        
        Args:
            query_fingerprints: List of (hash, time_offset) tuples from recorded audio
            
        Returns:
            Dictionary with match results or None
        """
        session = self.get_session()
        
        try:
            # Dynamic thresholds based on recording length
            # With 1000 sampled fingerprints, adjust expectations
            # False positives: 1-15, True matches: 50-100+
            EXPECTED_GOOD_MATCH = 100  # Baseline for true match with 1000 samples
            MIN_MATCH_PERCENTAGE = 0.05  # Lower threshold to 5%
            MIN_MATCHING_FINGERPRINTS = int(EXPECTED_GOOD_MATCH * MIN_MATCH_PERCENTAGE)  # 5 matches minimum
            MIN_CONFIDENCE_PERCENTAGE = MIN_MATCH_PERCENTAGE * 100  # 5%
            print(f"Debug: Thresholds - Min fingerprints: {MIN_MATCHING_FINGERPRINTS}, Min confidence: {MIN_CONFIDENCE_PERCENTAGE}%")
            
            # Dictionary to store matches: {song_id: {time_delta: count}}
            matches = {}
            """
            matches = {
                1: {10: 156, 12: 3, 8: 2},  # Song 1: 156 hashes match with delta=10
                2: {5: 12, 7: 8},           # Song 2: 12 hashes match with delta=5
                3: {15: 3}                  # Song 3: 3 hashes match with delta=15
            }
            What is time_delta?
            - The **time difference** between recorded offset and database offset
            - Shows how the recording aligns with the original song

            **Example:**
            ```
            Original song:  |--Hash at frame 100--|
            Your recording: |--Same hash at frame 90--|

            time_delta = 100 - 90 = 10

            Means: Your recording started 10 frames after the song's beginning
            """
            
            # Optimize lookups: batch query to avoid huge IN clause
            # Use strategic sampling: take fingerprints from different parts of recording
            MAX_QUERY_FINGERPRINTS = 400  # ~9 seconds of audio - optimized for speed
            BATCH_SIZE = 100  # Process in batches for early exit
            
            # Strategic sampling: every Nth fingerprint for better coverage
            if len(query_fingerprints) > MAX_QUERY_FINGERPRINTS:
                step = len(query_fingerprints) // MAX_QUERY_FINGERPRINTS
                sampled_fingerprints = query_fingerprints[::step][:MAX_QUERY_FINGERPRINTS]
            else:
                sampled_fingerprints = query_fingerprints
            
            # OPTIMIZATION: Process in batches with early exit
            matches = {}
            batches_processed = 0
            
            for batch_start in range(0, len(sampled_fingerprints), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(sampled_fingerprints))
                batch_fingerprints = sampled_fingerprints[batch_start:batch_end]
                
                # Extract query hashes for this batch
                query_hashes = [q[0] for q in batch_fingerprints]
                if not query_hashes:
                    continue

                print(f"Debug: Querying batch {batches_processed + 1} ({len(query_hashes)} fingerprints)...")
                
                query_start = time.time()
                
                # Single efficient query using indexed IN clause
                db_fingerprints_raw = session.query(
                    Fingerprint.hash_value,
                    Fingerprint.time_offset,
                    Fingerprint.song_id
                ).filter(
                    Fingerprint.hash_value.in_(query_hashes)
                ).all()
                
                query_time = time.time() - query_start
                print(f"Debug: Batch SQL query took {query_time:.2f}s, found {len(db_fingerprints_raw)} matches")
                
                # Build hash map for this batch
                hash_map = {}
                for row in db_fingerprints_raw:
                    hash_val, time_offset, song_id = row
                    if hash_val not in hash_map:
                        hash_map[hash_val] = []
                    hash_map[hash_val].append((time_offset, song_id))
                
                # Process matches for this batch
                for query_hash, query_offset in batch_fingerprints:
                    for db_offset, song_id in hash_map.get(query_hash, []):
                        time_delta = db_offset - query_offset

                        if song_id not in matches:
                            matches[song_id] = {}

                        matches[song_id][time_delta] = matches[song_id].get(time_delta, 0) + 1
                
                batches_processed += 1
                
                # EARLY EXIT: Check if we have a strong match after this batch
                if matches:
                    best_score = max(max(deltas.values()) for deltas in matches.values())
                    if best_score > 80:  # Strong confidence after processing batch
                        print(f"Debug: Early exit after batch {batches_processed} - strong match found ({best_score} fingerprints)")
                        break
            
            # Debug: Print matches
            print(f"Debug: Matches found: {len(matches)} potential songs")
            
            if not matches:
                return None
            
            # Find the best match: song with most consistent time delta
            best_match = None
            best_score = 0
            best_alignment = None
            
            for song_id, time_deltas in matches.items():
                # The most common time delta is the alignment point
                max_count = max(time_deltas.values())
                alignment = max(time_deltas, key=time_deltas.get)
                
                if max_count > best_score:
                    best_score = max_count
                    best_match = song_id
                    best_alignment = alignment
            
            # Calculate confidence percentage
            # Show as percentage of a good match baseline (100 fingerprints)
            confidence_pct = min(100, (best_score / 100) * 100)
            print(f"Debug: Best match - Song ID: {best_match}")
            print(f"Debug: Confidence: {best_score} matching hashes")
            print(f"Debug: Confidence Percentage: {confidence_pct:.2f}%")
            
            # CRITICAL: Apply minimum thresholds
            if best_score < MIN_MATCHING_FINGERPRINTS:
                print(f"Debug: REJECTED - Too few matching fingerprints ({best_score} < {MIN_MATCHING_FINGERPRINTS})")
                return None
            
            if confidence_pct < MIN_CONFIDENCE_PERCENTAGE:
                print(f"Debug: REJECTED - Confidence too low ({confidence_pct:.2f}% < {MIN_CONFIDENCE_PERCENTAGE}%)")
                return None
            
            # Get song details (only if we found a valid match with score > 0)
            if best_match and best_score > 0:
                song = session.query(Song).filter(Song.id == best_match).first()
                
                if not song:
                    print(f"Debug: ERROR - Song {best_match} not found in database!")
                    return None
                
                result = {
                    "song_id": song.id,
                    "title": song.title,
                    "artist": song.artist,
                    "album": song.album,
                    "confidence": best_score,  # Number of matching fingerprints
                    "total_query_prints": len(query_fingerprints),
                    "alignment_offset": best_alignment,
                    "confidence_percentage": confidence_pct  # Include corrected percentage
                }
                
                print(f"Debug: ✅ MATCH ACCEPTED - {song.title} by {song.artist}")
                
                return result
            return None
            
        finally:
            session.close()
    
    # Other CRUD operations as needed
    
    def get_song(self, song_id: int) -> Song:
        """Get song by ID."""
        session = self.get_session()
        try:
            # Don't load fingerprints unless needed - dramatically improves performance
            return session.query(Song).filter(Song.id == song_id).first()
        finally:
            session.close()
    
    def list_songs(self) -> List[Song]:
        """List all songs in database."""
        session = self.get_session()
        try:
            # Don't load fingerprints - they're not needed for listing
            # Loading fingerprints for songs with 30k+ prints each is extremely slow
            return session.query(Song).all()
        finally:
            session.close()
    
    def delete_song(self, song_id: int):
        """Delete a song and all its fingerprints."""
        session = self.get_session()
        try:
            song = session.query(Song).filter(Song.id == song_id).first()
            if song:
                session.delete(song)
                session.commit()
                print(f"✓ Deleted song: {song.title}")
                # Important: cascade="all, delete-orphan" in models.py ensures fingerprints are automatically deleted!
            else:
                print(f"✗ Song with ID {song_id} not found")
        except Exception as e:
            session.rollback()
            print(f"✗ Error deleting song: {e}")
            raise
        finally:
            session.close()
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database with 5-minute caching."""
        # Check cache first
        if self._stats_cache and self._stats_cache_time:
            time_since_cache = datetime.now() - self._stats_cache_time
            if time_since_cache < self._cache_duration:
                return self._stats_cache
        
        # Cache miss or expired, query database
        session = self.get_session()
        try:
            song_count = session.query(Song).count()
            fingerprint_count = session.query(Fingerprint).count()
            
            stats = {
                "total_songs": song_count,
                "total_fingerprints": fingerprint_count,
                "avg_fingerprints_per_song": fingerprint_count / song_count if song_count > 0 else 0
            }
            
            # Update cache
            self._stats_cache = stats
            self._stats_cache_time = datetime.now()
            
            return stats
        finally:
            session.close()
    
    def _invalidate_stats_cache(self):
        """Invalidate the stats cache when database changes."""
        self._stats_cache = None
        self._stats_cache_time = None
    
    def _generate_file_hash(self, filepath: str) -> str:
        """Generate SHA-256 hash of file to detect duplicates."""
        if not filepath or not os.path.exists(filepath):
            return None
        
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()