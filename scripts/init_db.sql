-- ============================================================
-- SCHEMA: Video Analytics Platform
-- DB: PostgreSQL (Neon serverless)
-- ============================================================

-- EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()

-- ============================================================
-- 1. VIDEO SOURCES
--    Una cámara / fuente de video configurada en el sistema
-- ============================================================
CREATE TABLE video_source (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT        NOT NULL,
    description     TEXT,
    source_type     TEXT        NOT NULL CHECK (source_type IN ('file', 'youtube_vod', 'youtube_live', 'rtsp')),
    source_uri      TEXT        NOT NULL,  -- path local, URL de YouTube, rtsp://...
    is_live         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. ROI (Region of Interest)
--    Una zona poligonal definida sobre una fuente de video.
--    Una fuente puede tener múltiples ROIs.
-- ============================================================
CREATE TABLE roi (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    video_source_id UUID        NOT NULL REFERENCES video_source(id) ON DELETE CASCADE,
    name            TEXT        NOT NULL,   -- "Entrada", "Zona restringida"
    polygon         JSONB       NOT NULL,   -- [[x1,y1],[x2,y2],...]
    positive_label  TEXT        NOT NULL DEFAULT 'inside',
    negative_label  TEXT        NOT NULL DEFAULT 'outside',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 3. ROI EVENT RULES
--    Qué eventos se quieren capturar para cada ROI.
-- ============================================================
CREATE TABLE roi_event_rule (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    roi_id          UUID        NOT NULL REFERENCES roi(id) ON DELETE CASCADE,
    event_type      TEXT        NOT NULL CHECK (event_type IN (
                                    'entry',            -- alguien ingresa al ROI
                                    'exit',             -- alguien sale del ROI
                                    'overcapacity',     -- personas_dentro > threshold
                                    'dwell_exceeded'    -- permanencia > threshold_seconds
                                )),
    threshold       INTEGER,    -- para overcapacity: max personas; para dwell: segundos
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 4. DETECTION SESSION
--    Una ejecución del pipeline sobre una fuente de video.
-- ============================================================
CREATE TABLE detection_session (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    video_source_id UUID        NOT NULL REFERENCES video_source(id),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,                        -- NULL si sigue activa
    timestamp_mode  TEXT        NOT NULL CHECK (timestamp_mode IN ('frame_based', 'realtime')),
    fps             NUMERIC(6,3),                       -- para frame_based: calcular tiempos
    total_frames    INTEGER,                            -- NULL si live
    write_video     BOOLEAN     NOT NULL DEFAULT FALSE,
    output_video_path TEXT,
    extra_analysis  JSONB,                              -- { requested: bool, target: str, result: str }
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 5. TRACKED ENTITY
--    Una persona/objeto trackeado dentro de una sesión.
-- ============================================================
CREATE TABLE tracked_entity (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID        NOT NULL REFERENCES detection_session(id) ON DELETE CASCADE,
    track_id            INTEGER     NOT NULL,   -- ID asignado por ByteTrack
    first_seen_at       TIMESTAMPTZ NOT NULL,
    last_seen_at        TIMESTAMPTZ NOT NULL,
    first_seen_frame    INTEGER,                -- NULL si realtime
    last_seen_frame     INTEGER,
    UNIQUE (session_id, track_id)
);

-- ============================================================
-- 6. ROI OCCUPANCY SNAPSHOT
--    Estado del ROI por frame/instante durante la sesión.
--    Permite reconstruir la ocupación a lo largo del tiempo.
-- ============================================================
CREATE TABLE roi_occupancy_snapshot (
    id              BIGSERIAL   PRIMARY KEY,
    session_id      UUID        NOT NULL REFERENCES detection_session(id) ON DELETE CASCADE,
    roi_id          UUID        NOT NULL REFERENCES roi(id),
    captured_at     TIMESTAMPTZ NOT NULL,
    frame_number    INTEGER,
    count_inside    INTEGER     NOT NULL DEFAULT 0,
    count_outside   INTEGER     NOT NULL DEFAULT 0,
    track_ids_inside INTEGER[]  NOT NULL DEFAULT '{}'
);

-- ============================================================
-- 7. ZONE EVENT
--    Cada evento puntual capturado durante la sesión.
-- ============================================================
CREATE TABLE zone_event (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID        NOT NULL REFERENCES detection_session(id) ON DELETE CASCADE,
    roi_id          UUID        NOT NULL REFERENCES roi(id),
    track_id        INTEGER,                    -- NULL para overcapacity
    event_type      TEXT        NOT NULL CHECK (event_type IN (
                                    'entry', 'exit', 'overcapacity', 'dwell_exceeded'
                                )),
    occurred_at     TIMESTAMPTZ NOT NULL,
    frame_number    INTEGER,
    dwell_seconds   NUMERIC(10,2),              -- solo para dwell_exceeded
    metadata        JSONB                       -- datos extra según tipo de evento
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_roi_source           ON roi(video_source_id);
CREATE INDEX idx_roi_rule_roi         ON roi_event_rule(roi_id);
CREATE INDEX idx_session_source       ON detection_session(video_source_id);
CREATE INDEX idx_session_started      ON detection_session(started_at DESC);
CREATE INDEX idx_tracked_session      ON tracked_entity(session_id);
CREATE INDEX idx_snapshot_session     ON roi_occupancy_snapshot(session_id, captured_at DESC);
CREATE INDEX idx_zone_event_session   ON zone_event(session_id, occurred_at DESC);
CREATE INDEX idx_zone_event_type      ON zone_event(event_type);
CREATE INDEX idx_zone_event_roi       ON zone_event(roi_id, occurred_at DESC);
