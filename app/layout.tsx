import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Tayari.ai — Interview Coach',
  description:
    'AI-powered conversational interview simulator for technical and behavioral preparation.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-black text-zinc-100 antialiased">{children}</body>
    </html>
  );
}
