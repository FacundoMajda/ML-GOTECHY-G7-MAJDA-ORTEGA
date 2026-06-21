CREATE SCHEMA "public";
CREATE TABLE "detection_session" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"video_source_id" uuid NOT NULL,
	"started_at" timestamp with time zone DEFAULT now() NOT NULL,
	"ended_at" timestamp with time zone,
	"timestamp_mode" text NOT NULL,
	"fps" numeric(6, 3),
	"total_frames" integer,
	"write_video" boolean DEFAULT false NOT NULL,
	"output_video_path" text,
	"extra_analysis" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "detection_session_timestamp_mode_check" CHECK ((timestamp_mode = ANY (ARRAY['frame_based'::text, 'realtime'::text])))
);
CREATE TABLE "roi" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"video_source_id" uuid NOT NULL,
	"name" text NOT NULL,
	"polygon" jsonb NOT NULL,
	"positive_label" text DEFAULT 'inside' NOT NULL,
	"negative_label" text DEFAULT 'outside' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "roi_event_rule" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"roi_id" uuid NOT NULL,
	"event_type" text NOT NULL,
	"threshold" integer,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "roi_event_rule_event_type_check" CHECK ((event_type = ANY (ARRAY['entry'::text, 'exit'::text, 'overcapacity'::text, 'dwell_exceeded'::text])))
);
CREATE TABLE "roi_occupancy_snapshot" (
	"id" bigserial PRIMARY KEY,
	"session_id" uuid NOT NULL,
	"roi_id" uuid NOT NULL,
	"captured_at" timestamp with time zone NOT NULL,
	"frame_number" integer,
	"count_inside" integer DEFAULT 0 NOT NULL,
	"count_outside" integer DEFAULT 0 NOT NULL,
	"track_ids_inside" integer[] DEFAULT '{}' NOT NULL
);
CREATE TABLE "tracked_entity" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"session_id" uuid NOT NULL UNIQUE,
	"track_id" integer NOT NULL UNIQUE,
	"first_seen_at" timestamp with time zone NOT NULL,
	"last_seen_at" timestamp with time zone NOT NULL,
	"first_seen_frame" integer,
	"last_seen_frame" integer,
	CONSTRAINT "tracked_entity_session_id_track_id_key" UNIQUE("session_id","track_id")
);
CREATE TABLE "video_source" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"name" text NOT NULL,
	"description" text,
	"source_type" text NOT NULL,
	"source_uri" text NOT NULL,
	"is_live" boolean DEFAULT false NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "video_source_source_type_check" CHECK ((source_type = ANY (ARRAY['file'::text, 'youtube_vod'::text, 'youtube_live'::text, 'rtsp'::text])))
);
CREATE TABLE "zone_event" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"session_id" uuid NOT NULL,
	"roi_id" uuid NOT NULL,
	"track_id" integer,
	"event_type" text NOT NULL,
	"occurred_at" timestamp with time zone NOT NULL,
	"frame_number" integer,
	"dwell_seconds" numeric(10, 2),
	"metadata" jsonb,
	CONSTRAINT "zone_event_event_type_check" CHECK ((event_type = ANY (ARRAY['entry'::text, 'exit'::text, 'overcapacity'::text, 'dwell_exceeded'::text])))
);
CREATE UNIQUE INDEX "detection_session_pkey" ON "detection_session" ("id");
CREATE INDEX "idx_session_source" ON "detection_session" ("video_source_id");
CREATE INDEX "idx_session_started" ON "detection_session" ("started_at");
CREATE INDEX "idx_roi_source" ON "roi" ("video_source_id");
CREATE UNIQUE INDEX "roi_pkey" ON "roi" ("id");
CREATE INDEX "idx_roi_rule_roi" ON "roi_event_rule" ("roi_id");
CREATE UNIQUE INDEX "roi_event_rule_pkey" ON "roi_event_rule" ("id");
CREATE INDEX "idx_snapshot_session" ON "roi_occupancy_snapshot" ("session_id","captured_at");
CREATE UNIQUE INDEX "roi_occupancy_snapshot_pkey" ON "roi_occupancy_snapshot" ("id");
CREATE INDEX "idx_tracked_session" ON "tracked_entity" ("session_id");
CREATE UNIQUE INDEX "tracked_entity_pkey" ON "tracked_entity" ("id");
CREATE UNIQUE INDEX "tracked_entity_session_id_track_id_key" ON "tracked_entity" ("session_id","track_id");
CREATE UNIQUE INDEX "video_source_pkey" ON "video_source" ("id");
CREATE INDEX "idx_zone_event_roi" ON "zone_event" ("roi_id","occurred_at");
CREATE INDEX "idx_zone_event_session" ON "zone_event" ("session_id","occurred_at");
CREATE INDEX "idx_zone_event_type" ON "zone_event" ("event_type");
CREATE UNIQUE INDEX "zone_event_pkey" ON "zone_event" ("id");
ALTER TABLE "detection_session" ADD CONSTRAINT "detection_session_video_source_id_fkey" FOREIGN KEY ("video_source_id") REFERENCES "video_source"("id");
ALTER TABLE "roi" ADD CONSTRAINT "roi_video_source_id_fkey" FOREIGN KEY ("video_source_id") REFERENCES "video_source"("id") ON DELETE CASCADE;
ALTER TABLE "roi_event_rule" ADD CONSTRAINT "roi_event_rule_roi_id_fkey" FOREIGN KEY ("roi_id") REFERENCES "roi"("id") ON DELETE CASCADE;
ALTER TABLE "roi_occupancy_snapshot" ADD CONSTRAINT "roi_occupancy_snapshot_roi_id_fkey" FOREIGN KEY ("roi_id") REFERENCES "roi"("id");
ALTER TABLE "roi_occupancy_snapshot" ADD CONSTRAINT "roi_occupancy_snapshot_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "detection_session"("id") ON DELETE CASCADE;
ALTER TABLE "tracked_entity" ADD CONSTRAINT "tracked_entity_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "detection_session"("id") ON DELETE CASCADE;
ALTER TABLE "zone_event" ADD CONSTRAINT "zone_event_roi_id_fkey" FOREIGN KEY ("roi_id") REFERENCES "roi"("id");
ALTER TABLE "zone_event" ADD CONSTRAINT "zone_event_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "detection_session"("id") ON DELETE CASCADE;