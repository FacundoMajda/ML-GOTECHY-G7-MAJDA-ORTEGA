import psycopg2

conn = psycopg2.connect(
    "postgresql://neondb_owner:npg_dFukZtBs5jL4@ep-damp-mouse-acdmtvfy-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)
cur = conn.cursor()

# Step 1: count duplicates
cur.execute("""
    SELECT session_id, roi_id, frame_number, COUNT(*) as dupes
    FROM roi_occupancy_snapshot
    GROUP BY session_id, roi_id, frame_number
    HAVING COUNT(*) > 1
    ORDER BY dupes DESC
    LIMIT 5
""")
dupes = cur.fetchall()
print(f"Top duplicate groups:")
for row in dupes:
    print(f"  {row[0]} / {row[1]} / frame={row[2]} -> {row[3]} duplicates")

# Step 2: dedupe — keep only the row with the lowest id per (session_id, roi_id, frame_number)
cur.execute("""
    DELETE FROM roi_occupancy_snapshot a
    USING roi_occupancy_snapshot b
    WHERE a.id > b.id
      AND a.session_id = b.session_id
      AND a.roi_id = b.roi_id
      AND a.frame_number = b.frame_number
""")
deleted = cur.rowcount
print(f"Deleted {deleted} duplicate rows")
conn.commit()

# Step 3: apply the unique constraint
cur.execute("SELECT 1 FROM pg_constraint WHERE conname = 'uq_snapshot_per_frame'")
if cur.fetchone():
    print("Constraint already exists")
else:
    cur.execute("ALTER TABLE roi_occupancy_snapshot ADD CONSTRAINT uq_snapshot_per_frame UNIQUE (session_id, roi_id, frame_number)")
    conn.commit()
    print("Constraint added successfully")

# Step 4: verify
cur.execute("SELECT COUNT(*) FROM roi_occupancy_snapshot")
print(f"Total snapshots now: {cur.fetchone()[0]}")

cur.close()
conn.close()
