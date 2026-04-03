import './globals.css';

export const metadata = {
  title: 'ScholarGraph AI — From Information Overload to Exam Intelligence',
  description: 'GenAI-powered academic intelligence platform. Predict exam topics, visualize knowledge graphs, and generate adaptive study plans.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
