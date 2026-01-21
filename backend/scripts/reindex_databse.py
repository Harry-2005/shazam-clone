import sys
import os
import argparse
from pathlib import Path

sys.path.append('..')

from app.fingerprint import AudioFingerprinter
from app.database import DatabaseManager
from app.models import Base


def parse_title_artist(filename: str):
	base = Path(filename).stem
	if ' - ' in base:
		first, second = base.split(' - ', 1)
		title, artist = first.strip(), second.strip()
	else:
		title, artist = base.strip(), "Unknown"
	return title or "Unknown", artist or "Unknown"


def build_fingerprinter(args) -> AudioFingerprinter:
	return AudioFingerprinter(
		sample_rate=args.sample_rate,
		n_fft=args.n_fft,
		hop_length=args.hop_length,
		freq_min=args.freq_min,
		freq_max=args.freq_max,
	)


def iter_audio_files(audio_dir: Path):
	exts = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}
	for path in sorted(audio_dir.rglob("*")):
		if path.suffix.lower() in exts:
			yield path


def reindex_database(args):
	db = DatabaseManager(database_url=args.database_url)
	audio_dir = Path(args.audio_dir).resolve()

	if not audio_dir.exists():
		raise SystemExit(f"Audio directory not found: {audio_dir}")

	print("This will DROP and recreate all tables, then fingerprint and upload every audio file found.")
	print(f"Database URL: {os.getenv('DATABASE_URL')}")
	print(f"Audio directory: {audio_dir}")
	if not args.force:
		confirm = input("Type 'yes' to continue: ")
		if confirm.lower() != "yes":
			print("Cancelled.")
			return

	# Drop and recreate schema
	Base.metadata.drop_all(bind=db.engine)
	Base.metadata.create_all(bind=db.engine)
	print("✓ Database schema recreated")

	fp = build_fingerprinter(args)

	audio_files = list(iter_audio_files(audio_dir))
	if not audio_files:
		print("No audio files found to ingest.")
		return

	print(f"Found {len(audio_files)} audio files. Fingerprinting...")
	for idx, audio_path in enumerate(audio_files, 1):
		print(f"[{idx}/{len(audio_files)}] {audio_path.name}")
		try:
			hashes = fp.fingerprint_file(str(audio_path))
			title, artist = parse_title_artist(audio_path.name)
			song_id = db.add_song(
				title=title,
				artist=artist,
				album=None,
				duration=None,
				fingerprints=hashes,
				filepath=str(audio_path),
			)
			print(f"  ✓ Added as song ID {song_id} ({len(hashes)} fingerprints)")
		except Exception as exc:
			print(f"  ✗ Failed: {exc}")

	print("Reindexing complete.")


def main():
	default_audio_dir = Path(__file__).resolve().parents[2] / "sample-songs"

	parser = argparse.ArgumentParser(description="Drop DB and re-fingerprint all audio files.")
	parser.add_argument("--audio-dir", default=default_audio_dir, help="Directory containing audio files to ingest")
	parser.add_argument("--database-url", default=None, help="Override DATABASE_URL")
	parser.add_argument("--sample-rate", type=int, default=22050, help="Fingerprint sample rate")
	parser.add_argument("--n-fft", type=int, default=2048, help="FFT window size")
	parser.add_argument("--hop-length", type=int, default=512, help="STFT hop length")
	parser.add_argument("--freq-min", type=int, default=20, help="Min frequency considered")
	parser.add_argument("--freq-max", type=int, default=8000, help="Max frequency considered")
	parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")

	args = parser.parse_args()
	reindex_database(args)


if __name__ == "__main__":
	main()
