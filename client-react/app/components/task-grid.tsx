'use client';

import React, { useState } from 'react';
import { Task } from '@shared/models/task';
import { useTasksApi } from '../hooks/use-tasks-api';
import { AddTaskDialog } from './add-task-dialog';

export const TaskGrid: React.FC = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const { useGetTasks, useCreateTask, useUpdateTask, useDeleteTask } = useTasksApi();

  const { data: tasks = [], isLoading, error } = useGetTasks();
  const createTaskMutation = useCreateTask();
  const updateTaskMutation = useUpdateTask();
  const deleteTaskMutation = useDeleteTask();

  const handleAddTask = () => {
    setIsDialogOpen(true);
  };

  const handleDialogClose = () => {
    setIsDialogOpen(false);
  };

  const handleTaskSubmit = (data: { title: string }) => {
    createTaskMutation.mutate(
      { title: data.title, completed: false },
      {
        onSuccess: () => {
          setIsDialogOpen(false);
        },
      }
    );
  };

  const handleTaskToggle = (task: Task) => {
    updateTaskMutation.mutate({
      id: task.id,
      task: { completed: !task.completed },
    });
  };

  const handleTaskDelete = (taskId: string) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      deleteTaskMutation.mutate(taskId);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading tasks...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-red-600">Error loading tasks</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md">
        {/* Toolbar */}
        <div className="border-b border-gray-200 p-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-800">Task Manager</h2>
            <button
              onClick={handleAddTask}
              className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <span className="text-lg">+</span>
              Add Task
            </button>
          </div>
        </div>

        {/* Task Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-4 text-center text-gray-500">
                    No tasks found. Add your first task!
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr key={task.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={task.completed}
                        onChange={() => handleTaskToggle(task)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div
                        className={`text-sm ${
                          task.completed
                            ? 'text-gray-500 line-through'
                            : 'text-gray-900 font-medium'
                        }`}
                      >
                        {task.title}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button
                        onClick={() => handleTaskDelete(task.id)}
                        className="text-red-600 hover:text-red-800 transition-colors"
                        title="Delete task"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <AddTaskDialog
        isOpen={isDialogOpen}
        onClose={handleDialogClose}
        onSubmit={handleTaskSubmit}
      />
    </div>
  );
};
