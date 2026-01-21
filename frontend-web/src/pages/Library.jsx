import SongList from '../components/SongList';
import './Library.css';

const Library = () => {
  return (
    <div className="library-page">
      <div className="page-header">
        <h1>📚 Song Library</h1>
        <p>Browse all songs in the database</p>
      </div>

      <SongList />
    </div>
  );
};

export default Library;