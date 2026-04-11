'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Search, X } from 'lucide-react'

interface ReportsFiltersProps {
  onFilterChange: (filters: FilterState) => void
  onCreateNew: () => void
}

export interface FilterState {
  search: string
  status?: string
  tags?: string[]
}

const statusOptions = [
  { value: 'all', label: 'Tất cả' },
  { value: 'active', label: 'Hoạt động' },
  { value: 'inactive', label: 'Không hoạt động' },
  { value: 'draft', label: 'Nháp' },
]

const availableTags = [
  'chất lượng',
  'OPM',
  'shop',
  'SLA',
  'test',
  'vita',
  'chỉnh lịch',
  'theo dõi',
  'vận hành',
  'hiệu suất',
  'bộ phận',
  'giao dịch',
  'hàng ngày',
  'rủi ro',
  'tín dụng',
  'kiểm soát',
  'dự báo',
  'bán hàng',
]

export function ReportsFilters({ onFilterChange, onCreateNew }: ReportsFiltersProps) {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [showTagDropdown, setShowTagDropdown] = useState(false)

  const handleSearchChange = (value: string) => {
    setSearch(value)
    onFilterChange({
      search: value,
      status: status === 'all' ? undefined : status,
      tags: selectedTags.length > 0 ? selectedTags : undefined,
    })
  }

  const handleStatusChange = (value: string) => {
    setStatus(value)
    onFilterChange({
      search,
      status: value === 'all' ? undefined : value,
      tags: selectedTags.length > 0 ? selectedTags : undefined,
    })
  }

  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => {
      const newTags = prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
      onFilterChange({
        search,
        status: status === 'all' ? undefined : status,
        tags: newTags.length > 0 ? newTags : undefined,
      })
      return newTags
    })
  }

  const clearFilters = () => {
    setSearch('')
    setStatus('all')
    setSelectedTags([])
    onFilterChange({ search: '', status: undefined, tags: undefined })
  }

  return (
    <div className="space-y-4 bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-end gap-4 flex-wrap">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-2">Mã báo cáo</label>
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Nhập mã báo cáo"
              className="pl-10"
              value={search}
              onChange={e => handleSearchChange(e.target.value)}
            />
          </div>
        </div>

        {/* Status Filter */}
        <div className="min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-2">Trạng thái</label>
          <Select value={status} onValueChange={(val) => handleStatusChange(val ?? 'all')}>
            <SelectTrigger>
              <SelectValue placeholder="Chọn trạng thái" />
            </SelectTrigger>
            <SelectContent>
              {statusOptions.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Search & Create Buttons */}
        <div className="flex gap-2">
          <Button variant="outline" className="border-green-600 text-green-600 hover:bg-green-50">
            <Search size={16} className="mr-2" />
            Tìm kiếm
          </Button>
          <Button className="bg-green-600 hover:bg-green-700 text-white" onClick={onCreateNew}>
            Nhập lại
          </Button>
        </div>
      </div>

      {/* Tags Filter */}
      <div className="relative">
        <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedTags.map(tag => (
            <div
              key={tag}
              className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm flex items-center gap-2"
            >
              {tag}
              <button
                onClick={() => handleTagToggle(tag)}
                className="hover:bg-green-200 rounded-full p-0.5"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>

        <button
          onClick={() => setShowTagDropdown(!showTagDropdown)}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          + Thêm tag
        </button>

        {showTagDropdown && (
          <div className="absolute top-full left-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto w-full">
            {availableTags.map(tag => (
              <button
                key={tag}
                onClick={() => {
                  handleTagToggle(tag)
                }}
                className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${
                  selectedTags.includes(tag) ? 'bg-green-50' : ''
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Clear Filters */}
      {(search || status !== 'all' || selectedTags.length > 0) && (
        <Button variant="ghost" size="sm" onClick={clearFilters} className="text-red-600">
          <X size={16} className="mr-2" />
          Xóa bộ lọc
        </Button>
      )}
    </div>
  )
}
