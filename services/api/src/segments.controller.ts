import { Controller, Get, HttpCode, Logger, NotFoundException, Post } from '@nestjs/common';
import { randomUUID } from 'node:crypto';
import { SEGMENT_QUEUE, TOPICS } from './config';
import { SegmentReady, SegmentRequest } from './contracts';
import { KafkaService } from './kafka.service';
import { RedisService } from './redis.service';
import { WeatherCollector } from './weather.collector';

@Controller()
export class SegmentsController {
  private readonly log = new Logger(SegmentsController.name);

  constructor(
    private readonly weather: WeatherCollector,
    private readonly kafka: KafkaService,
    private readonly redis: RedisService,
  ) {}

  /** Dev trigger: collect the weather and start one segment. Returns 202 = accepted, not finished. */
  @Post('dev/segment/weather')
  @HttpCode(202)
  async triggerWeather(): Promise<{ id: string }> {
    const fact = await this.weather.collect();
    await this.kafka.produce(TOPICS.factsRaw, fact.id, fact);

    const req: SegmentRequest = {
      id: randomUUID(),
      kind: 'weather',
      host: 'anchor',
      facts: [fact],
      createdAt: new Date().toISOString(),
    };
    await this.kafka.produce(TOPICS.segmentsRequested, req.id, req);
    this.log.log(`request produced ${req.id}`);
    return { id: req.id };
  }

  /** Newest finished segment, for the web player. */
  @Get('segments/latest')
  async latest(): Promise<SegmentReady> {
    const raw = await this.redis.client.lindex(SEGMENT_QUEUE, 0);
    if (!raw) throw new NotFoundException('no segments yet');
    return JSON.parse(raw) as SegmentReady;
  }
}
