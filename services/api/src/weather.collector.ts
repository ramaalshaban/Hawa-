import { Injectable } from '@nestjs/common';
import { randomUUID } from 'node:crypto';
import { FactSnapshot } from './contracts';
import { fetchJson } from './http.util';

const OPEN_METEO_RIYADH =
  'https://api.open-meteo.com/v1/forecast?latitude=24.71&longitude=46.68' +
  '&current=temperature_2m,wind_speed_10m,weather_code';

@Injectable()
export class WeatherCollector {
  /** One live reading for Riyadh, wrapped as a FactSnapshot. */
  async collect(): Promise<FactSnapshot> {
    const data = await fetchJson<Record<string, unknown>>(OPEN_METEO_RIYADH);
    return {
      id: randomUUID(),
      source: 'open-meteo',
      takenAt: new Date().toISOString(),
      data, // keeps Open-Meteo's shape: { current: { temperature_2m, ... } }
    };
  }
}
