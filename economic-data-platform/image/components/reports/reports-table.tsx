'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { Report } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { Search, MoreHorizontal, Edit2, Trash2, Eye, ChevronLeft, ChevronRight } from 'lucide-react'

interface ReportsTableProps {
  reports: Report[]
  onDelete: (id: string | number) => void
  filters: {
    search: string
    status?: string
    tags?: string[]
  }
}

const ITEMS_PER_PAGE = 5

export function ReportsTable({ reports, onDelete, filters }: ReportsTableProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [sortBy, setSortBy] = useState<keyof Report>('createdAt')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const filteredReports = useMemo(() => {
    return reports.filter(report => {
      const matchesSearch =
        filters.search === '' ||
        report.title.toLowerCase().includes(filters.search.toLowerCase()) ||
        report.description?.toLowerCase().includes(filters.search.toLowerCase()) ||
        report.creator.toLowerCase().includes(filters.search.toLowerCase())

      const matchesStatus =
        !filters.status || filters.status === 'all' || report.status === filters.status

      const matchesTags =
        !filters.tags || filters.tags.length === 0 || filters.tags.some(tag => report.tags.includes(tag))

      return matchesSearch && matchesStatus && matchesTags
    })
  }, [reports, filters])

  const sortedReports = useMemo(() => {
    const sorted = [...filteredReports].sort((a, b) => {
      const aVal = a[sortBy]
      const bVal = b[sortBy]

      if (aVal instanceof Date && bVal instanceof Date) {
        return sortOrder === 'asc' ? aVal.getTime() - bVal.getTime() : bVal.getTime() - aVal.getTime()
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }

      return 0
    })

    return sorted
  }, [filteredReports, sortBy, sortOrder])

  const paginatedReports = useMemo(() => {
    const startIdx = (currentPage - 1) * ITEMS_PER_PAGE
    return sortedReports.slice(startIdx, startIdx + ITEMS_PER_PAGE)
  }, [sortedReports, currentPage])

  const totalPages = Math.ceil(sortedReports.length / ITEMS_PER_PAGE)

  const handleSort = (column: keyof Report) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
    setCurrentPage(1)
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

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <Table>
          <TableHeader className="bg-gray-50">
            <TableRow>
              <TableHead
                className="cursor-pointer hover:bg-gray-100 text-xs font-semibold"
                onClick={() => handleSort('id')}
              >
                Mã
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-gray-100 text-xs font-semibold"
                onClick={() => handleSort('title')}
              >
                Tên Báo cáo
              </TableHead>
              <TableHead className="text-xs font-semibold">Người tạo</TableHead>
              <TableHead className="text-xs font-semibold">Người chịu trách nhiệm</TableHead>
              <TableHead className="text-xs font-semibold">Người được duyệt</TableHead>
              <TableHead className="text-xs font-semibold">Kênh nhận</TableHead>
              <TableHead className="text-xs font-semibold">Kết thúc</TableHead>
              <TableHead className="text-xs font-semibold">Lần chạy tiếp</TableHead>
              <TableHead className="text-xs font-semibold">Lần gửi tiếp</TableHead>
              <TableHead className="text-xs font-semibold">Lỗi?</TableHead>
              <TableHead className="text-xs font-semibold">Hoạt động</TableHead>
              <TableHead className="text-xs font-semibold">Sửa</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedReports.map(report => (
              <TableRow key={report.id} className="hover:bg-gray-50 border-b border-gray-200 text-sm">
                <TableCell className="font-medium text-gray-900">{report.id}</TableCell>
                <TableCell>
                  <div>
                    <p className="font-medium text-gray-900">{report.title}</p>
                    {report.description && (
                      <p className="text-xs text-gray-500">{report.description}</p>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-gray-700">{report.creator}</TableCell>
                <TableCell className="text-gray-700">{report.owner}</TableCell>
                <TableCell className="text-gray-700">{report.recipient}</TableCell>
                <TableCell>
                  <code className="bg-gray-100 px-2 py-1 rounded text-xs">{report.id}</code>
                </TableCell>
                <TableCell className="text-gray-700">
                  {report.createdAt ? formatDate(report.createdAt) : '-'}
                </TableCell>
                <TableCell className="text-gray-700">
                  {report.lastSentAt ? formatDate(report.lastSentAt) : '-'}
                </TableCell>
                <TableCell className="text-gray-700">
                  {report.nextSendAt ? formatDate(report.nextSendAt) : '-'}
                </TableCell>
                <TableCell>
                  {report.status === 'active' ? (
                    <span className="text-green-600 text-lg">✓</span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </TableCell>
                <TableCell>
                  <Badge
                    className={`${getStatusColor(report.status)} text-xs`}
                  >
                    {report.status === 'active' ? 'Hoạt động' : report.status === 'draft' ? 'Nháp' : 'Không hoạt động'}
                  </Badge>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreHorizontal size={16} />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem asChild>
                        <Link href={`/reports/${report.id}`} className="flex items-center gap-2">
                          <Eye size={16} />
                          Xem
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href={`/reports/${report.id}/edit`} className="flex items-center gap-2">
                          <Edit2 size={16} />
                          Chỉnh sửa
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onDelete(report.id)}
                        className="text-red-600 focus:text-red-600 flex items-center gap-2"
                      >
                        <Trash2 size={16} />
                        Xóa
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-600">
          Hiển thị {paginatedReports.length > 0 ? (currentPage - 1) * ITEMS_PER_PAGE + 1 : 0}-
          {Math.min(currentPage * ITEMS_PER_PAGE, sortedReports.length)} trong {sortedReports.length} báo cáo
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft size={16} />
          </Button>
          <span className="text-xs text-gray-600 px-2">
            Trang {currentPage} / {totalPages || 1}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>
    </div>
  )
}
