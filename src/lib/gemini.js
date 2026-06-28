import { GoogleGenerativeAI } from '@google/generative-ai';
import { getQas, getPdfs } from './db.js';

// Get API Key from environment variables
const apiKey = process.env.GEMINI_API_KEY;

// Check if Gemini API Key is configured
export function isGeminiConfigured() {
  return typeof apiKey === 'string' && apiKey.length > 0;
}

// Initialise Gemini client
const genAI = isGeminiConfigured() ? new GoogleGenerativeAI(apiKey) : null;

// Default fallback response
export const FALLBACK_RESPONSE = 'Tôi không tìm thấy thông tin này trong tài liệu hướng dẫn về thuế. Vui lòng hỏi câu hỏi khác hoặc liên hệ cơ quan thuế.';

/**
 * Send a chat query to Gemini, applying context from PDFs and Q&As
 * @param {string} userQuestion - The user's query
 * @param {Array} chatHistory - Previous messages: [{ role: 'user'|'model', parts: [{ text: '...' }] }]
 */
export async function askTaxChatbot(userQuestion, chatHistory = []) {
  if (!isGeminiConfigured()) {
    return {
      text: '⚠️ Hệ thống chưa được cấu hình API Key cho Gemini. Vui lòng cấu hình `GEMINI_API_KEY` trong file `.env.local` ở thư mục gốc.',
      sources: []
    };
  }

  try {
    // 1. Gather all documents (PDFs & Q&As)
    const qas = getQas();
    const pdfs = getPdfs();

    // 2. Format Context
    let contextText = 'Dưới đây là tài liệu hướng dẫn về thuế cho hộ kinh doanh:\n\n';
    
    contextText += '=== DANH SÁCH HỎI ĐÁP CỐ ĐỊNH (Q&As) ===\n';
    qas.forEach((qa, idx) => {
      contextText += `Hỏi đáp ${idx + 1}:\n- Câu hỏi: ${qa.question}\n- Câu trả lời: ${qa.answer}\n\n`;
    });

    contextText += '=== TÀI LIỆU VĂN BẢN PDF ĐÃ ĐĂNG TẢI ===\n';
    const activePdfs = pdfs.filter(pdf => pdf.parsedText);
    
    if (activePdfs.length === 0) {
      contextText += '(Chưa có tài liệu PDF nào được tải lên hoặc phân tích)\n';
    } else {
      activePdfs.forEach((pdf) => {
        contextText += `Tên tài liệu: "${pdf.name}"\nNội dung chi tiết:\n${pdf.parsedText}\n=========================================\n\n`;
      });
    }

    // 3. System instructions
    const systemInstruction = `Bạn là một trợ lý ảo chuyên nghiệp về Thuế dành cho Hộ kinh doanh cá thể tại Việt Nam.
Nhiệm vụ của bạn là trả lời các câu hỏi của người dùng một cách chính xác, lịch sự và rõ ràng.

Quy tắc nghiêm ngặt:
1. Bạn CHỈ ĐƯỢC PHÉP trả lời dựa trên thông tin có sẵn trong tài liệu ngữ cảnh (Context) được cung cấp dưới đây. Không sử dụng bất kỳ kiến thức bên ngoài nào.
2. Nếu câu hỏi không liên quan đến thuế hộ kinh doanh hoặc KHÔNG thể tìm thấy câu trả lời trong dữ liệu Context được cung cấp, bạn BẮT BUỘC phải trả lời chính xác là:
"${FALLBACK_RESPONSE}"
Không được thêm bớt từ ngữ, không được chế tạo câu trả lời khác, không được tự suy diễn từ kiến thức chung của bạn.
3. Khi trả lời, hãy trích dẫn nguồn tài liệu nếu thông tin lấy từ tài liệu PDF hoặc Q&A cụ thể. Định dạng nguồn trích dẫn là: "[Nguồn: Tên_tài_liệu_PDF_hoặc_Q&A]" ở cuối câu trả lời.
4. Trả lời bằng tiếng Việt, trình bày đẹp mắt dưới dạng markdown (dùng bullet points, in đậm các ý chính, hoặc bảng nếu thích hợp để thông tin dễ đọc).

Bối cảnh tài liệu (Context):
---------------------
${contextText}
---------------------
`;

    // 4. Connect to Gemini Model
    // We use gemini-2.5-flash as default because of its massive context window and fast response time.
    const model = genAI.getGenerativeModel({
      model: 'gemini-2.5-flash',
      systemInstruction: systemInstruction,
    });

    // 5. Setup safety settings and generation configuration
    const generationConfig = {
      temperature: 0.1, // Low temperature to force strict adherence to the context and discourage creativity
      topP: 0.95,
      topK: 40,
      maxOutputTokens: 2048,
    };

    // Filter and format history correctly
    // The Gemini SDK expects: [{ role: 'user' | 'model', parts: [{ text: string }] }]
    const formattedHistory = chatHistory
      .filter(msg => msg.role === 'user' || msg.role === 'model')
      .map(msg => ({
        role: msg.role,
        parts: [{ text: msg.content || msg.text || '' }]
      }));

    // Start chat session with formatted history
    const chat = model.startChat({
      history: formattedHistory,
      generationConfig,
    });

    // Send question
    const result = await chat.sendMessage(userQuestion);
    const response = await result.response;
    const responseText = response.text().trim();

    // 6. Deduce sources used
    const sources = [];
    activePdfs.forEach(pdf => {
      if (responseText.includes(pdf.name)) {
        sources.push({ type: 'pdf', name: pdf.name });
      }
    });

    return {
      text: responseText,
      sources: sources
    };
  } catch (error) {
    console.error('Error calling Gemini API:', error);
    return {
      text: `❌ Lỗi khi kết nối với mô hình AI Gemini: ${error.message || error}`,
      sources: []
    };
  }
}
