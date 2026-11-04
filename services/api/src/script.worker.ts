import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { INFERENCE_URL, TOPICS } from './config';
import { ScriptReady, SegmentRequest } from './contracts';
import { fetchJson } from './http.util';
import { KafkaService } from './kafka.service';
import { RedisService } from './redis.service';

/** segments.requested -> POST /script -> scripts.ready */
@Injectable()
export class ScriptWorker implements OnModuleInit {
  private readonly log = new Logger(ScriptWorker.name);

  constructor(
    private readonly kafka: KafkaService,
    private readonly redis: RedisService,
  ) {}

  async onModuleInit(): Promise<void> {
    await this.kafka.subscribe<SegmentRequest>(
      TOPICS.segmentsRequested,
      'script-worker',
      (req) => this.handle(req),
    );
  }

  private async handle(req: SegmentRequest): Promise<void> {
    const key = `idem:script:${req.id}`;
    if (!(await this.redis.claim(key))) {
      this.log.warn(`skip duplicate request ${req.id}`);
      return;
    }
    try {
      const out = await fetchJson<{ text: string; lang: string; source: string }>(
        `${INFERENCE_URL}/script`,
        { method: 'POST', body: { kind: req.kind, host: req.host, facts: req.facts } },
      );
      const ready: ScriptReady = { id: req.id, host: req.host, text: out.text, lang: out.lang };
      await this.kafka.produce(TOPICS.scriptsReady, req.id, ready);
      this.log.log(`script produced ${req.id} (${out.source})`);
    } catch (err) {
      await this.redis.release(key); // let the Kafka retry run
      throw err;
    }
  }
}
