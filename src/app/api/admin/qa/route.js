import { NextResponse } from 'next/server';
import { getQas, createQa, updateQa, deleteQa } from '@/lib/db';

export async function GET() {
  try {
    const qas = getQas();
    return NextResponse.json(qas);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const { question, answer } = await request.json();
    if (!question || !answer) {
      return NextResponse.json({ error: 'Thiếu thông tin bắt buộc (Câu hỏi, Câu trả lời)' }, { status: 400 });
    }
    const newItem = createQa({ question, answer });
    return NextResponse.json(newItem, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function PUT(request) {
  try {
    const { id, question, answer } = await request.json();
    if (!id) {
      return NextResponse.json({ error: 'Thiếu ID câu hỏi cần cập nhật' }, { status: 400 });
    }
    const updated = updateQa(id, { question, answer });
    if (!updated) {
      return NextResponse.json({ error: 'Không tìm thấy câu hỏi' }, { status: 404 });
    }
    return NextResponse.json(updated);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function DELETE(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    if (!id) {
      return NextResponse.json({ error: 'Thiếu ID câu hỏi cần xóa' }, { status: 400 });
    }
    const deleted = deleteQa(id);
    if (!deleted) {
      return NextResponse.json({ error: 'Không tìm thấy câu hỏi' }, { status: 404 });
    }
    return NextResponse.json({ success: true, deleted });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
