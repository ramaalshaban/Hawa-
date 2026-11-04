import { NestFactory } from '@nestjs/core';
import { NestExpressApplication } from '@nestjs/platform-express';
import { AppModule } from './app.module';
import { DATA_DIR, PORT } from './config';

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);
  app.enableCors(); // the Next.js page (another origin) fetches /segments/latest
  app.useStaticAssets(DATA_DIR, { prefix: '/media' }); // /media/segments/<id>.wav -> data/segments/<id>.wav
  app.enableShutdownHooks(); // lets Kafka/Redis disconnect cleanly on Ctrl+C
  await app.listen(PORT);
}
void bootstrap();
