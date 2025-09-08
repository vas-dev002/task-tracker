import { Component, inject, signal } from '@angular/core';
import { TableModule } from 'primeng/table';
import { Task } from 'vas-shared/common';
import { TasksEndpoint } from '../../endpoints/tasks.endponit';

@Component({
  selector: 'app-grid-view',
  imports: [TableModule],
  providers: [TasksEndpoint],
  templateUrl: './grid-view.html',
  styleUrl: './grid-view.scss',
  standalone: true,
})
export class GridView {
  protected tasksEndpoint = inject(TasksEndpoint);
  public tasks = signal<Task[]>([]);
}
