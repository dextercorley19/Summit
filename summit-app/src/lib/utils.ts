import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// API URL configuration - change this for production vs development
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
