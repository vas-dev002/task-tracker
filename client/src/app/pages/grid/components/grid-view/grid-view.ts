import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { TableModule } from 'primeng/table';
import { TasksEndpoint } from '../../endpoints/tasks.endponit';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { Task } from 'vas-shared/common';
import { ButtonModule } from 'primeng/button';
import { AddTaskDialog } from '../add-task-dialog/add-task-dialog';
import { Subject, switchMap } from 'rxjs';
import { ToolbarModule } from 'primeng/toolbar';
import { CheckboxChangeEvent, CheckboxModule } from 'primeng/checkbox';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-grid-view',
  imports: [TableModule, ButtonModule, AddTaskDialog, ToolbarModule, CheckboxModule, FormsModule],
  providers: [TasksEndpoint],
  templateUrl: './grid-view.html',
  styleUrl: './grid-view.scss',
  standalone: true,
})
export class GridView implements OnInit {
  protected tasksEndpoint = inject(TasksEndpoint);
  protected destroyRef = inject(DestroyRef);
  public taskDialogVisible = signal(false);
  protected getTasks$ = new Subject<void>();
  public tasks = toSignal<Task[]>(this.getTasks$.pipe(switchMap(() => this.tasksEndpoint.getTasks$())));

  public ngOnInit(): void {
    this.getTasks$.next();
  }

  public addTask() {
    this.taskDialogVisible.set(true);
  }

  public handleResult(data: Partial<Task>) {
    this.taskDialogVisible.set(false);
    this.tasksEndpoint
      .createTask$(data)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.getTasks$.next();
      });
  }

  public handleCancel() {
    this.taskDialogVisible.set(false);
  }

  public deleteTask(task: Task) {
    this.tasksEndpoint
      .deleteTask$(task.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.getTasks$.next();
      });
  }

  taskStatusChange(event: CheckboxChangeEvent, task: Task) {
    this.tasksEndpoint
      .updateTask$({ id: task.id, task: { completed: event.checked } })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe();
  }
}
