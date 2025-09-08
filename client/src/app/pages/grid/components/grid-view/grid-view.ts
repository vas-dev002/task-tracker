import { Component, inject } from '@angular/core';
import { TableModule } from 'primeng/table';
import { TasksEndpoint } from '../../endpoints/tasks.endponit';
import { toSignal } from '@angular/core/rxjs-interop';
import { Task } from 'vas-shared/common';

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
  public tasks = toSignal<Task[]>(this.tasksEndpoint.getTasks$());
}
