'use client'

import { use } from 'react'
import Link from 'next/link'
import { useReports } from '@/components/providers/reports-provider'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Edit2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { useRouter } from 'next/navigation'

export default function ReportDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const { getReport, deleteReport } = useReports()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const report = getReport(id)

  if (!report) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Báo cáo không tìm thấy</h1>
          <p className="text-gray-600 mt-2">Báo cáo bạn tìm kiếm không tồn tại.</p>
          <Link href="/">
            <Button className="mt-4">
              <ArrowLeft size={16} className="mr-2" />
              Quay lại
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  const handleDelete = async () => {
    await deleteReport(id)
    router.push('/')
  }

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'inactive':
        return 'bg-gray-100 text-gray-800'
      case 'draft':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getScheduleLabel = (schedule: string) => {
    const schedules: Record<string, string> = {
      once: 'Một lần',
      daily: 'Hàng ngày',
      weekly: 'Hàng tuần',
      monthly: 'Hàng tháng',
    }
    return schedules[schedule] || schedule
  }

  return (
    <div className="w-full min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Link href="/">
                <Button variant="ghost" size="sm" className="p-0 h-auto">
                  <ArrowLeft size={18} />
                </Button>
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">{report.title}</h1>
            </div>
            <p className="text-sm text-gray-600">ID: {report.id}</p>
          </div>
          <div className="flex gap-2">
            <Link href={`/reports/${report.id}/edit`}>
              <Button className="bg-green-600 hover:bg-green-700 text-white">
                <Edit2 size={16} className="mr-2" />
                Chỉnh sửa
              </Button>
            </Link>
            <Button
              variant="outline"
              className="border-red-300 text-red-600 hover:bg-red-50"
              onClick={() => setShowDeleteDialog(true)}
            >
              <Trash2 size={16} className="mr-2" />
              Xóa
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-8 max-w-4xl mx-auto">
          {/* Basic Info */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Thông tin cơ bản</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-1">Mô tả</p>
                <p className="text-gray-900">{report.description || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Trạng thái</p>
                <Badge className={getStatusColor(report.status)}>
                  {report.status === 'active' ? 'Hoạt động' : report.status === 'draft' ? 'Nháp' : 'Không hoạt động'}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Người tạo</p>
                <p className="text-gray-900">{report.creator}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Chủ sở hữu</p>
                <p className="text-gray-900">{report.owner}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Người nhận</p>
                <p className="text-gray-900">{report.recipient}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Tần suất</p>
                <p className="text-gray-900">{getScheduleLabel(report.schedule)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Ngày tạo</p>
                <p className="text-gray-900">{formatDate(report.createdAt)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Nhóm</p>
                <p className="text-gray-900">{report.group || '-'}</p>
              </div>
            </div>
          </div>

          {/* Schedule Info */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Lịch trình</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-1">Lần chạy cuối cùng</p>
                <p className="text-gray-900">{report.lastSentAt ? formatDate(report.lastSentAt) : '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Lần chạy tiếp theo</p>
                <p className="text-gray-900">{report.nextSendAt ? formatDate(report.nextSendAt) : '-'}</p>
              </div>
            </div>
          </div>

          {/* Tags */}
          {report.tags.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Tags</h2>
              <div className="flex flex-wrap gap-2">
                {report.tags.map(tag => (
                  <Badge key={tag} className="bg-green-100 text-green-700">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Advanced Config */}
          {(report.loaiForm || report.connector || report.queue || report.sqlTemplate) && (
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Cấu hình nâng cao</h2>
              <div className="space-y-4">
                {report.loaiForm && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Loại Form</p>
                    <p className="text-gray-900">{report.loaiForm}</p>
                  </div>
                )}
                {report.connector && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Connector</p>
                    <p className="text-gray-900">{report.connector}</p>
                  </div>
                )}
                {report.queue && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Queue</p>
                    <p className="text-gray-900">{report.queue}</p>
                  </div>
                )}
                {report.sqlTemplate && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">SQL Template</p>
                    <pre className="bg-gray-50 p-3 rounded border border-gray-200 text-sm overflow-x-auto">
                      <code>{report.sqlTemplate}</code>
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Notes */}
          {report.notes && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Ghi chú</h2>
              <p className="text-gray-900 whitespace-pre-wrap">{report.notes}</p>
            </div>
          )}
        </div>
      </div>

      {/* Delete Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogTitle>Xóa báo cáo?</AlertDialogTitle>
          <AlertDialogDescription>
            Bạn có chắc chắn muốn xóa báo cáo "{report.title}"? Hành động này không thể được hoàn tác.
          </AlertDialogDescription>
          <div className="flex gap-3 justify-end">
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
              Xóa
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
