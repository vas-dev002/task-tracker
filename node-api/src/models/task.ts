import { UUID } from 'crypto';

export interface Task {
  id: UUID;
  title: string;
  completed: boolean;
}

export const TaskProtectedFields: (keyof Task)[] = ['id'];

export const TasksStorage: Task[] = [
  {
    id: 'eb9955a2-c6cf-40df-831a-2d84a7033e6a',
    title: 'Initial Task',
    completed: false,
  },
  {
    id: 'cd37afda-1006-41c0-a708-bc2939c9400e',
    title: 'Second Task',
    completed: true,
  },
  {
    id: '888f6e5e-601a-4e59-b57c-565997cba5d6',
    title: 'Third Task',
    completed: false,
  },
];
