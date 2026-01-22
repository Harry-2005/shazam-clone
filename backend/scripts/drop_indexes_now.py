from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:changeme@localhost:5432/shazam_clone')

with engine.connect() as conn:
    conn.execute(text("COMMIT"))
    conn.execute(text("DROP INDEX IF EXISTS ix_fingerprints_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_fingerprints_hash_value"))
    conn.execute(text("DROP INDEX IF EXISTS idx_hash"))
    conn.execute(text("DROP INDEX IF EXISTS idx_hash_song"))
    conn.commit()
    
    result = conn.execute(text("SELECT indexname FROM pg_indexes WHERE tablename='fingerprints'"))
    remaining = [row[0] for row in result]
    print(f"Remaining indexes: {remaining}")

engine.dispose()
print("DONE!")
