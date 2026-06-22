// API types based on M6 specifications

export interface ApiResponse<T> {
  success: true;
  timestamp: string;
  data: T;
  confidence: number | null;
  metadata: Record<string, any>;
}

export interface ApiError {
  success: false;
  timestamp: string;
  error_code: string;
  message: string;
  details: any | null;
}
