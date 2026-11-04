import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { INFERENCE_URL, SEGMENT_QUEUE, TOPICS } from './config';
import { ScriptReady, SegmentReady } from './contracts';
import { fetchJson } from './http.util';
import { KafkaService } from './kafka.service';
import { RedisService } from './redis.service';

/** scripts.ready -> POST /tts -> Redis list queue:segments */
@Injectable()
export class AudioWorker implements OnModuleInit {
  private readonly log = new Logger(AudioWorker.name);

  constructor(
    private readonly kafka: KafkaService,
    private readonly redis: RedisService,
  ) {}

  async onModuleInit(): Promise<void> {
    await this.kafka.subscribe<ScriptReady>(TOPICS.scriptsReady, 'audio-worker', (s) =>
      this.handle(s),
    );
  }

  private async handle(script: ScriptReady): Promise<void> {
    const key = `idem:audio:${script.id}`;
    if (!(await this.redis.claim(key))) {
      this.log.warn(`skip duplicate script ${script.id}`);
      return;
    }
    try {
      const out = await fetchJson<{ path: string; durationS: number }>(`${INFERENCE_URL}/tts`, {
        method: 'POST',
        body: { id: script.id, text: script.text, voice: script.host },
      });
      const ready: SegmentReady = {
        id: script.id,
        path: out.path,
        durationS: out.durationS,
        host: script.host,
      };
      await this.redis.client.lpush(SEGMENT_QUEUE, JSON.stringify(ready)); // newest at index 0
      this.log.log(`audio written ${script.id} (${out.durationS.toFixed(1)}s)`);
    } catch (err) {
      await this.redis.release(key);
      throw err;
    }
  }
}
