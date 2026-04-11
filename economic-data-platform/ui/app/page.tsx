'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useReports } from '@/components/providers/reports-provider'
import { ReportsFilters, FilterState } from '@/components/reports/reports-filters'
import { ReportsTable } from '@/components/reports/reports-table'
import { Button } from '@/components/ui/button'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Plus } from 'lucide-react'

export default function Dashboard() {
  const router = useRouter()
  const { reports, deleteReport } = useReports()
  const [filters, setFilters] = useState<FilterState>({ search: '' })
  const [deleteId, setDeleteId] = useState<string | number | null>(null)

  const handleDelete = async (id: string | number) => {
    setDeleteId(id)
  }

  const confirmDelete = async () => {
    if (deleteId !== null) {
      await deleteReport(deleteId)
      setDeleteId(null)
    }
  }

  return (
    <div className="w-full h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Báo cáo định kỳ</h1>
            <p className="text-sm text-gray-600 mt-1">Quản lý và theo dõi các báo cáo của bạn</p>
          </div>
          <Button
            className="bg-green-600 hover:bg-green-700 text-white"
            onClick={() => router.push('/reports/create')}
          >
            <Plus size={18} className="mr-2" />
            Tạo báo cáo mới
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-8 space-y-6">
          {/* Filters */}
          <ReportsFilters
            onFilterChange={setFilters}
            onCreateNew={() => router.push('/reports/create')}
          />

          {/* Table */}
          <ReportsTable
            reports={reports}
            onDelete={handleDelete}
            filters={filters}
          />
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteId !== null} onOpenChange={open => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogTitle>Xóa báo cáo?</AlertDialogTitle>
          <AlertDialogDescription>
            Bạn có chắc chắn muốn xóa báo cáo này? Hành động này không thể được hoàn tác.
          </AlertDialogDescription>
          <div className="flex gap-3 justify-end">
            <AlertDialogCancel onClick={() => setDeleteId(null)}>Hủy</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-red-600 hover:bg-red-700">
              Xóa
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
