'use client'

import React, { createContext, useContext, useState, useCallback } from 'react'
import { Report, ReportFormData } from '@/lib/types'
import { mockReports } from '@/lib/data'

interface ReportsContextType {
  reports: Report[]
  loading: boolean
  error: string | null
  addReport: (report: ReportFormData) => Promise<void>
  updateReport: (id: string | number, report: ReportFormData) => Promise<void>
  deleteReport: (id: string | number) => Promise<void>
  getReport: (id: string | number) => Report | undefined
}

const ReportsContext = createContext<ReportsContextType | undefined>(undefined)

export function ReportsProvider({ children }: { children: React.ReactNode }) {
  const [reports, setReports] = useState<Report[]>(mockReports)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addReport = useCallback(async (reportData: ReportFormData) => {
    setLoading(true)
    setError(null)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))

      const newReport: Report = {
        ...reportData,
        id: Math.max(...reports.map(r => typeof r.id === 'number' ? r.id : 0), 0) + 1,
        createdAt: new Date(),
      }

      setReports(prev => [newReport, ...prev])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add report')
      throw err
    } finally {
      setLoading(false)
    }
  }, [reports])

  const updateReport = useCallback(async (id: string | number, reportData: ReportFormData) => {
    setLoading(true)
    setError(null)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))

      setReports(prev =>
        prev.map(r =>
          r.id === id
            ? {
                ...r,
                ...reportData,
              }
            : r
        )
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update report')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteReport = useCallback(async (id: string | number) => {
    setLoading(true)
    setError(null)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))

      setReports(prev => prev.filter(r => r.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete report')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const getReport = useCallback((id: string | number) => {
    return reports.find(r => r.id === id)
  }, [reports])

  return (
    <ReportsContext.Provider value={{ reports, loading, error, addReport, updateReport, deleteReport, getReport }}>
      {children}
    </ReportsContext.Provider>
  )
}

export function useReports() {
  const context = useContext(ReportsContext)
  if (context === undefined) {
    throw new Error('useReports must be used within ReportsProvider')
  }
  return context
}
