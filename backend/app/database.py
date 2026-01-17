from sqlalchemy import create_engine # Creates connection to PostgreSQL database
from sqlalchemy.orm import sessionmaker, Session # sessionmaker creates sessions to interact with DB
from .models import Base, Song, Fingerprint
from typing import List, Tuple, Dict
import hashlib # For generating SHA-256 file hashes
import os
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
        # Create engine
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Test connections before using -> Prevents errors from stale/closed connections
            echo=False  # Set True to see SQL queries (useful for debugging)
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
            
            # Create fingerprint entries (batch insert for efficiency)
            fingerprint_objects = [
                Fingerprint(
                    hash_value=fp_hash,
                    time_offset=int(time_offset),
                    song_id=song.id
                )
                for fp_hash, time_offset in fingerprints
            ]
            
            # Insert using ORM (ensures defaults like created_at are applied)
            session.add_all(fingerprint_objects) # Batch operation: Insert all fingerprints at once, much faster than single  additions
            
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
            
            # Optimize lookups: query all matching fingerprints in a single DB call
            query_hashes = [q[0] for q in query_fingerprints]
            if not query_hashes:
                return None

            db_fingerprints = session.query(Fingerprint).filter(
                Fingerprint.hash_value.in_(query_hashes)
            ).all()
            
            # Debug: Check if we found any matches
            print(f"Debug: Query fingerprints: {len(query_fingerprints)}")
            print(f"Debug: DB fingerprints found: {len(db_fingerprints)}")

            # Build a map from hash to list of db fingerprints for quick access
            hash_map = {}
            for db_fp in db_fingerprints:
                hash_map.setdefault(db_fp.hash_value, []).append(db_fp)
            """
            hash_map = {
                "a1b2c3d4e5f6...": [
                    Fingerprint(hash="a1b2...", offset=100, song_id=1),
                    Fingerprint(hash="a1b2...", offset=205, song_id=1),  # Same hash, different time
                    Fingerprint(hash="a1b2...", offset=88, song_id=2)    # Different song
                ],
                "f7g8h9i0j1k2...": [
                    Fingerprint(hash="f7g8...", offset=115, song_id=1)
                ],
                ...
            }
            """

            # For each query fingerprint, compute time delta counts
            for query_hash, query_offset in query_fingerprints:
                for db_fp in hash_map.get(query_hash, []):
                    song_id = db_fp.song_id
                    db_offset = db_fp.time_offset
                    time_delta = db_offset - query_offset

                    if song_id not in matches:
                        matches[song_id] = {}

                    matches[song_id][time_delta] = matches[song_id].get(time_delta, 0) + 1
            
            # Debug: Print matches
            print(f"Debug: Matches found: {matches}")
            
            if not matches:
                return None
            
            # Find the best match: song with most consistent time delta
            best_match = None
            best_score = 0
            
            for song_id, time_deltas in matches.items():
                # The most common time delta is the alignment point
                max_count = max(time_deltas.values())
                
                if max_count > best_score:
                    best_score = max_count
                    best_match = song_id
                    
            print(f"Debug: Best match - Song ID: {best_match}, Score: {best_score}")
            
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
                    "total_query_prints": len(query_fingerprints)
                }
                print(f"Debug: Returning result: {result}")
                return result
            return None
            
        finally:
            session.close()
    
    # Other CRUD operations as needed
    
    def get_song(self, song_id: int) -> Song:
        """Get song by ID."""
        session = self.get_session()
        try:
            return session.query(Song).filter(Song.id == song_id).first()
        finally:
            session.close()
    
    def list_songs(self) -> List[Song]:
        """List all songs in database."""
        session = self.get_session()
        try:
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
        """Get statistics about the database."""
        session = self.get_session()
        try:
            song_count = session.query(Song).count()
            fingerprint_count = session.query(Fingerprint).count()
            
            return {
                "total_songs": song_count,
                "total_fingerprints": fingerprint_count,
                "avg_fingerprints_per_song": fingerprint_count / song_count if song_count > 0 else 0
            }
        finally:
            session.close()
    
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
    """
    How it works:

    Opens file in binary mode ("rb")
    Reads 4096 bytes at a time
    Updates hash with each chunk
    Returns 64-character hexadecimal string
    """