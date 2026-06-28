import { NextResponse } from 'next/server';
import { getNews, createNews, updateNews, deleteNews } from '@/lib/db';

export async function GET() {
  try {
    const news = getNews();
    return NextResponse.json(news);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const { title, summary, content, category } = await request.json();
    if (!title || !content || !category) {
      return NextResponse.json({ error: 'Thiếu thông tin bắt buộc (Tiêu đề, Nội dung, Danh mục)' }, { status: 400 });
    }
    const newItem = createNews({ title, summary, content, category });
    return NextResponse.json(newItem, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function PUT(request) {
  try {
    const { id, title, summary, content, category } = await request.json();
    if (!id) {
      return NextResponse.json({ error: 'Thiếu ID bài viết cần cập nhật' }, { status: 400 });
    }
    const updated = updateNews(id, { title, summary, content, category });
    if (!updated) {
      return NextResponse.json({ error: 'Không tìm thấy bài viết' }, { status: 404 });
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
      return NextResponse.json({ error: 'Thiếu ID bài viết cần xóa' }, { status: 400 });
    }
    const deleted = deleteNews(id);
    if (!deleted) {
      return NextResponse.json({ error: 'Không tìm thấy bài viết' }, { status: 404 });
    }
    return NextResponse.json({ success: true, deleted });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
