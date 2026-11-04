// Shared message shapes for the Hawa pipeline.
// Every Kafka message and Redis payload must match one of these types.
// The Python inference service mirrors these shapes, so change both together.

/** What kind of segment is being made. Later days only add cases here. */
export type SegmentKind = 'weather' | 'news' | 'banter';

/** Which on-air voice reads the segment. Later days only add cases here. */
export type Host = 'anchor' | 'nightowl';

/** A raw reading from an outside source, e.g. Open-Meteo. Topic: facts.raw */
export interface FactSnapshot {
  id: string; // unique id of this snapshot
  source: string; // where it came from, e.g. 'open-meteo'
  takenAt: string; // ISO 8601 timestamp of when it was read
  data: Record<string, unknown>; // the raw values, e.g. { temperature_2m: 31 }
}

/** A request to make one segment. Topic: segments.requested */
export interface SegmentRequest {
  id: string; // also the idempotency key and the wav file name
  kind: SegmentKind;
  host: Host;
  facts: FactSnapshot[]; // the only facts the LLM may talk about
  createdAt: string; // ISO 8601
}

/** The written script for a segment. Topic: scripts.ready */
export interface ScriptReady {
  id: string; // same id as the SegmentRequest it answers
  host: Host;
  text: string; // Arabic script, before TTS normalization
  lang: string; // language code, 'ar'
}

/** A finished audio file. Pushed onto the Redis list queue:segments */
export interface SegmentReady {
  id: string; // same id as the request
  path: string; // wav location, e.g. 'segments/<id>.wav' (served under /media)
  durationS: number; // length in seconds (samples / sampling_rate)
  host: Host;
}
