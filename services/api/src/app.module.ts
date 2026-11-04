import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { AudioWorker } from './audio.worker';
import { KafkaService } from './kafka.service';
import { RedisService } from './redis.service';
import { ScriptWorker } from './script.worker';
import { SegmentsController } from './segments.controller';
import { WeatherCollector } from './weather.collector';

@Module({
  imports: [],
  controllers: [AppController, SegmentsController],
  providers: [
    AppService,
    KafkaService,
    RedisService,
    WeatherCollector,
    ScriptWorker,
    AudioWorker,
  ],
})
export class AppModule {}
