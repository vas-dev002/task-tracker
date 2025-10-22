import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { QueryProvider } from './providers/query-provider';
import { EnvironmentProvider } from '@shared/providers/environment-provider';
import { environment } from './config/environment';
import { AntdRegistry } from '@ant-design/nextjs-registry';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Task Tracker',
  description: 'Task management application built with Next.js and React',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <EnvironmentProvider environment={environment}>
          <QueryProvider>
            <AntdRegistry>{children}</AntdRegistry>
          </QueryProvider>
        </EnvironmentProvider>
      </body>
    </html>
  );
}
