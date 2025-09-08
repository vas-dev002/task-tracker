import { UUID } from 'crypto';

export interface Task {
  id: UUID;
  title: string;
  completed: boolean;
}

export const TaskProtectedFields: Array<keyof Task> = ['id'];

export let tasks: Task[] = [];
