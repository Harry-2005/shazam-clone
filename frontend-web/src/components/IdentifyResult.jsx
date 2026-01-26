import './IdentifyResult.css';

/**
 * IdentifyResult Component
 * Displays the result of song identification
 */
const IdentifyResult = ({ result, onReset }) => {
  if (!result) return null;

  const { matched, song } = result; // Remove confidence fields

  return (
    <div className="identify-result">
      {matched ? (
        <div className="result-success">
          <div className="success-icon">🎵</div>
          <h2>Match Found!</h2>
          
          <div className="song-info">
            <h3>{song.title}</h3>
            <p className="artist">{song.artist}</p>
            {song.album && <p className="album">{song.album}</p>}
          </div>

          <button className="btn btn-primary" onClick={onReset}>
            Identify Another Song
          </button>
        </div>
      ) : (
        <div className="result-no-match">
          <div className="no-match-icon">❌</div>
          <h2>No Match Found</h2>
          <p>
            We couldn't identify this song. This could mean:
          </p>
          <ul>
            <li>The song is not in our database</li>
            <li>The recording quality was too low</li>
            <li>There was too much background noise</li>
          </ul>
          <button className="btn btn-primary" onClick={onReset}>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default IdentifyResult;