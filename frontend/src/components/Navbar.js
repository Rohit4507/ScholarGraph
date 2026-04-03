'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();

  const links = [
    { href: '/dashboard', label: '📊 Dashboard' },
    { href: '/chat', label: '💬 Chat AI' },
    { href: '/upload', label: '📄 Upload' },
    { href: '/predict', label: '🎯 Predict' },
    { href: '/graph', label: '🕸️ Graph' },
    { href: '/quiz', label: '🧠 Quiz' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link href="/" className="navbar-brand">
          <span>🎓 ScholarGraph AI</span>
        </Link>
        <div className="navbar-links">
          {links.map(link => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname === link.href ? 'active' : ''}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
