import { NextResponse } from 'next/server';
import { askTaxChatbot } from '@/lib/gemini';

export async function POST(request) {
  try {
    const { message, history } = await request.json();
    
    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'Nội dung tin nhắn không hợp lệ' }, { status: 400 });
    }

    const response = await askTaxChatbot(message, history || []);
    return NextResponse.json(response);
  } catch (error) {
    console.error('Error in chat API route:', error);
    return NextResponse.json(
      { error: `Đã xảy ra lỗi khi xử lý tin nhắn: ${error.message || error}` },
      { status: 500 }
    );
  }
}
