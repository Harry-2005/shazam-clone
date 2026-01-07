from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()
# Acts as a parent of all our database tables. 

class Song(Base):
    """
    Represents a song in our database.
    
    Each song has metadata and many associated fingerprints.
    """
    __tablename__ = "songs" # name in postgres
    
    id = Column(Integer, primary_key=True, index=True)
    # primary_key=True -> unique identifier for each song -- no 2 songs can have the same ID, automatically auto-incremented
    # index=True -> creates an index on this column for faster lookups
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True) # optional field
    duration = Column(Float, nullable=True)  # Duration in seconds
    file_hash = Column(String(64), unique=True, nullable=False)  # To avoid duplicates
    
    # Relationship: one song has many fingerprints
    fingerprints = relationship("Fingerprint", back_populates="song", 
                               cascade="all, delete-orphan")
    # This defines one-to-many relationship. One ong has many fingerprints.
    # relationship("Fingerprint",...) tells SQLAlchemy that this is related to the Fingerprint class. Allows us to access song.fingerprints to get all fingerprints for a song.
    # back_populates="song" creates a bidirectional relationship, allowing us to access fingerprint.song to get the parent song of a fingerprint.
    # cascade="all, delete-orphan" -> "all" means that any operation (like delete) on a Song will cascade to its Fingerprints. "delete-orphan" means that if a Fingerprint is no longer associated with any Song, it will be deleted from the database.
    
    # String representation 
    def __repr__(self):
        return f"<Song(id={self.id}, title='{self.title}', artist='{self.artist}')>"


class Fingerprint(Base):
    """
    Represents a single fingerprint hash from a song.
    
    The fingerprint table is the heart of the system:
    - hash: The fingerprint hash value
    - time_offset: When this hash occurs in the song
    - song_id: Which song this belongs to
    """
    __tablename__ = "fingerprints"
    
    id = Column(Integer, primary_key=True, index=True)
    hash_value = Column(String(64), nullable=False, index=True)  # The fingerprint hash
    time_offset = Column(Integer, nullable=False)  # Time offset in frames
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationship: many fingerprints belong to one song
    song = relationship("Song", back_populates="fingerprints")
    
    # Composite indexes for fast lookups
    __table_args__ = (
        Index('idx_hash_song', 'hash_value', 'song_id'),
        Index('idx_hash', 'hash_value'),
    )

    def __repr__(self):
        hv = (self.hash_value[:8] + '...') if self.hash_value else 'None'
        return f"<Fingerprint(hash='{hv}', offset={self.time_offset}, song_id={self.song_id})>"
    
    """
    Here's what the actual database tables look like:

    ### songs table

    +----+-------------------+-------------+------------------+----------+------------------+
    | id | title             | artist      | album            | duration | file_hash        |
    +----+-------------------+-------------+------------------+----------+------------------+
    | 1  | Bohemian Rhapsody | Queen       | A Night at Opera | 354.5    | a3f5d8c2b1e4f... |
    | 2  | Imagine           | John Lennon | Imagine          | 183.2    | f6a7c8d9e0f1a... |
    +----+-------------------+-------------+------------------+----------+------------------+


    ### fingerprints table

    +----+------------------------------------------+-------------+---------+-------------------------+
    | id | hash_value                               | time_offset | song_id | created_at              |
    +----+------------------------------------------+-------------+---------+-------------------------+
    | 1  | a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0 | 10          | 1       | 2024-01-15 14:23:45.123 |
    | 2  | f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7 | 25          | 1       | 2024-01-15 14:23:45.145 |
    | 3  | b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2 | 42          | 1       | 2024-01-15 14:23:45.167 |
    | 4  | x8y9z0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8 | 15          | 2       | 2024-01-15 14:25:12.456 |
    +----+------------------------------------------+-------------+---------+-------------------------+
    
    **Why not store everything in one table?**

     **Bad design (one table):**

    fingerprints table:
    hash_value | time_offset | title             | artist | album | duration
    abc123...  | 10          | Bohemian Rhapsody | Queen  | ...   | 354.5
    def456...  | 25          | Bohemian Rhapsody | Queen  | ...   | 354.5  ← Duplicate data!
    

    **Good design (two tables):**
    
    songs: Store metadata once
    fingerprints: Just reference song_id
    """