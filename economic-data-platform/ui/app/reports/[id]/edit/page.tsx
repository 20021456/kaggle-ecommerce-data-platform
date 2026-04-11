'use client'

import { use } from 'react'
import { useReports } from '@/components/providers/reports-provider'
import { CreateReportForm } from '@/components/reports/create-report-form'
import { CreateReportInput } from '@/lib/schemas'

export default function EditReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { getReport } = useReports()
  const report = getReport(id)

  if (!report) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Báo cáo không tìm thấy</h1>
          <p className="text-gray-600 mt-2">Báo cáo bạn tìm kiếm không tồn tại.</p>
        </div>
      </div>
    )
  }

  const reportData: CreateReportInput = {
    title: report.title,
    description: report.description,
    creator: report.creator,
    owner: report.owner,
    recipient: report.recipient,
    schedule: report.schedule,
    status: report.status,
    tags: report.tags,
    group: report.group,
    sqlTemplate: report.sqlTemplate,
    loaiForm: report.loaiForm,
    chiBieuDon: report.chiBieuDon,
    connector: report.connector,
    queue: report.queue,
    notes: report.notes,
  }

  return (
    <div className="w-full min-h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chỉnh sửa báo cáo</h1>
          <p className="text-sm text-gray-600 mt-1">{report.title}</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        <CreateReportForm initialData={reportData} />
      </div>
    </div>
  )
}
