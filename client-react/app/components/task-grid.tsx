'use client';

import React, { useState } from 'react';
import { Task } from '@shared/models/task';
import { useTasksApi } from '../hooks/use-tasks-api';
import { AddTaskDialog } from './add-task-dialog';
import { Table, Button, Checkbox, Space, Popconfirm, Card, message } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

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
          message.success('Task added successfully');
        },
        onError: () => {
          message.error('Failed to add task');
        },
      }
    );
  };

  const handleTaskToggle = (task: Task) => {
    updateTaskMutation.mutate(
      {
        id: task.id,
        task: { completed: !task.completed },
      },
      {
        onSuccess: () => {
          message.success(task.completed ? 'Task marked as incomplete' : 'Task completed');
        },
        onError: () => {
          message.error('Failed to update task');
        },
      }
    );
  };

  const handleTaskDelete = (taskId: string) => {
    deleteTaskMutation.mutate(taskId, {
      onSuccess: () => {
        message.success('Task deleted successfully');
      },
      onError: () => {
        message.error('Failed to delete task');
      },
    });
  };

  const columns: ColumnsType<Task> = [
    {
      title: 'Status',
      dataIndex: 'completed',
      key: 'completed',
      width: 100,
      render: (completed: boolean, record: Task) => (
        <Checkbox checked={completed} onChange={() => handleTaskToggle(record)} />
      ),
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: Task) => (
        <span style={{ textDecoration: record.completed ? 'line-through' : 'none' }}>{title}</span>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record: Task) => (
        <Space>
          <Popconfirm
            title="Delete Task"
            description="Are you sure you want to delete this task?"
            onConfirm={() => handleTaskDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (error) {
    message.error('Error loading tasks');
  }

  return (
    <div className="container mx-auto p-6">
      <Card
        title="Task Manager"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAddTask}>
            Add Task
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} tasks`,
          }}
          locale={{
            emptyText: 'No tasks found. Add your first task!',
          }}
        />
      </Card>

      <AddTaskDialog
        isOpen={isDialogOpen}
        onClose={handleDialogClose}
        onSubmit={handleTaskSubmit}
      />
    </div>
  );
};
