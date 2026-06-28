'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function NewsFeed({ initialNews }) {
  const [news, setNews] = useState(initialNews);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Tất cả');

  // Categories list
  const categories = ['Tất cả', 'Lệ phí môn bài', 'Thuế khoán', 'Hóa đơn điện tử', 'Khác'];

  // Filter news based on category and search query
  const filteredNews = news.filter(item => {
    const matchesCategory = selectedCategory === 'Tất cả' || item.category === selectedCategory;
    const matchesSearch = 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
      item.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.content.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div>
      <section className="news-hero">
        <div className="container">
          <h1 className="news-hero-title">Kiến Thức & Tin Tức Thuế Hộ Kinh Doanh</h1>
          <p style={{ color: 'var(--muted)', fontSize: '1.15rem', maxWidth: '700px', margin: '0 auto' }}>
            Cập nhật nhanh chóng, chính xác các văn bản pháp luật, hướng dẫn tính thuế khoán, lệ phí môn bài và quản lý hóa đơn cho hộ kinh doanh cá thể.
          </p>
        </div>
      </section>

      <div className="container">
        {/* Search and Filters */}
        <div className="news-search-filter animate-slide-up">
          <div className="search-wrapper">
            <svg 
              className="search-icon" 
              xmlns="http://www.w3.org/2000/svg" 
              width="18" 
              height="18" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.3-4.3"></path>
            </svg>
            <input
              type="text"
              className="search-input"
              placeholder="Tìm kiếm bài viết, tài liệu hướng dẫn..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="filter-categories">
            {categories.map((category) => (
              <button
                key={category}
                className={`filter-btn ${selectedCategory === category ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* News Grid */}
        <h2 style={{ fontSize: '1.5rem', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '4px', height: '24px', backgroundColor: 'var(--primary)', display: 'inline-block', borderRadius: '2px' }}></span>
          Bài viết mới nhất
        </h2>

        {filteredNews.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', border: '1px dashed var(--border)', borderRadius: 'var(--radius)', backgroundColor: 'var(--card-bg)', marginBottom: '60px' }}>
            <p style={{ fontSize: '1.1rem', color: 'var(--muted)', margin: 0 }}>Không tìm thấy bài viết nào phù hợp với bộ lọc hiện tại.</p>
          </div>
        ) : (
          <div className="news-grid animate-fade">
            {filteredNews.map((item) => (
              <article key={item.id} className="news-card">
                <div className="news-card-body">
                  <div className="news-card-meta">
                    <span className="badge badge-primary">{item.category}</span>
                    <span className="news-date" style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                      {formatDate(item.date)}
                    </span>
                  </div>
                  <h3 className="news-card-title">{item.title}</h3>
                  <p className="news-card-summary">{item.summary}</p>
                  
                  <div style={{ marginTop: 'auto' }}>
                    <Link href={`/news/${item.id}`} className="news-card-link">
                      Đọc chi tiết
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M5 12h14M12 5l7 7-7 7"></path>
                      </svg>
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
