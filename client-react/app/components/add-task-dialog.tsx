'use client';

import React, { useState } from 'react';
import { Modal, Input, Form, message } from 'antd';

interface AddTaskDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { title: string }) => void;
}

export const AddTaskDialog: React.FC<AddTaskDialogProps> = ({ isOpen, onClose, onSubmit }) => {
  const [form] = Form.useForm();

  const handleSubmit = () => {
    form
      .validateFields()
      .then((values) => {
        onSubmit({ title: values.title.trim() });
        form.resetFields();
      })
      .catch(() => {
        message.error('Please fill in the task title');
      });
  };

  const handleClose = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title="Add New Task"
      open={isOpen}
      onOk={handleSubmit}
      onCancel={handleClose}
      okText="Add Task"
      cancelText="Cancel"
    >
      <Form form={form} layout="vertical" className="mt-4">
        <Form.Item
          name="title"
          label="Task Title"
          rules={[
            { required: true, message: 'Please enter a task title' },
            { whitespace: true, message: 'Task title cannot be empty' },
          ]}
        >
          <Input placeholder="Enter task title" size="large" />
        </Form.Item>
      </Form>
    </Modal>
  );
};
