import { Injectable, OnModuleDestroy } from '@nestjs/common';
import Redis from 'ioredis';
import { IDEMPOTENCY_TTL_S, REDIS_URL } from './config';

@Injectable()
export class RedisService implements OnModuleDestroy {
  readonly client = new Redis(REDIS_URL);

  /**
   * Claim a job: SET key NX EX 3600. Returns true for the first caller only,
   * so a redelivered Kafka message is skipped instead of processed twice.
   */
  async claim(key: string): Promise<boolean> {
    return (await this.client.set(key, '1', 'EX', IDEMPOTENCY_TTL_S, 'NX')) === 'OK';
  }

  /** Give a claim back after a failure, so the retry is allowed to run. */
  async release(key: string): Promise<void> {
    await this.client.del(key);
  }

  async onModuleDestroy(): Promise<void> {
    await this.client.quit();
  }
}
