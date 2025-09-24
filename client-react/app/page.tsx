"use client";

import { Button } from "antd";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold text-gray-800 mb-4">Hello World</h1>
        <p className="text-xl text-gray-600 max-w-lg mx-auto">
          Welcome to Task Tracker - React + Next.js Edition
        </p>
        <div className="space-y-4">
          <div className="text-sm text-gray-500">
            Built with Next.js 13+, TypeScript, TailwindCSS, and Ant Design
          </div>
          <Button
            type="primary"
            size="large"
            className="bg-blue-600 hover:bg-blue-700"
          >
            Get Started
          </Button>
        </div>
      </div>
    </main>
  );
}
