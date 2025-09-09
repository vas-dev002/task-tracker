import { Request, Response, NextFunction } from 'express';
import { TasksStorage, Task, TaskProtectedFields } from '../models/task';
import { randomUUID } from 'crypto';

export const createTask = (req: Request, res: Response, next: NextFunction) => {
  try {
    const { title } = req.body;
    if (!title) {
      res.status(400).json({ message: 'Invalid task data' });
      return;
    }
    const newTitle: Task = { id: randomUUID(), title, completed: false };
    TasksStorage.push(newTitle);
    res.status(201).json(newTitle);
  } catch (error) {
    next(error);
  }
};

export const getTasks = (req: Request, res: Response, next: NextFunction) => {
  try {
    res.json(TasksStorage);
  } catch (error) {
    next(error);
  }
};

export const getTaskById = (
  req: Request,
  res: Response,
  next: NextFunction,
) => {
  try {
    const { id } = req.params;
    const task = TasksStorage.find((i) => i.id === id);
    if (!task) {
      res.status(404).json({ message: 'Task not found' });
      return;
    }
    res.json(task);
  } catch (error) {
    next(error);
  }
};

export const updateTask = (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;
    const patch = req.body as Partial<Task>;
    const taskIndex = TasksStorage.findIndex((i) => i.id === id);
    if (taskIndex === -1) {
      res.status(404).json({ message: 'Task not found' });
      return;
    }

    let updated = false;
    for (const [key, value] of Object.entries(patch)) {
      if (TaskProtectedFields.includes(key as keyof Task)) {
        continue;
      }
      if (Object.prototype.hasOwnProperty.call(TasksStorage[taskIndex], key)) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (TasksStorage[taskIndex] as any)[key] = value as any;
        updated = true;
      }
    }

    if (!updated) {
      res.status(400).json({ message: 'No valid fields provided to update' });
      return;
    }

    res.json(TasksStorage[taskIndex]);
  } catch (error) {
    next(error);
  }
};

export const deleteTask = (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;
    const taskIndex = TasksStorage.findIndex((i) => i.id === id);
    if (taskIndex === -1) {
      res.status(404).json({ message: 'Task not found' });
      return;
    }
    const deletedTask = TasksStorage.splice(taskIndex, 1)[0];
    res.json(deletedTask);
  } catch (error) {
    next(error);
  }
};
