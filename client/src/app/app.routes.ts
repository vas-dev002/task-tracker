import { Routes } from '@angular/router';
import { GridView } from './pages/grid/components/grid-view/grid-view';

export const routes: Routes = [
  { path: '', component: GridView },
  { path: '**', redirectTo: '' },
];
