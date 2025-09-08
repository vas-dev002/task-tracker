import { Request, Response, NextFunction } from "express";
import { tasks, Task } from "../models/task";
import { randomUUID } from "crypto";

export const createTask = (req: Request, res: Response, next: NextFunction) => {
  try {
    const { title, completed } = req.body;
    if (!title || completed === undefined) {
      res.status(400).json({ message: "Invalid task data" });
      return;
    }
    const newTitle: Task = { id: randomUUID(), title, completed };
    tasks.push(newTitle);
    res.status(201).json(newTitle);
  } catch (error) {
    next(error);
  }
};

export const getTasks = (req: Request, res: Response, next: NextFunction) => {
  try {
    res.json(tasks);
  } catch (error) {
    next(error);
  }
};

export const getTaskById = (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { id } = req.params;
    const task = tasks.find((i) => i.id === id);
    if (!task) {
      res.status(404).json({ message: "Task not found" });
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
    const { completed } = req.body;
    const itemIndex = tasks.findIndex((i) => i.id === id);
    if (itemIndex === -1) {
      res.status(404).json({ message: "Task not found" });
      return;
    }
    tasks[itemIndex].completed = completed;
    res.json(tasks[itemIndex]);
  } catch (error) {
    next(error);
  }
};

export const deleteTask = (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;
    const taskIndex = tasks.findIndex((i) => i.id === id);
    if (taskIndex === -1) {
      res.status(404).json({ message: "Task not found" });
      return;
    }
    const deletedTask = tasks.splice(taskIndex, 1)[0];
    res.json(deletedTask);
  } catch (error) {
    next(error);
  }
};
