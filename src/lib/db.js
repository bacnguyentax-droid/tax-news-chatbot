import fs from 'fs';
import path from 'path';

const DB_DIR = path.join(process.cwd(), 'data');
const DB_FILE = path.join(process.cwd(), 'data', 'db.json');
const UPLOAD_DIR = path.join(process.cwd(), 'data', 'uploads');

// Ensure database and upload folders exist
function initDb() {
  if (!fs.existsSync(DB_DIR)) {
    fs.mkdirSync(DB_DIR, { recursive: true });
  }
  if (!fs.existsSync(UPLOAD_DIR)) {
    fs.mkdirSync(UPLOAD_DIR, { recursive: true });
  }
  if (!fs.existsSync(DB_FILE)) {
    const initialData = {
      news: [
        {
          id: 'news-1',
          title: 'Hướng dẫn nộp Lệ phí môn bài năm 2026 cho hộ kinh doanh mới',
          summary: 'Chi tiết về mức đóng lệ phí môn bài và thời hạn nộp dành cho các hộ kinh doanh cá thể thành lập mới trong năm 2026.',
          content: `## Quy định về Lệ phí môn bài năm 2026

Hộ kinh doanh mới thành lập cần lưu ý các quy định sau đây về Lệ phí môn bài (trước đây gọi là Thuế môn bài):

### 1. Mức nộp lệ phí môn bài
Theo Nghị định 139/2016/NĐ-CP và các văn bản sửa đổi, mức đóng lệ phí môn bài đối với hộ gia đình, cá nhân, nhóm cá nhân hoạt động sản xuất, kinh doanh như sau:
- **Doanh thu trên 500 triệu đồng/năm**: 1.000.000 đồng/năm.
- **Doanh thu từ trên 300 triệu đến 500 triệu đồng/năm**: 500.000 đồng/năm.
- **Doanh thu từ trên 100 triệu đến 300 triệu đồng/năm**: 300.000 đồng/năm.
- **Doanh thu từ 100 triệu đồng/năm trở xuống**: Miễn lệ phí môn bài.

### 2. Miễn lệ phí môn bài năm đầu tiên
Hộ kinh doanh, cá nhân hoạt động sản xuất, kinh doanh mới thành lập hoặc ra hoạt động sản xuất, kinh doanh lần đầu được **miễn lệ phí môn bài trong năm đầu tiên** thành lập hoặc ra hoạt động sản xuất, kinh doanh (từ ngày 01 tháng 01 đến ngày 31 tháng 12).

### 3. Thời hạn nộp hồ sơ và tiền lệ phí môn bài
- **Thời hạn nộp lệ phí môn bài**: Chậm nhất là ngày 30 tháng 01 hàng năm.
- Đối với hộ kinh doanh mới thành lập được miễn năm đầu thì thời hạn nộp tờ khai và lệ phí (nếu có phát sinh quy mô doanh thu thay đổi) của năm tiếp theo là ngày 30/01 của năm tiếp theo.
- Hãy chắc chắn bạn nộp đúng hạn để tránh bị phạt chậm nộp theo quy định pháp luật thuế hiện hành.`,
          category: 'Lệ phí môn bài',
          date: '2026-06-25T08:00:00.000Z'
        },
        {
          id: 'news-2',
          title: 'Thuế khoán hộ kinh doanh: Cách tính và thủ tục kê khai mới nhất',
          summary: 'Tìm hiểu về thuế khoán, cách cơ quan thuế xác định mức doanh thu khoán và quy trình kê khai thuế định kỳ hàng năm.',
          content: `## Thuế khoán là gì?

Thuế khoán là phương pháp tính thuế theo tỷ lệ trên doanh thu khoán do cơ quan thuế xác định để tính mức thuế giá trị gia tăng (GTGT) và thuế thu nhập cá nhân (TNCN) phải nộp đối với hộ kinh doanh, cá nhân kinh doanh không thực hiện chế độ kế toán, hóa đơn, chứng từ.

### 1. Cách tính thuế khoán
Số thuế GTGT và TNCN phải nộp được tính như sau:
- **Thuế GTGT phải nộp** = Doanh thu tính thuế GTGT x Tỷ lệ thuế GTGT
- **Thuế TNCN phải nộp** = Doanh thu tính thuế TNCN x Tỷ lệ thuế TNCN

### 2. Tỷ lệ thuế tính trên doanh thu
Tỷ lệ thuế tính trên doanh thu được quy định khác nhau tùy theo ngành nghề kinh doanh:
- **Phân phối, cung cấp hàng hóa**: GTGT 1% - TNCN 0.5% (Tổng 1.5%)
- **Dịch vụ, xây dựng không bao thầu nguyên vật liệu**: GTGT 5% - TNCN 2% (Tổng 7%)
- **Sản xuất, vận tải, dịch vụ có gắn với hàng hóa, xây dựng có bao thầu nguyên vật liệu**: GTGT 3% - TNCN 1.5% (Tổng 4.5%)
- **Hoạt động kinh doanh khác**: GTGT 2% - TNCN 1% (Tổng 3%)

### 3. Thủ tục và thời hạn kê khai
- Hộ kinh doanh nộp thuế khoán thực hiện khai thuế khoán ổn định 01 lần/năm theo Mẫu số 01/CNKD ban hành kèm theo Thông tư 40/2021/TT-BTC.
- **Thời hạn nộp tờ khai**: Chậm nhất là ngày 15 tháng 12 của năm trước năm tính thuế. Đối với hộ kinh doanh mới ra kinh doanh thì thời hạn nộp hồ sơ khai thuế chậm nhất là ngày thứ 10 kể từ ngày bắt đầu kinh doanh.`,
          category: 'Thuế khoán',
          date: '2026-06-20T09:30:00.000Z'
        }
      ],
      qas: [
        {
          id: 'qa-1',
          question: 'Doanh thu dưới 100 triệu một năm có phải nộp thuế không?',
          answer: 'Theo quy định hiện hành tại Thông tư 40/2021/TT-BTC, hộ kinh doanh, cá nhân kinh doanh có doanh thu từ hoạt động sản xuất, kinh doanh trong năm dương lịch từ 100 triệu đồng trở xuống thì thuộc trường hợp không phải nộp thuế GTGT và không phải nộp thuế TNCN.',
          date: '2026-06-28T09:00:00.000Z'
        },
        {
          id: 'qa-2',
          question: 'Hạn chót nộp tờ khai thuế khoán hàng năm là khi nào?',
          answer: 'Thời hạn nộp hồ sơ khai thuế khoán đối với hộ kinh doanh nộp thuế khoán ổn định từ đầu năm là chậm nhất là ngày 15 tháng 12 của năm trước năm tính thuế. Trường hợp hộ kinh doanh mới ra kinh doanh trong năm thì thời hạn là chậm nhất là ngày thứ 10 kể từ ngày bắt đầu hoạt động.',
          date: '2026-06-28T09:05:00.000Z'
        }
      ],
      pdfs: []
    };
    fs.writeFileSync(DB_FILE, JSON.stringify(initialData, null, 2), 'utf8');
  }
}

export function getDb() {
  initDb();
  const data = fs.readFileSync(DB_FILE, 'utf8');
  return JSON.parse(data);
}

export function saveDb(data) {
  initDb();
  fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), 'utf8');
}

// News CRUD
export function getNews() {
  const db = getDb();
  return db.news.sort((a, b) => new Date(b.date) - new Date(a.date));
}

export function getNewsById(id) {
  const db = getDb();
  return db.news.find(item => item.id === id);
}

export function createNews(item) {
  const db = getDb();
  const newItem = {
    id: `news-${Date.now()}`,
    date: new Date().toISOString(),
    ...item
  };
  db.news.push(newItem);
  saveDb(db);
  return newItem;
}

export function updateNews(id, updatedFields) {
  const db = getDb();
  const index = db.news.findIndex(item => item.id === id);
  if (index !== -1) {
    db.news[index] = { ...db.news[index], ...updatedFields };
    saveDb(db);
    return db.news[index];
  }
  return null;
}

export function deleteNews(id) {
  const db = getDb();
  const index = db.news.findIndex(item => item.id === id);
  if (index !== -1) {
    const deleted = db.news.splice(index, 1);
    saveDb(db);
    return deleted[0];
  }
  return null;
}

// Q&As CRUD
export function getQas() {
  const db = getDb();
  return db.qas.sort((a, b) => new Date(b.date) - new Date(a.date));
}

export function createQa(item) {
  const db = getDb();
  const newItem = {
    id: `qa-${Date.now()}`,
    date: new Date().toISOString(),
    ...item
  };
  db.qas.push(newItem);
  saveDb(db);
  return newItem;
}

export function updateQa(id, updatedFields) {
  const db = getDb();
  const index = db.qas.findIndex(item => item.id === id);
  if (index !== -1) {
    db.qas[index] = { ...db.qas[index], ...updatedFields };
    saveDb(db);
    return db.qas[index];
  }
  return null;
}

export function deleteQa(id) {
  const db = getDb();
  const index = db.qas.findIndex(item => item.id === id);
  if (index !== -1) {
    const deleted = db.qas.splice(index, 1);
    saveDb(db);
    return deleted[0];
  }
  return null;
}

// PDFs CRUD
export function getPdfs() {
  const db = getDb();
  return db.pdfs.sort((a, b) => new Date(b.uploadDate) - new Date(a.uploadDate));
}

export function createPdf(pdfMetadata) {
  const db = getDb();
  const newPdf = {
    id: `pdf-${Date.now()}`,
    uploadDate: new Date().toISOString(),
    ...pdfMetadata
  };
  db.pdfs.push(newPdf);
  saveDb(db);
  return newPdf;
}

export function deletePdf(id) {
  const db = getDb();
  const index = db.pdfs.findIndex(item => item.id === id);
  if (index !== -1) {
    const pdf = db.pdfs[index];
    // Remove the physical file if it exists
    if (pdf.filePath) {
      const fullPath = path.join(process.cwd(), pdf.filePath);
      if (fs.existsSync(fullPath)) {
        try {
          fs.unlinkSync(fullPath);
        } catch (err) {
          console.error(`Failed to delete physical file: ${fullPath}`, err);
        }
      }
    }
    const deleted = db.pdfs.splice(index, 1);
    saveDb(db);
    return deleted[0];
  }
  return null;
}

export { UPLOAD_DIR };
