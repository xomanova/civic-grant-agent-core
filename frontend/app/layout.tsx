import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Civic Grant Agent',
  description: 'AI-powered grant finding and writing for fire departments and EMS agencies',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
