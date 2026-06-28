'use client';

import { useState, useEffect } from 'react';

export default function AdminPage() {
  // Simple auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [passwordInput, setPasswordInput] = useState('');
  const [loginError, setLoginError] = useState('');

  // Active tab state: 'stats', 'news', 'qa', 'pdf'
  const [activeTab, setActiveTab] = useState('stats');

  // Database list states
  const [news, setNews] = useState([]);
  const [qas, setQas] = useState([]);
  const [pdfs, setPdfs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Form states for News
  const [newsId, setNewsId] = useState(null);
  const [newsTitle, setNewsTitle] = useState('');
  const [newsSummary, setNewsSummary] = useState('');
  const [newsContent, setNewsContent] = useState('');
  const [newsCategory, setNewsCategory] = useState('Thuế khoán');
  const [isEditingNews, setIsEditingNews] = useState(false);

  // Form states for Q&A
  const [qaId, setQaId] = useState(null);
  const [qaQuestion, setQaQuestion] = useState('');
  const [qaAnswer, setQaAnswer] = useState('');
  const [isEditingQa, setIsEditingQa] = useState(false);

  // File state for PDF
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploadingPdf, setIsUploadingPdf] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');

  // Authentication check on mount
  useEffect(() => {
    const loggedIn = sessionStorage.getItem('admin_authenticated') === 'true';
    if (loggedIn) {
      setIsAuthenticated(true);
      fetchData();
    } else {
      setIsLoading(false);
    }
  }, []);

  const handleLogin = (e) => {
    e.preventDefault();
    // Static simple password for admin access
    const adminPassword = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || 'admin123';
    
    if (passwordInput === adminPassword) {
      setIsAuthenticated(true);
      sessionStorage.setItem('admin_authenticated', 'true');
      fetchData();
    } else {
      setLoginError('Mật mã quản trị không chính xác. Vui lòng thử lại!');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    sessionStorage.removeItem('admin_authenticated');
  };

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [newsRes, qaRes, pdfRes] = await Promise.all([
        fetch('/api/admin/news'),
        fetch('/api/admin/qa'),
        fetch('/api/admin/pdf')
      ]);

      if (newsRes.ok) setNews(await newsRes.json());
      if (qaRes.ok) setQas(await qaRes.json());
      if (pdfRes.ok) setPdfs(await pdfRes.json());
    } catch (err) {
      console.error('Lỗi khi tải dữ liệu trang quản trị:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // --- News Handlers ---
  const handleSaveNews = async (e) => {
    e.preventDefault();
    if (!newsTitle || !newsContent || !newsCategory) {
      alert('Vui lòng nhập đầy đủ các trường bắt buộc!');
      return;
    }

    const payload = {
      title: newsTitle,
      summary: newsSummary,
      content: newsContent,
      category: newsCategory
    };

    try {
      let res;
      if (isEditingNews && newsId) {
        // Update
        res = await fetch('/api/admin/news', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: newsId, ...payload })
        });
      } else {
        // Create
        res = await fetch('/api/admin/news', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      if (res.ok) {
        alert(isEditingNews ? 'Cập nhật tin tức thành công!' : 'Tạo tin tức mới thành công!');
        resetNewsForm();
        fetchData();
      } else {
        const errorData = await res.json();
        alert(`Lỗi: ${errorData.error}`);
      }
    } catch (err) {
      alert(`Đã xảy ra lỗi: ${err.message}`);
    }
  };

  const handleEditNews = (item) => {
    setNewsId(item.id);
    setNewsTitle(item.title);
    setNewsSummary(item.summary || '');
    setNewsContent(item.content);
    setNewsCategory(item.category);
    setIsEditingNews(true);
    window.scrollTo({ top: 300, behavior: 'smooth' });
  };

  const handleDeleteNews = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa bài viết này không?')) return;
    try {
      const res = await fetch(`/api/admin/news?id=${id}`, { method: 'DELETE' });
      if (res.ok) {
        alert('Xóa bài viết thành công!');
        fetchData();
      } else {
        const err = await res.json();
        alert(`Lỗi: ${err.error}`);
      }
    } catch (err) {
      alert(`Đã xảy ra lỗi: ${err.message}`);
    }
  };

  const resetNewsForm = () => {
    setNewsId(null);
    setNewsTitle('');
    setNewsSummary('');
    setNewsContent('');
    setNewsCategory('Thuế khoán');
    setIsEditingNews(false);
  };

  // --- Q&A Handlers ---
  const handleSaveQa = async (e) => {
    e.preventDefault();
    if (!qaQuestion || !qaAnswer) {
      alert('Vui lòng điền câu hỏi và câu trả lời!');
      return;
    }

    const payload = { question: qaQuestion, answer: qaAnswer };

    try {
      let res;
      if (isEditingQa && qaId) {
        res = await fetch('/api/admin/qa', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: qaId, ...payload })
        });
      } else {
        res = await fetch('/api/admin/qa', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      if (res.ok) {
        alert(isEditingQa ? 'Cập nhật Q&A thành công!' : 'Thêm Q&A mới thành công!');
        resetQaForm();
        fetchData();
      } else {
        const errorData = await res.json();
        alert(`Lỗi: ${errorData.error}`);
      }
    } catch (err) {
      alert(`Đã xảy ra lỗi: ${err.message}`);
    }
  };

  const handleEditQa = (item) => {
    setQaId(item.id);
    setQaQuestion(item.question);
    setQaAnswer(item.answer);
    setIsEditingQa(true);
    window.scrollTo({ top: 300, behavior: 'smooth' });
  };

  const handleDeleteQa = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa câu hỏi/đáp này không?')) return;
    try {
      const res = await fetch(`/api/admin/qa?id=${id}`, { method: 'DELETE' });
      if (res.ok) {
        alert('Xóa Q&A thành công!');
        fetchData();
      } else {
        const err = await res.json();
        alert(`Lỗi: ${err.error}`);
      }
    } catch (err) {
      alert(`Đã xảy ra lỗi: ${err.message}`);
    }
  };

  const resetQaForm = () => {
    setQaId(null);
    setQaQuestion('');
    setQaAnswer('');
    setIsEditingQa(false);
  };

  // --- PDF Upload Handlers ---
  const handleUploadPdf = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      alert('Vui lòng chọn một file PDF!');
      return;
    }

    setIsUploadingPdf(true);
    setUploadMessage('Hệ thống đang tải file lên và trích xuất dữ liệu văn bản. Vui lòng đợi...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('/api/admin/pdf', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();

      if (res.ok) {
        setUploadMessage('🎉 Tải lên và phân tích tài liệu PDF thành công!');
        setSelectedFile(null);
        // Clear file input
        document.getElementById('pdf-file-input').value = '';
        fetchData();
      } else {
        setUploadMessage(`❌ Lỗi: ${data.error}`);
      }
    } catch (err) {
      setUploadMessage(`❌ Lỗi kết nối: ${err.message}`);
    } finally {
      setIsUploadingPdf(false);
    }
  };

  const handleDeletePdf = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa tài liệu PDF này không? Chatbot sẽ không thể học thông tin từ file này nữa.')) return;
    try {
      const res = await fetch(`/api/admin/pdf?id=${id}`, { method: 'DELETE' });
      if (res.ok) {
        alert('Xóa tài liệu thành công!');
        fetchData();
      } else {
        const err = await res.json();
        alert(`Lỗi: ${err.error}`);
      }
    } catch (err) {
      alert(`Đã xảy ra lỗi: ${err.message}`);
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // --- Rendering UI ---

  if (!isAuthenticated) {
    return (
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1, minHeight: 'calc(100vh - 210px)' }}>
        <div className="login-container animate-slide-up">
          <div className="logo-icon" style={{ margin: '0 auto 16px auto', width: '48px', height: '48px' }}>🔐</div>
          <h1 style={{ fontSize: '1.5rem', marginBottom: '12px' }}>Trang Quản Trị Viên</h1>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '24px' }}>
            Vui lòng nhập mật mã quản trị để truy cập trang quản lý tài liệu học và bài viết tin tức.
          </p>

          <form onSubmit={handleLogin}>
            <div className="form-group" style={{ marginBottom: '16px', textAlign: 'left' }}>
              <label className="form-label">Mật mã quản trị</label>
              <input
                type="password"
                className="form-control"
                placeholder="Nhập mật mã (Mặc định: admin123)"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                required
              />
            </div>
            {loginError && <p style={{ color: 'var(--error)', fontSize: '0.85rem', marginBottom: '16px', fontWeight: 600 }}>{loginError}</p>}
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
              Đăng Nhập
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="container">
        {/* Admin Header */}
        <div className="admin-header">
          <div>
            <h1 style={{ fontSize: '1.85rem', margin: 0 }}>Trang Quản Trị Hệ Thống</h1>
            <p style={{ color: 'var(--muted)', margin: 0, fontSize: '0.95rem' }}>Quản lý tin tức, bộ câu hỏi Q&A và tài liệu huấn luyện AI.</p>
          </div>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            🚪 Đăng xuất
          </button>
        </div>

        {/* Tab Controls */}
        <div className="admin-tabs">
          <button className={`admin-tab ${activeTab === 'stats' ? 'active' : ''}`} onClick={() => setActiveTab('stats')}>
            📊 Tổng Quan
          </button>
          <button className={`admin-tab ${activeTab === 'news' ? 'active' : ''}`} onClick={() => setActiveTab('news')}>
            📰 Quản lý Tin Tức
          </button>
          <button className={`admin-tab ${activeTab === 'qa' ? 'active' : ''}`} onClick={() => setActiveTab('qa')}>
            ❓ Quản lý Q&A
          </button>
          <button className={`admin-tab ${activeTab === 'pdf' ? 'active' : ''}`} onClick={() => setActiveTab('pdf')}>
            📄 Tài liệu PDF
          </button>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <div style={{ fontSize: '1.2rem', color: 'var(--muted)' }}>Đang tải dữ liệu hệ thống...</div>
          </div>
        ) : (
          <div className="animate-fade">
            {/* Tab: STATS */}
            {activeTab === 'stats' && (
              <div>
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">{news.length}</span>
                    <span className="stat-label">Bài viết tin tức</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{qas.length}</span>
                    <span className="stat-label">Câu hỏi Q&A nạp</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{pdfs.length}</span>
                    <span className="stat-label">Tài liệu văn bản PDF</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value" style={{ color: 'var(--success)', fontSize: '1.5rem', height: '40px', display: 'flex', alignItems: 'center' }}>
                      Đang Hoạt Động
                    </span>
                    <span className="stat-label">Trạng thái Gemini AI</span>
                  </div>
                </div>

                <div className="admin-card">
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '16px' }}>Hướng dẫn Vận hành Hệ thống</h3>
                  <ol style={{ paddingLeft: '20px', lineHeight: 1.8, color: 'var(--muted)', fontSize: '0.95rem' }}>
                    <li><strong>Huấn luyện Chatbot bằng PDF</strong>: Chuyển qua tab "Tài liệu PDF", tải lên các văn bản Thuế chính thức. Hệ thống sẽ tự động quét, lưu trữ văn bản và cập nhật lập tức vào trí nhớ của Gemini.</li>
                    <li><strong>Nạp Q&A nhanh</strong>: Nếu muốn chatbot trả lời chính xác một số câu hỏi đặc thù theo ý muốn, bạn có thể nạp các cặp câu hỏi-trả lời cố định tại tab "Quản lý Q&A".</li>
                    <li><strong>Viết Tin Tức</strong>: Đăng tải tin tức luật thuế mới tại tab "Quản lý Tin Tức" để hiển thị trên trang chủ cho người dân và hộ kinh doanh theo dõi.</li>
                    <li><strong>Kiểm soát Chatbot</strong>: Chatbot được lập trình chỉ lấy dữ liệu từ 2 nguồn trên. Khi bạn cập nhật hoặc xóa tài liệu, câu trả lời của chatbot sẽ được cập nhật đồng bộ ngay lập tức.</li>
                  </ol>
                </div>
              </div>
            )}

            {/* Tab: NEWS */}
            {activeTab === 'news' && (
              <div>
                {/* Form Add/Edit */}
                <div className="admin-card">
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '20px' }}>
                    {isEditingNews ? '📝 Chỉnh sửa bài viết' : '➕ Viết bài mới'}
                  </h3>
                  
                  <form onSubmit={handleSaveNews} className="admin-form">
                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label">Tiêu đề bài viết <span>*</span></label>
                        <input
                          type="text"
                          className="form-control"
                          placeholder="Tiêu đề chính..."
                          value={newsTitle}
                          onChange={(e) => setNewsTitle(e.target.value)}
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Danh mục thuế <span>*</span></label>
                        <select
                          className="form-control"
                          value={newsCategory}
                          onChange={(e) => setNewsCategory(e.target.value)}
                        >
                          <option value="Lệ phí môn bài">Lệ phí môn bài</option>
                          <option value="Thuế khoán">Thuế khoán</option>
                          <option value="Hóa đơn điện tử">Hóa đơn điện tử</option>
                          <option value="Khác">Khác</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Tóm tắt ngắn</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Mô tả tóm tắt hiện trên thẻ bài viết..."
                        value={newsSummary}
                        onChange={(e) => setNewsSummary(e.target.value)}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Nội dung chi tiết <span>*</span> (Hỗ trợ Markdown cơ bản)</label>
                      <textarea
                        className="form-control form-textarea"
                        placeholder="Dùng ## để tạo tiêu đề lớn, ### tiêu đề phụ, - để tạo danh sách dòng..."
                        value={newsContent}
                        onChange={(e) => setNewsContent(e.target.value)}
                      />
                    </div>

                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button type="submit" className="btn btn-primary">
                        {isEditingNews ? 'Cập nhật' : 'Đăng bài'}
                      </button>
                      {isEditingNews && (
                        <button type="button" className="btn btn-secondary" onClick={resetNewsForm}>
                          Hủy chỉnh sửa
                        </button>
                      )}
                    </div>
                  </form>
                </div>

                {/* News Table */}
                <div className="admin-card" style={{ overflowX: 'auto' }}>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '20px' }}>Danh sách bài viết đã đăng</h3>
                  {news.length === 0 ? (
                    <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '20px' }}>Chưa có bài viết nào.</p>
                  ) : (
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Tiêu đề</th>
                          <th>Danh mục</th>
                          <th>Ngày đăng</th>
                          <th style={{ textAlign: 'right' }}>Thao tác</th>
                        </tr>
                      </thead>
                      <tbody>
                        {news.map((item) => (
                          <tr key={item.id}>
                            <td style={{ fontWeight: 600, maxWidth: '350px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.title}</td>
                            <td><span className="badge badge-primary">{item.category}</span></td>
                            <td style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{new Date(item.date).toLocaleDateString('vi-VN')}</td>
                            <td style={{ textAlign: 'right' }}>
                              <div className="action-buttons" style={{ justifyContent: 'flex-end' }}>
                                <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => handleEditNews(item)}>
                                  Sửa
                                </button>
                                <button className="btn btn-danger" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => handleDeleteNews(item.id)}>
                                  Xóa
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            )}

            {/* Tab: QA */}
            {activeTab === 'qa' && (
              <div>
                {/* Form Add/Edit */}
                <div className="admin-card">
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '20px' }}>
                    {isEditingQa ? '📝 Chỉnh sửa câu hỏi Q&A' : '➕ Thêm câu hỏi Q&A mới'}
                  </h3>

                  <form onSubmit={handleSaveQa} className="admin-form">
                    <div className="form-group">
                      <label className="form-label">Câu hỏi (User hỏi) <span>*</span></label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Ví dụ: Hộ kinh doanh có được miễn thuế môn bài không?"
                        value={qaQuestion}
                        onChange={(e) => setQaQuestion(e.target.value)}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Câu trả lời mẫu (Chatbot học) <span>*</span></label>
                      <textarea
                        className="form-control form-textarea"
                        placeholder="Nội dung câu trả lời đầy đủ và chính xác về quy định thuế..."
                        value={qaAnswer}
                        onChange={(e) => setQaAnswer(e.target.value)}
                      />
                    </div>

                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button type="submit" className="btn btn-primary">
                        {isEditingQa ? 'Cập nhật' : 'Thêm mới'}
                      </button>
                      {isEditingQa && (
                        <button type="button" className="btn btn-secondary" onClick={resetQaForm}>
                          Hủy chỉnh sửa
                        </button>
                      )}
                    </div>
                  </form>
                </div>

                {/* Q&A Table */}
                <div className="admin-card" style={{ overflowX: 'auto' }}>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '20px' }}>Danh sách câu hỏi/đáp đã nạp</h3>
                  {qas.length === 0 ? (
                    <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '20px' }}>Chưa có cặp câu hỏi/đáp nào.</p>
                  ) : (
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th style={{ width: '40%' }}>Câu hỏi</th>
                          <th style={{ width: '45%' }}>Câu trả lời</th>
                          <th style={{ textAlign: 'right' }}>Thao tác</th>
                        </tr>
                      </thead>
                      <tbody>
                        {qas.map((item) => (
                          <tr key={item.id}>
                            <td style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.question}</td>
                            <td style={{ fontSize: '0.9rem', color: 'var(--muted)', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.answer}</td>
                            <td style={{ textAlign: 'right' }}>
                              <div className="action-buttons" style={{ justifyContent: 'flex-end' }}>
                                <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => handleEditQa(item)}>
                                  Sửa
                                </button>
                                <button className="btn btn-danger" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => handleDeleteQa(item.id)}>
                                  Xóa
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            )}

            {/* Tab: PDF */}
            {activeTab === 'pdf' && (
              <div>
                {/* PDF Upload zone */}
                <div className="admin-card">
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '20px' }}>Upload tài liệu thuế mới (Định dạng PDF)</h3>
                  
                  <form onSubmit={handleUploadPdf} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div className="upload-zone" onClick={() => document.getElementById('pdf-file-input').click()}>
                      <div className="upload-zone-icon">📥</div>
                      <p style={{ fontWeight: 700, margin: '0 0 4px 0' }}>
                        {selectedFile ? `Đã chọn: ${selectedFile.name}` : 'Nhấp chuột vào đây để chọn file PDF tài liệu'}
                      </p>
                      <p style={{ color: 'var(--muted)', fontSize: '0.8rem', margin: 0 }}>
                        {selectedFile ? `Kích thước: ${formatSize(selectedFile.size)}` : 'Chỉ hỗ trợ file định dạng .pdf'}
                      </p>
                      <input
                        type="file"
                        id="pdf-file-input"
                        accept=".pdf"
                        style={{ display: 'none' }}
                        onChange={(e) => setSelectedFile(e.target.files[0] || null)}
                      />
                    </div>

                    {uploadMessage && (
                      <p style={{ 
                        margin: 0, 
                        fontSize: '0.9rem', 
                        color: uploadMessage.startsWith('❌') ? 'var(--error)' : 'var(--success)',
                        fontWeight: 600
                      }}>
                        {uploadMessage}
                      </p>
                    )}

                    <div>
                      <button 
                        type="submit" 
                        className="btn btn-primary" 
                        disabled={!selectedFile || isUploadingPdf}
                        style={{ display: 'flex', gap: '8px', alignItems: 'center' }}
                      >
                        {isUploadingPdf ? 'Đang tải lên...' : '🚀 Tải lên tài liệu và huấn luyện AI'}
                      </button>
                    </div>
                  </form>
                </div>

                {/* PDF Documents Table */}
                <div className="admin-card" style={{ overflowX: 'auto' }}>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '20px' }}>Danh sách tài liệu đã học</h3>
                  {pdfs.length === 0 ? (
                    <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '20px' }}>Chưa có tài liệu PDF nào.</p>
                  ) : (
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Tên tài liệu</th>
                          <th>Dung lượng</th>
                          <th>Ngày tải lên</th>
                          <th style={{ textAlign: 'right' }}>Thao tác</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pdfs.map((item) => (
                          <tr key={item.id}>
                            <td style={{ fontWeight: 600 }}>📄 {item.name}</td>
                            <td style={{ fontSize: '0.85rem' }}>{formatSize(item.size)}</td>
                            <td style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{new Date(item.uploadDate).toLocaleDateString('vi-VN')}</td>
                            <td style={{ textAlign: 'right' }}>
                              <button className="btn btn-danger" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => handleDeletePdf(item.id)}>
                                Xóa tài liệu
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
