import { NextResponse } from 'next/server';
import { getTableList } from '@/lib/db';

export async function GET() {
  try {
    const tables = await getTableList();
    return NextResponse.json(tables);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch tables' }, { status: 500 });
  }
}
