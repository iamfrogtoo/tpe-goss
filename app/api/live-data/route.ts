import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // 優先使用 CDN 備用資料源（公開可訪問）
    const cdnUrl = 'https://cdn.jsdelivr.net/gh/iamfrogtoo/tpe-goss@main/public/live_data.json';
    
    console.log('嘗試從 CDN 獲取資料:', cdnUrl);
    const response = await fetch(cdnUrl, {
      headers: {
        'User-Agent': 'TPE-GOSS-API-Proxy/1.0',
      },
    });

    if (!response.ok) {
      throw new Error(`CDN HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('成功從 CDN 獲取資料，航班數量:', data.flights?.length || 0);

    // 返回資料，設定 CORS 標頭
    return NextResponse.json(data, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    });

  } catch (error) {
    console.error('API Proxy Error:', error);
    
    // 返回錯誤回應
    return NextResponse.json(
      { 
        error: '無法獲取即時資料',
        timestamp: new Date().toISOString(),
        details: error.message
      },
      { 
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      }
    );
  }
}

export async function OPTIONS() {
  return NextResponse.json({}, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}