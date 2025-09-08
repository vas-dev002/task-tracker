import { HttpClient } from '@angular/common/http';
import { inject } from '@angular/core';
import { ENVIRONMENT } from 'vas-shared';
import { Task } from 'vas-shared/common';

export class TasksEndpoint {
  protected env = inject(ENVIRONMENT);
  protected baseUrl = this.env.baseUrl;
  protected http = inject(HttpClient);

  public getTasks$() {
    return this.http.get(`${this.baseUrl}/tasks`);
  }

  public createTask$(task: Task) {
    return this.http.post(`${this.baseUrl}/tasks`, task);
  }

  public updateTask$({ task, id }: { task: Partial<Task>; id: string }) {
    return this.http.patch(`${this.baseUrl}/tasks/${id}`, task);
  }

  public deleteTask$(id: string) {
    return this.http.delete(`${this.baseUrl}/tasks/${id}`);
  }
}
