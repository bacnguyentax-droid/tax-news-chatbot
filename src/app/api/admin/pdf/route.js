import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
// Mock browser globals for pdf-parse in Node.js server environment during compilation
if (typeof global.DOMMatrix === 'undefined') {
  global.DOMMatrix = class DOMMatrix {};
}
if (typeof global.ImageData === 'undefined') {
  global.ImageData = class ImageData {};
}
if (typeof global.Path2D === 'undefined') {
  global.Path2D = class Path2D {};
}

// Preload the legacy worker to prevent PDF.js dynamic imports during execution
import * as pdfjsWorker from 'pdfjs-dist/legacy/build/pdf.worker.mjs';
globalThis.pdfjsWorker = pdfjsWorker;

import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pdfParse = require('pdf-parse');
import { getPdfs, createPdf, deletePdf, UPLOAD_DIR } from '@/lib/db';

export async function GET() {
  try {
    const pdfs = getPdfs();
    // Return PDFs metadata, but omit the huge parsedText to save bandwidth
    const sanitizedPdfs = pdfs.map(({ parsedText, ...rest }) => rest);
    return NextResponse.json(sanitizedPdfs);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');
    
    if (!file || !(file instanceof File)) {
      return NextResponse.json({ error: 'Không tìm thấy file tải lên hoặc định dạng không đúng' }, { status: 400 });
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return NextResponse.json({ error: 'Chỉ chấp nhận file định dạng PDF' }, { status: 400 });
    }

    // Read file bytes
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // Parse PDF text content
    let parsedText = '';
    try {
      const parser = new pdfParse.PDFParse({ data: buffer });
      const pdfData = await parser.getText();
      parsedText = pdfData.text || '';
    } catch (parseError) {
      console.error('Error parsing PDF content:', parseError);
      return NextResponse.json({ error: `Không thể trích xuất văn bản từ PDF: ${parseError.message}` }, { status: 500 });
    }

    // Save physical file to upload directory
    const fileName = `${Date.now()}-${file.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`;
    const filePath = path.join(UPLOAD_DIR, fileName);
    fs.writeFileSync(filePath, buffer);

    // Save metadata in JSON DB
    const relativeFilePath = path.relative(process.cwd(), filePath).replace(/\\/g, '/');
    const pdfMetadata = createPdf({
      name: file.name,
      size: file.size,
      filePath: relativeFilePath,
      parsedText: parsedText,
    });

    // Return the created metadata without parsedText
    const { parsedText: _, ...responseMetadata } = pdfMetadata;
    return NextResponse.json(responseMetadata, { status: 201 });
  } catch (error) {
    console.error('Error uploading PDF:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function DELETE(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    if (!id) {
      return NextResponse.json({ error: 'Thiếu ID tài liệu cần xóa' }, { status: 400 });
    }
    const deleted = deletePdf(id);
    if (!deleted) {
      return NextResponse.json({ error: 'Không tìm thấy tài liệu trong cơ sở dữ liệu' }, { status: 404 });
    }
    return NextResponse.json({ success: true, deletedName: deleted.name });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
