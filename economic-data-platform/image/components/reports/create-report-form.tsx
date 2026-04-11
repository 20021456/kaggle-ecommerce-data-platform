'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { createReportSchema, CreateReportInput } from '@/lib/schemas'
import { useReports } from '@/components/providers/reports-provider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, ChevronLeft, ChevronRight, Plus, X } from 'lucide-react'

const scheduleOptions = [
  { value: 'once', label: 'Một lần' },
  { value: 'daily', label: 'Hàng ngày' },
  { value: 'weekly', label: 'Hàng tuần' },
  { value: 'monthly', label: 'Hàng tháng' },
]

const statusOptions = [
  { value: 'draft', label: 'Nháp' },
  { value: 'active', label: 'Hoạt động' },
  { value: 'inactive', label: 'Không hoạt động' },
]

const loaiFormOptions = [
  { value: 'Chi tiết', label: 'Chi tiết' },
  { value: 'Tính toán', label: 'Tính toán' },
  { value: 'Chỉ số', label: 'Chỉ số' },
]

const availableTags = ['chất lượng', 'OPM', 'shop', 'SLA', 'test', 'vita', 'vận hành', 'hiệu suất']
const groupOptions = ['Báo cáo tiêu chuẩn', 'Báo cáo kinh doanh', 'Báo cáo nội bộ', 'Báo cáo vận hành']

interface CreateReportFormProps {
  initialData?: CreateReportInput
}

export function CreateReportForm({ initialData }: CreateReportFormProps) {
  const router = useRouter()
  const { addReport, updateReport } = useReports()
  const [currentStep, setCurrentStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [selectedTags, setSelectedTags] = useState<string[]>(initialData?.tags || [])
  const [showTagDropdown, setShowTagDropdown] = useState(false)

  const form = useForm<CreateReportInput>({
    resolver: zodResolver(createReportSchema),
    defaultValues: initialData || {
      title: '',
      description: '',
      creator: '',
      owner: '',
      recipient: '',
      schedule: 'daily',
      status: 'draft',
      tags: [],
      group: '',
      sqlTemplate: '',
      loaiForm: 'Chi tiết',
    },
  })

  const onSubmit = async (data: CreateReportInput) => {
    setIsSubmitting(true)
    try {
      const reportData = {
        ...data,
        tags: selectedTags,
      }

      if (initialData) {
        await updateReport(initialData.title, reportData)
      } else {
        await addReport(reportData)
      }

      router.push('/reports')
      router.refresh()
    } catch (error) {
      console.error('Failed to save report:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => {
      const newTags = prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
      form.setValue('tags', newTags)
      return newTags
    })
  }

  const handleRemoveTag = (tag: string) => {
    const newTags = selectedTags.filter(t => t !== tag)
    setSelectedTags(newTags)
    form.setValue('tags', newTags)
  }

  const totalSteps = 3
  const isFirstStep = currentStep === 1
  const isLastStep = currentStep === totalSteps

  return (
    <div className="max-w-4xl mx-auto">
      {/* Step Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {[1, 2, 3].map((step, idx) => (
            <div key={step} className="flex items-center flex-1">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full font-semibold ${
                  step === currentStep
                    ? 'bg-green-600 text-white'
                    : step < currentStep
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-200 text-gray-700'
                }`}
              >
                {step < currentStep ? '✓' : step}
              </div>
              {idx < 2 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    step < currentStep ? 'bg-green-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-gray-600">
          <span>Bước 1: Thông tin cơ bản</span>
          <span>Bước 2: Lịch trình</span>
          <span>Bước 3: Cấu hình nâng cao</span>
        </div>
      </div>

      {/* Form */}
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          {/* Step 1: Basic Info */}
          {currentStep === 1 && (
            <div className="space-y-6 bg-white p-6 rounded-lg border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Thông tin cơ bản</h2>

              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Tên báo cáo <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="Nhập tên báo cáo" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mô tả</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Nhập mô tả báo cáo" rows={4} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="creator"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Người tạo <span className="text-red-500">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input placeholder="Nhập tên người tạo" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="owner"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Chủ sở hữu <span className="text-red-500">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input placeholder="Nhập tên chủ sở hữu" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="recipient"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Người nhận <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="Nhập tên người nhận" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          )}

          {/* Step 2: Schedule */}
          {currentStep === 2 && (
            <div className="space-y-6 bg-white p-6 rounded-lg border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Lịch trình gửi báo cáo</h2>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="schedule"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Tần suất <span className="text-red-500">*</span>
                      </FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Chọn tần suất" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {scheduleOptions.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="status"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Trạng thái <span className="text-red-500">*</span>
                      </FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Chọn trạng thái" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {statusOptions.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="group"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nhóm báo cáo</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value || ''}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Chọn nhóm báo cáo" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {groupOptions.map(option => (
                          <SelectItem key={option} value={option}>
                            {option}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          )}

          {/* Step 3: Advanced Config */}
          {currentStep === 3 && (
            <div className="space-y-6 bg-white p-6 rounded-lg border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Cấu hình nâng cao</h2>

              <FormField
                control={form.control}
                name="loaiForm"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loại Form</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value || 'Chi tiết'}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Chọn loại form" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {loaiFormOptions.map(option => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="connector"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Connector</FormLabel>
                    <FormControl>
                      <Input placeholder="Nhập connector" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="queue"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Queue</FormLabel>
                    <FormControl>
                      <Input placeholder="Nhập queue" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Tags */}
              <FormItem>
                <FormLabel>Tags</FormLabel>
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {selectedTags.map(tag => (
                      <Badge key={tag} className="bg-green-100 text-green-700 flex items-center gap-1 px-3">
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="hover:bg-green-200 rounded p-0.5"
                        >
                          <X size={14} />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setShowTagDropdown(!showTagDropdown)}
                      className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      <Plus size={14} />
                      Thêm tag
                    </button>

                    {showTagDropdown && (
                      <div className="absolute top-full left-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto w-64">
                        {availableTags.map(tag => (
                          <button
                            key={tag}
                            type="button"
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
                </div>
              </FormItem>

              <FormField
                control={form.control}
                name="sqlTemplate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>SQL Template</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Nhập SQL template (ví dụ: SELECT * FROM table)"
                        rows={6}
                        className="font-mono text-sm"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>Nhập mẫu SQL để truy vấn dữ liệu</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="notes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ghi chú</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Nhập ghi chú" rows={3} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          )}

          {/* Navigation */}
          <div className="flex gap-3 justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
              className="border-gray-300"
            >
              <ChevronLeft size={16} className="mr-2" />
              Hủy
            </Button>

            <div className="flex gap-3">
              {!isFirstStep && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCurrentStep(currentStep - 1)}
                >
                  <ChevronLeft size={16} className="mr-2" />
                  Quay lại
                </Button>
              )}

              {!isLastStep ? (
                <Button
                  type="button"
                  className="bg-green-600 hover:bg-green-700 text-white"
                  onClick={() => setCurrentStep(currentStep + 1)}
                >
                  Tiếp theo
                  <ChevronRight size={16} className="ml-2" />
                </Button>
              ) : (
                <Button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 text-white"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Đang lưu...' : 'Tạo báo cáo'}
                </Button>
              )}
            </div>
          </div>
        </form>
      </Form>
    </div>
  )
}
