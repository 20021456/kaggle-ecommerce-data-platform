'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  ChevronDown,
  Plus,
  FileText,
  List,
  BarChart3,
  Heart,
  Clock,
  Command,
  Activity,
  Database,
  LayoutDashboard,
} from 'lucide-react'
import { useState } from 'react'

const menuItems = [
  {
    section: 'Monitoring',
    items: [
      {
        label: 'Airflow Monitor',
        icon: Activity,
        href: '/monitor/airflow',
      },
      {
        label: 'Ingestion Monitor',
        icon: Database,
        href: '/monitor/ingestion',
      },
    ],
  },
  {
    section: 'Analytics',
    items: [
      {
        label: 'Dashboard',
        icon: LayoutDashboard,
        href: '/dashboard',
      },
    ],
  },
  {
    section: 'Danh mục',
    items: [
      {
        label: 'Báo cáo có bản',
        icon: FileText,
        href: '/',
        badge: '',
      },
      {
        label: 'Danh sách báo cáo',
        icon: List,
        href: '/reports',
      },
    ],
  },
  {
    section: 'Quản lý',
    items: [
      {
        label: 'Tạo báo cáo',
        icon: Plus,
        href: '/reports/create',
      },
      {
        label: 'Tạo báo cáo nâng cao',
        icon: BarChart3,
        href: '/reports/create',
      },
      {
        label: 'Danh sách yêu cầu',
        icon: Heart,
        href: '/reports',
      },
      {
        label: 'Báo cáo định kỳ',
        icon: Clock,
        href: '/reports',
      },
      {
        label: 'Đăng xuất',
        icon: Command,
        href: '/',
      },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const [expandedSections, setExpandedSections] = useState<string[]>(['Monitoring', 'Analytics', 'Danh mục', 'Quản lý'])

  const toggleSection = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section) ? prev.filter(s => s !== section) : [...prev, section]
    )
  }

  return (
    <aside className="w-56 bg-gray-50 border-r border-gray-200 min-h-screen p-4 overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-sm font-semibold text-gray-600 px-2">Danh mục</h1>
      </div>

      <nav className="space-y-1">
        {menuItems.map(section => (
          <div key={section.section} className="mb-4">
            <button
              onClick={() => toggleSection(section.section)}
              className="w-full flex items-center justify-between px-2 py-2 text-xs font-semibold text-gray-600 hover:text-gray-900 transition-colors"
            >
              <span>{section.section}</span>
              <ChevronDown
                size={16}
                className={`transition-transform ${expandedSections.includes(section.section) ? 'rotate-180' : ''}`}
              />
            </button>

            {expandedSections.includes(section.section) && (
              <div className="mt-2 space-y-1">
                {section.items.map(item => {
                  const Icon = item.icon
                  const isActive = pathname === item.href
                  return (
                    <Link
                      key={item.label}
                      href={item.href}
                      className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                        isActive
                          ? 'bg-green-50 text-green-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Icon size={16} />
                      <span className="flex-1">{item.label}</span>
                      {'badge' in item && item.badge && (
                        <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  )
                })}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  )
}
