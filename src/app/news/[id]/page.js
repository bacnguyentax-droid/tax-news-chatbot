import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getNewsById } from '@/lib/db';

export const dynamic = 'force-dynamic';

function renderMarkdownToHtml(markdownText) {
  if (!markdownText) return '';

  const lines = markdownText.split('\n');
  let html = [];
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i].trim();

    // Process lists
    if (line.startsWith('- ')) {
      if (!inList) {
        html.push('<ul class="news-list">');
        inList = true;
      }
      const itemText = line.substring(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      html.push(`<li>${itemText}</li>`);
      continue;
    } else if (inList && !line.startsWith('- ') && line !== '') {
      html.push('</ul>');
      inList = false;
    }

    // Process headers
    if (line.startsWith('## ')) {
      const headerText = line.substring(3).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      html.push(`<h2>${headerText}</h2>`);
    } else if (line.startsWith('### ')) {
      const headerText = line.substring(4).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      html.push(`<h3>${headerText}</h3>`);
    } else if (line === '') {
      // Empty line, ignore or add small spacing
      continue;
    } else {
      // Regular paragraph
      const formattedText = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      html.push(`<p>${formattedText}</p>`);
    }
  }

  if (inList) {
    html.push('</ul>');
  }

  return html.join('\n');
}

export default async function NewsDetail({ params }) {
  // Await the params object in Next.js 15+ App Router
  const { id } = await params;
  const article = getNewsById(id);

  if (!article) {
    notFound();
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const htmlContent = renderMarkdownToHtml(article.content);

  return (
    <div className="news-detail-container animate-fade">
      {/* Back button */}
      <Link href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '24px', fontWeight: 600, fontSize: '0.95rem' }}>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="m15 18-6-6 6-6"></path>
        </svg>
        Quay lại trang tin tức
      </Link>

      <article>
        <header className="news-detail-header">
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>{article.category}</span>
          <h1 style={{ fontSize: '2.25rem', marginBottom: '16px', lineHeight: 1.2 }}>{article.title}</h1>
          
          <div className="news-detail-meta">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect>
                <line x1="16" x2="16" y1="2" y2="6"></line>
                <line x1="8" x2="8" y1="2" y2="6"></line>
                <line x1="3" x2="21" y1="10" y2="10"></line>
              </svg>
              <span>{formatDate(article.date)}</span>
            </div>
            <span>•</span>
            <span>Tác giả: Ban Biên Tập TaxHKD</span>
          </div>
        </header>

        {/* Render content */}
        <div 
          className="news-content"
          dangerouslySetInnerHTML={{ __html: htmlContent }} 
        />
      </article>

      {/* Footer Banner */}
      <div 
        style={{ 
          marginTop: '60px', 
          padding: '30px', 
          backgroundColor: 'var(--card-bg)', 
          border: '1px solid var(--border)', 
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: '16px'
        }}
      >
        <h3 style={{ margin: 0, fontSize: '1.25rem' }}>Bạn cần tư vấn chi tiết hơn về trường hợp của mình?</h3>
        <p style={{ margin: 0, color: 'var(--muted)', fontSize: '0.95rem', maxWidth: '500px' }}>
          Hỏi ngay Trợ lý Thuế ảo thông minh của chúng tôi. Chatbot được huấn luyện trên tài liệu văn bản thuế chính thống của hộ kinh doanh.
        </p>
        <Link href="/chat" className="btn btn-primary" style={{ textDecoration: 'none' }}>
          💬 Trò chuyện với Chatbot
        </Link>
      </div>
    </div>
  );
}
