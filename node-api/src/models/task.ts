import { UUID } from 'crypto';

export interface Task {
  id: UUID;
  title: string;
  completed: boolean;
}

export const TaskProtectedFields: (keyof Task)[] = ['id'];

export const TasksStorage: Task[] = [];
