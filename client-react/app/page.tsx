import { TaskGrid } from './components/task-grid';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
          Task Tracker - React
        </h1>
        <TaskGrid />
      </div>
    </main>
  );
}
