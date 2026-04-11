'use client'

import { CreateReportForm } from '@/components/reports/create-report-form'

export default function CreateReportPage() {
  return (
    <div className="w-full min-h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tạo báo cáo mới</h1>
          <p className="text-sm text-gray-600 mt-1">Điền thông tin và cấu hình báo cáo của bạn</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        <CreateReportForm />
      </div>
    </div>
  )
}
