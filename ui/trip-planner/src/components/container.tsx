import { cn } from "@/app/lib/utils";
import React from 'react'

export const Container = ({children,className}: {
    children: React.ReactNode,
    className?: string
}) => {
  return (
    <div className={cn("max-w-7xl mx-auto px-4 md:py-8 w-full", className)}>{children}</div>
  )
}
