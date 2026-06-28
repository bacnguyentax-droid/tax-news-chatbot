import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Cổng Thông Tin Thuế Hộ Kinh Doanh & Chatbot AI",
  description: "Trang tin tức cập nhật chính sách thuế mới nhất dành cho hộ kinh doanh cá thể tại Việt Nam và tích hợp chatbot trả lời tự động dựa trên tài liệu pháp luật.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi" className={`${geistSans.variable} ${geistMono.variable}`} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('theme');
                  if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                    document.documentElement.classList.add('dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body>
        <Navbar />
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {children}
        </main>
        <footer className="footer">
          <div className="container footer-content">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <div className="logo-icon" style={{ width: '28px', height: '28px', fontSize: '0.85rem' }}>T</div>
              <span style={{ fontWeight: 700, color: 'var(--foreground)' }}>TaxHKD.vn</span>
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem' }}>
              © {new Date().getFullYear()} Cổng Thông Tin Thuế Hộ Kinh Doanh. Nền tảng chatbot thông minh tự động hỗ trợ giải đáp pháp luật thuế.
            </p>
            <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--muted)' }}>
              Phát triển trên nền tảng Gemini AI & Tài liệu Thuế Việt Nam.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
