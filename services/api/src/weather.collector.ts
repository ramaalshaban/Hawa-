import { Injectable } from '@nestjs/common';
import { randomUUID } from 'node:crypto';
import { FactSnapshot } from './contracts';
import { fetchJson } from './http.util';

/** Cities on the air. Arabic names go straight into the facts so the LLM never has to translate. */
const CITIES = [
  { name: 'الرياض', lat: 24.71, lon: 46.68 },
  { name: 'جدة', lat: 21.54, lon: 39.17 },
  { name: 'مكة المكرمة', lat: 21.39, lon: 39.86 },
  { name: 'المدينة المنورة', lat: 24.47, lon: 39.61 },
];

// Open-Meteo takes comma-separated coordinates: ONE request, one result per city, in the same order.
const OPEN_METEO_URL =
  'https://api.open-meteo.com/v1/forecast' +
  `?latitude=${CITIES.map((c) => c.lat).join(',')}` +
  `&longitude=${CITIES.map((c) => c.lon).join(',')}` +
  '&current=temperature_2m,wind_speed_10m,weather_code';

interface OpenMeteoCurrent {
  current: { temperature_2m: number; wind_speed_10m: number; weather_code: number };
}

@Injectable()
export class WeatherCollector {
  /** One live reading for every city in CITIES, wrapped as a single FactSnapshot. */
  async collect(): Promise<FactSnapshot> {
    const results = await fetchJson<OpenMeteoCurrent[]>(OPEN_METEO_URL);
    if (!Array.isArray(results) || results.length !== CITIES.length) {
      // Fail loudly: a half-matched list would attach the wrong temperature to a city.
      throw new Error(`open-meteo returned ${JSON.stringify(results).slice(0, 100)}, expected ${CITIES.length} cities`);
    }
    return {
      id: randomUUID(),
      source: 'open-meteo',
      takenAt: new Date().toISOString(),
      data: {
        cities: CITIES.map((c, i) => ({ city: c.name, ...results[i].current })),
      },
    };
  }
}
