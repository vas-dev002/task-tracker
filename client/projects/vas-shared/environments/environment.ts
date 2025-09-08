import { InjectionToken } from '@angular/core';

export interface Environment {
  baseUrl: string;
  production: boolean;
  envTitle: string;
}

export const ENVIRONMENT = new InjectionToken<Environment>('App Environment');
