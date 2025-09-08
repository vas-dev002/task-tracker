import { HttpClient } from '@angular/common/http';
import { inject } from '@angular/core';
import { ENVIRONMENT } from 'vas-shared';
import { Task } from 'vas-shared/common';

export class TasksEndpoint {
  protected env = inject(ENVIRONMENT);
  protected http = inject(HttpClient);

  public getTasks$() {
    return this.http.get<Task[]>(`tasks`, { mode: 'no-cors' });
  }

  public createTask$(task: Task) {
    return this.http.post<Task>(`tasks`, task);
  }

  public updateTask$({ task, id }: { task: Partial<Task>; id: string }) {
    return this.http.patch<Task>(`tasks/${id}`, task);
  }

  public deleteTask$(id: string) {
    return this.http.delete<Task>(`tasks/${id}`);
  }
}
