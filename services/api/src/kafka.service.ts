import { Injectable, Logger, OnModuleDestroy } from '@nestjs/common';
import { Consumer, Kafka, Producer } from 'kafkajs';
import { KAFKA_BROKERS } from './config';

@Injectable()
export class KafkaService implements OnModuleDestroy {
  private readonly log = new Logger(KafkaService.name);
  private readonly kafka = new Kafka({ clientId: 'hawa-api', brokers: KAFKA_BROKERS });
  private readonly producer: Producer = this.kafka.producer();
  private producerReady?: Promise<void>;
  private readonly consumers: Consumer[] = [];

  /** Send one JSON message. `key` keeps messages with the same id on the same partition. */
  async produce<T>(topic: string, key: string, value: T): Promise<void> {
    await (this.producerReady ??= this.producer.connect());
    await this.producer.send({ topic, messages: [{ key, value: JSON.stringify(value) }] });
  }

  /**
   * Run `handler` for every message. The offset is committed only AFTER the handler
   * resolves: if it throws, nothing is committed and kafkajs retries the message
   * (at-least-once delivery, so handlers must be idempotent).
   */
  async subscribe<T>(
    topic: string,
    groupId: string,
    handler: (value: T) => Promise<void>,
  ): Promise<void> {
    const consumer = this.kafka.consumer({ groupId });
    this.consumers.push(consumer);
    await consumer.connect();
    await consumer.subscribe({ topic });
    await consumer.run({
      autoCommit: false,
      eachMessage: async ({ topic, partition, message }) => {
        const value = JSON.parse(message.value!.toString()) as T;
        await handler(value);
        await consumer.commitOffsets([
          { topic, partition, offset: (BigInt(message.offset) + 1n).toString() },
        ]);
      },
    });
    this.log.log(`subscribed: ${topic} (group ${groupId})`);
  }

  async onModuleDestroy(): Promise<void> {
    await Promise.all(this.consumers.map((c) => c.disconnect()));
    if (this.producerReady) await this.producer.disconnect();
  }
}
