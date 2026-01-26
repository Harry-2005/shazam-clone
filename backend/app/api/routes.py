from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
# APIRouter -> Creates a collection of related endpoints
from .schemas import (
    SongResponse, SongListResponse, MatchResult, 
    UploadResponse, DatabaseStats, ErrorResponse
) # Pydantic models for request/response validation
from ..fingerprint import AudioFingerprinter
from ..database import DatabaseManager
import tempfile # Create temporary files for upload
import os
import librosa
from typing import List
import time

# Create router
router = APIRouter()

# Initialize fingerprinter and database
fingerprinter = AudioFingerprinter()
db_manager = DatabaseManager()

"""
API ENDPOINTS

Each endpoint is a function decorated with @router.{method}
- The method (get, post, delete) defines the HTTP verb
- The path defines the URL endpoint
- Response models define what data is returned
"""

# Endpoint 1: Upload a song
@router.post("/songs/upload", response_model=UploadResponse, tags=["Songs"])
async def upload_song(
    file: UploadFile = File(..., description="Audio file (MP3, WAV, etc.)"),
    title: str = Form(..., description="Song title"),
    artist: str = Form(..., description="Artist name"),
    album: str = Form(None, description="Album name (optional)")
):
    """
    Upload a song to the database.
    
    This endpoint:
    1. Receives an audio file
    2. Generates fingerprints
    3. Stores in database
    4. Returns song ID and stats
    
    **File types supported**: MP3, WAV, FLAC, OGG, M4A
    """
    
    try:
        # Validate file type
        allowed_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Get audio duration
            duration = librosa.get_duration(path=tmp_path)
            
            # Generate fingerprints
            fingerprints = fingerprinter.fingerprint_file(tmp_path)
            
            if not fingerprints:
                raise HTTPException(
                    status_code=400,
                    detail="Could not generate fingerprints from audio file"
                )
            
            # Add to database
            song_id = db_manager.add_song(
                title=title,
                artist=artist,
                album=album,
                duration=duration,
                fingerprints=fingerprints,
                filepath=tmp_path
            )
            
            return UploadResponse(
                message="Song uploaded successfully",
                song_id=song_id,
                fingerprints_generated=len(fingerprints)
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path) # Remove temp file
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 2: Identify a song from audio recording
@router.post("/identify", response_model=MatchResult, tags=["Identification"])
async def identify_song(
    file: UploadFile = File(..., description="Audio recording to identify")
):
    """
    Identify a song from an audio recording.
    
    This is the core Shazam functionality:
    1. Receives audio recording (can be short clip)
    2. Generates fingerprints
    3. Matches against database
    4. Returns identified song
    
    **Minimum recording length**: 3-5 seconds recommended
    **Works with**: Background noise, live recordings, phone recordings
    """
    
    try:
        # Save uploaded file temporarily
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            start_time = time.time()
            
            print(f"\n{'='*60}")
            print(f"Identifying song from: {file.filename}")
            print(f"{'='*60}")
            
            # Generate fingerprints from recording with preprocessing for better matching
            # Preprocessing: trim silence and normalize audio
            fingerprint_start = time.time()
            query_fingerprints = fingerprinter.fingerprint_file(tmp_path, preprocess=True)
            fingerprint_time = time.time() - fingerprint_start
            
            print(f"Generated {len(query_fingerprints)} query fingerprints in {fingerprint_time:.2f}s")
            
            if not query_fingerprints:
                raise HTTPException(
                    status_code=400,
                    detail="Could not generate fingerprints from recording"
                )
            
            # Find matches
            match_start = time.time()
            match_result = db_manager.find_matches(query_fingerprints)
            match_time = time.time() - match_start
            
            total_time = time.time() - start_time
            
            print(f"\nTiming Breakdown:")
            print(f"  Fingerprinting: {fingerprint_time:.2f}s")
            print(f"  Database Query: {match_time:.2f}s")
            print(f"  Total Time:     {total_time:.2f}s")
            print(f"\nMatch result: {match_result}")
            print(f"{'='*60}\n")
            
            if match_result and match_result.get('confidence', 0) > 0:
                # Use the corrected confidence percentage from database (already calculated properly)
                # Don't recalculate - it was already done in find_matches()
                
                 # Get full song details from database to ensure accuracy
                song = db_manager.get_song(match_result['song_id'])
                
                if not song:
                    print(f"ERROR: Song {match_result['song_id']} not found!")
                    return MatchResult(
                        matched=False,
                        song=None,
                        confidence=0,
                        confidence_percentage=0.0
                    )
                
                
                return MatchResult(
                    matched=True,
                    song=SongResponse(
                        id=song.id,
                        title=song.title,
                        artist=song.artist,
                        album=song.album,
                        duration= song.duration  
                    ),
                    confidence=match_result['confidence'],
                    confidence_percentage=match_result.get('confidence_percentage', 0.0)
                )
            else:
                return MatchResult(
                    matched=False,
                    song=None,
                    confidence=0,
                    confidence_percentage=0.0
                )
        
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    except Exception as e:
        print(f"ERROR in identify_song: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint 3: List all songs in database
@router.get("/songs", response_model=SongListResponse, tags=["Songs"])
async def list_songs():
    """
    List all songs in the database.
    
    Returns list of songs with their metadata.
    """
    
    try:
        songs = db_manager.list_songs()
        
        return SongListResponse(
            songs=[SongResponse.from_orm(song) for song in songs],
            # SongResponse.from_orm -> Convert SQLAlchemy Song object to Pydantic model
            total=len(songs)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 4: Get details of a specific song
@router.get("/songs/{song_id}", response_model=SongResponse, tags=["Songs"])
async def get_song(song_id: int):
    """
    Get details of a specific song.
    
    Args:
        song_id: Unique song identifier
    """
    
    try:
        song = db_manager.get_song(song_id)
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        return SongResponse.from_orm(song)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 5: Delete a song
@router.delete("/songs/{song_id}", tags=["Songs"])
async def delete_song(song_id: int):
    """
    Delete a song from the database.
    
    This removes the song and all its fingerprints.
    
    Args:
        song_id: Unique song identifier
    """
    
    try:
        db_manager.delete_song(song_id)
        return {"message": "Song deleted successfully", "song_id": song_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 6: Get database statistics
@router.get("/stats", response_model=DatabaseStats, tags=["System"])
async def get_stats():
    """
    Get database statistics.
    
    Returns information about:
    - Total songs in database
    - Total fingerprints stored
    - Average fingerprints per song
    """
    
    try:
        stats = db_manager.get_database_stats()
        return DatabaseStats(**stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 7: Health check
@router.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Used to verify the API is running.
    """
    return {"status": "healthy", "message": "Shazam Clone API is running"}