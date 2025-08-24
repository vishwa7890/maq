'use client'
 
export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-[200px]">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-r-transparent" />
    </div>
  )
}
