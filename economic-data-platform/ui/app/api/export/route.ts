import { NextResponse } from 'next/server';
import { getTableData } from '@/lib/db';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const schema = searchParams.get('schema');
  const table = searchParams.get('table');
  const format = searchParams.get('format') || 'json';

  if (!schema || !table) {
    return NextResponse.json({ error: 'Schema and table required' }, { status: 400 });
  }

  try {
    const data = await getTableData(schema, table, 1000);

    if (format === 'csv') {
      const csv = convertToCSV(data);
      return new NextResponse(csv, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename="${schema}_${table}.csv"`,
        },
      });
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Export failed' }, { status: 500 });
  }
}

function convertToCSV(data: any[]) {
  if (!data.length) return '';
  const headers = Object.keys(data[0]);
  const rows = data.map(row => headers.map(h => JSON.stringify(row[h] ?? '')).join(','));
  return [headers.join(','), ...rows].join('\n');
}
