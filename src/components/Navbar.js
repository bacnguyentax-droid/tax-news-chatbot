'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    // Read theme from localStorage or document class on mount
    const isDark = document.documentElement.classList.contains('dark');
    setTheme(isDark ? 'dark' : 'light');
  }, []);

  const toggleTheme = () => {
    if (theme === 'light') {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
      setTheme('dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
      setTheme('light');
    }
  };

  return (
    <header className="main-header">
      {/* Top Section: White background with Logo and Portal Title */}
      <div className="header-top">
        <div className="container header-top-content">
          <Link href="/" className="gov-logo">
            <div className="gov-emblem">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="32" height="32">
                <circle cx="50" cy="50" r="48" fill="#d32f2f" stroke="#ffb300" strokeWidth="4" />
                <polygon points="50,15 61,38 86,38 66,54 73,78 50,63 27,78 34,54 14,38 39,38" fill="#ffeb3b" />
              </svg>
            </div>
            <div className="logo-text-group">
              <span className="logo-title-upper">CỔNG THÔNG TIN THUẾ HỘ KINH DOANH</span>
              <span className="logo-title-lower">Hành chính phục vụ • Cục Thuế - Bộ Tài chính</span>
            </div>
          </Link>
          
          <div className="header-top-actions">
            <Link href="/admin" className="btn-gov-outline">Đăng ký</Link>
            <Link href="/admin" className="btn-gov-solid">Đăng nhập</Link>
          </div>
        </div>
      </div>

      {/* Bottom Section: Solid Blue Navigation Bar */}
      <div className="header-bottom">
        <div className="container header-bottom-content">
          <nav className="gov-nav">
            <ul className="gov-nav-links">
              <li>
                <Link 
                  href="/" 
                  className={`gov-nav-link ${pathname === '/' ? 'active' : ''}`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
                    <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                    <polyline points="9 22 9 12 15 12 15 22"></polyline>
                  </svg>
                  TRANG CHỦ
                </Link>
              </li>
              <li>
                <Link 
                  href="/" 
                  className={`gov-nav-link ${pathname.startsWith('/news') || pathname === '/' ? 'active' : ''}`}
                >
                  TIN TỨC THUẾ
                </Link>
              </li>
              <li>
                <Link 
                  href="/chat" 
                  className={`gov-nav-link ${pathname === '/chat' ? 'active' : ''}`}
                >
                  💬 CHATBOT HỎI THUẾ
                </Link>
              </li>
              <li>
                <Link 
                  href="/admin" 
                  className={`gov-nav-link ${pathname === '/admin' ? 'active' : ''}`}
                >
                  QUẢN TRỊ VIÊN
                </Link>
              </li>
            </ul>

            <button 
              onClick={toggleTheme} 
              className="gov-theme-toggle"
              title="Đổi giao diện Sáng/Tối"
              aria-label="Toggle Theme"
            >
              {theme === 'light' ? (
                // Sun Icon
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="4"></circle>
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>
                </svg>
              ) : (
                // Moon Icon
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path>
                </svg>
              )}
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}
