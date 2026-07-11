import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Tayari.ai — Interview Coach',
  description:
    'AI-powered conversational interview simulator for technical and behavioral preparation.',
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22 font-family=%22monospace%22>Ti</text></svg>',
  },
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
