'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Task } from '@shared/models/task';
import { useEnvironment } from '@shared/providers/environment-provider';

export const useTasksApi = () => {
  const environment = useEnvironment();
  const queryClient = useQueryClient();

  const api = axios.create({
    baseURL: environment.baseUrl,
  });

  const useGetTasks = () => {
    return useQuery({
      queryKey: ['tasks'],
      queryFn: async (): Promise<Task[]> => {
        const response = await api.get<Task[]>('/tasks');
        return response.data;
      },
    });
  };

  const useCreateTask = () => {
    return useMutation({
      mutationFn: async (task: Partial<Task>): Promise<Task> => {
        const response = await api.post<Task>('/tasks', task);
        return response.data;
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['tasks'] });
      },
    });
  };

  const useUpdateTask = () => {
    return useMutation({
      mutationFn: async ({ id, task }: { id: string; task: Partial<Task> }): Promise<Task> => {
        const response = await api.patch<Task>(`/tasks/${id}`, task);
        return response.data;
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['tasks'] });
      },
    });
  };

  const useDeleteTask = () => {
    return useMutation({
      mutationFn: async (id: string): Promise<void> => {
        await api.delete(`/tasks/${id}`);
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['tasks'] });
      },
    });
  };

  return {
    useGetTasks,
    useCreateTask,
    useUpdateTask,
    useDeleteTask,
  };
};
