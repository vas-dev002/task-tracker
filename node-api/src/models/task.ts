import { UUID } from "crypto";

export interface Task {
  id: UUID;
  title: string;
  completed: boolean;
}

export let tasks: Task[] = [];
