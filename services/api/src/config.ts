import { resolve } from 'node:path';

// Host processes talk to Redpanda on localhost:9092 (the OUTSIDE listener in docker-compose).
export const KAFKA_BROKERS = (process.env.KAFKA_BROKERS ?? 'localhost:9092').split(',');
export const REDIS_URL = process.env.REDIS_URL ?? 'redis://localhost:6379';
export const INFERENCE_URL = process.env.INFERENCE_URL ?? 'http://localhost:8001';
export const PORT = Number(process.env.PORT ?? 3001);

// Repo-level data/ folder (the API is started from services/api).
export const DATA_DIR = resolve(process.env.DATA_DIR ?? '../../data');

export const TOPICS = {
  factsRaw: 'facts.raw',
  segmentsRequested: 'segments.requested',
  scriptsReady: 'scripts.ready',
} as const;

export const SEGMENT_QUEUE = 'queue:segments'; // Redis list of SegmentReady JSON
export const HTTP_TIMEOUT_MS = 20_000;
export const IDEMPOTENCY_TTL_S = 3600;
