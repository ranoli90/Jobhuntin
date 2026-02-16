import { NextRequest, NextResponse } from 'next/server';
import DatabasePerformanceTest from '../../../lib/performance-test';

export async function GET(request: NextRequest) {
  try {
    // Run comprehensive performance test
    const results = await DatabasePerformanceTest.runFullTest();
    
    return NextResponse.json({
      success: true,
      data: results,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Performance test failed:', error);
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    }, { status: 500 });
  }
}
