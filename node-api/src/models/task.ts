import { UUID } from 'crypto';

export interface Task {
  id: UUID;
  title: string;
  completed: boolean;
}

export const TaskProtectedFields: (keyof Task)[] = ['id'];

export const TasksStorage: Task[] = [
  {
    id: '00000000-0000-0000-0000-000000000000',
    title: 'Initial Task',
    completed: false,
  },
  {
    id: '11111111-1111-1111-1111-111111111111',
    title: 'Second Task',
    completed: true,
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    title: 'Third Task',
    completed: false,
  },
  {
    id: '33333333-3333-3333-3333-333333333333',
    title: 'Fourth Task',
    completed: true,
  },
];
