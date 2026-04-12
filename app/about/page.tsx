import Link from "next/link";

export default function About() {
    return (
        <div className="container-goss">
            <h1 className="text-[24px] font-bold text-[#00f260] border-b border-[#333] pb-[10px] mb-4">
                關於 TPE GOSS
            </h1>
            <p className="text-[#e0e0e0] leading-relaxed mb-8">
                Ground Operations Support System (地面作業支援系統)
                <br />
                本系統整合 ADS-B 航班數據與機場班表，提供地勤人員即時的戰術資訊。
            </p>

            <h2 className="text-[20px] font-bold text-[#ffca28] mt-[30px] mb-4">
                開發日誌與初衷
            </h2>
            <div className="flex flex-col gap-6">
                <div className="border-l-[3px] border-[#4facfe] pl-[15px]">
                    <div className="text-[12px] text-[#4facfe] font-bold tracking-widest">THE VISION</div>
                    <strong className="text-white block mt-1 text-[18px]">來自機坪一線的真實需求</strong>
                    <p className="text-[#aaa] mt-2 text-[14px] leading-relaxed">
                        每天分秒必爭的地面作業中，我們需要的是「精準的落地順序」、「即時機坪分配」與「準確的地面狀態」。
                        現有公開平台資訊常有延遲或缺失，這讓我們決定自己打造專屬於地勤人員的戰情系統。
                    </p>
                </div>

                <div className="border-l-[3px] border-[#00f260] pl-[15px]">
                    <div className="text-[12px] text-[#00f260] font-bold tracking-widest">THE JOURNEY</div>
                    <strong className="text-white block mt-1 text-[18px]">與硬體搏鬥的歷程</strong>
                    <p className="text-[#aaa] mt-2 text-[14px] leading-relaxed">
                        從老舊筆電起步，到自購 RTL-SDR 天線，我們克服了 USB 供電不足與驅動問題。
                        現在，我們利用絕佳的空中視距優勢，部署樹莓派 (Raspberry Pi) 作為前哨站，補足了桃園機場周邊監控的死角。
                    </p>
                </div>

                <div className="border-l-[3px] border-[#f1c40f] pl-[15px]">
                    <div className="text-[12px] text-[#f1c40f] font-bold tracking-widest">CORE VALUE</div>
                    <strong className="text-white block mt-1 text-[18px]">地勤最需要的總和</strong>
                    <ul className="text-[#aaa] mt-2 text-[14px] leading-relaxed list-disc ml-[15px] space-y-1">
                        <li><strong className="text-[#ccc]">精準排序：</strong>結合雷達高度與機場班表，解決盤旋與過境航班誤導。</li>
                        <li><strong className="text-[#ccc]">資料融合：</strong>獨家整合自建雷達與桃機官網，即時顯示機坪分配。</li>
                        <li><strong className="text-[#ccc]">視覺優化：</strong>黑底高對比設計，夜間作業與強光下皆清晰可見。</li>
                    </ul>
                </div>
            </div>

            <h2 className="text-[20px] font-bold text-[#ffca28] mt-[40px] mb-4">
                版本更新紀錄
            </h2>
            <div className="bg-[#1a1a1a] p-[20px] rounded-[8px] border border-[#333]">
                <ul className="text-[#aaa] text-[14px] leading-relaxed space-y-3 font-mono">
                    <li className="flex items-start gap-3">
                        <span className="text-[#f1c40f] font-bold shrink-0">2026/04/11</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">持續修改中</span>
                        <span className="text-[#ccc]">4.0版本又遇到難題，但是聽到對夥伴有幫助，開心！持續修改中。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#ff6b6b] font-bold shrink-0">2026/03/25</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">改進方案努力中</span>
                        <span className="text-[#ccc]">3.0架構失敗了，導致數據錯亂丟失，加上Google Token 縮水，效率變低，改進方案努力中。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#f1c40f] font-bold shrink-0">2026/04/04</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">4.0 測試版</span>
                        <span className="text-[#ccc]">新版架構敬請期待，使用 SQLite3 資料庫，整合本地天線與 OpenSky 數據融合。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#00f260] font-bold shrink-0">2026/03/11</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">2.7 版</span>
                        <span className="text-[#ccc]">🎉 瀏覽人次突破 1,000！新增 LINE 錯誤反饋 Bot 懸浮按鈕（全站右下角一鍵加好友），建立討論群組。修正入境追蹤器時間窗異常放行與重複航班判斷邏輯。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#00f260] font-bold shrink-0">2026/03/07</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">2.63 版</span>
                        <span className="text-[#ccc]">去除部分無效錯誤訊息與拔除實驗性留言功能，修正航空公司代碼 (O3) 解析，並導入 ICAO 轉 IATA 解決方案，修復「即時離場」機坪遺失問題。改善「過境航班」視覺置中排版。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#00f260] font-bold shrink-0">2026/03/06</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">2.6 版</span>
                        <span className="text-[#ccc]">去除部分無效錯誤訊息警告，新增即時航班之機型與過濾星宇航空與 A320 機型，並導入註冊機號雙重顯示。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#ffca28] font-bold shrink-0">2026/03/01</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">2.02 版</span>
                        <span className="text-[#ccc]">修復航班時間解析邏輯，解決即時離場頁面缺少未來航班與機坪資訊的問題；同步背景多重追蹤器邏輯，消弭網頁新舊資料反覆跳動之錯誤。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#00f260] font-bold shrink-0">2026/02/26</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">2.01 版</span>
                        <span className="text-[#ccc]">全面升級為 Next.js 現代化框架，引入無 CORS 跨日排序防呆機制，擴展每日航班班表查詢功能，介面效能與穩定度大幅進化。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#4facfe] font-bold shrink-0">2026/01/30</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">1.1 版</span>
                        <span className="text-[#ccc]">部署樹莓派硬體前哨站，完善雷達監測死角，強化 ADS-B 本地端訊號收集能力。</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-[#f1c40f] font-bold shrink-0">2025/11/22</span>
                        <span className="text-white bg-[#333] px-[6px] py-[2px] rounded text-[11px] shrink-0 mt-[2px]">1.01 版</span>
                        <span className="text-[#ccc]">TPE GOSS 第一版正式上線，導入機坪動態配置與基礎落地即時排序功能，解決地勤前線痛點。</span>
                    </li>
                </ul>
            </div>

            <h2 className="text-[20px] font-bold text-[#ffca28] mt-[40px] mb-4">
                永續經營與贊助支持
            </h2>
            <div className="bg-[#1a1a1a] p-[20px] rounded-[8px] border border-[#333]">
                <p className="text-[#e0e0e0] mb-4 text-[14px] leading-relaxed">
                    為了讓 TPE GOSS 能持續免費服務地勤同仁，我們需要您的支持。您的贊助將用於維護網址 (tpegoss.com)、
                    雲端主機、樹莓派電費、採購 UPS 不斷電系統，以及未來擴充更高階的 API 航資。
                    <br /><br />
                    <strong className="text-[#00f260]">🎉 贊助者獨享回饋：</strong>未來將開放歷史航跡回放，以及專屬 LINE 通知機器人（例如特殊塗裝機接近提醒）。
                </p>

                <div className="mt-[20px] flex justify-center">
                    {/* 街口支付 */}
                    <div className="bg-[#E4002B]/10 border border-[#E4002B]/30 p-5 rounded-lg flex flex-col items-center justify-center max-w-[300px] w-full">
                        <div className="text-[#E4002B] font-bold text-[18px] mb-1">街口支付 JKO PAY</div>
                        <p className="text-[#aaa] text-[12px] text-center mb-4">
                            免手續費，掃碼立即贊助
                        </p>

                        <a href="jkopay://transfer?jkoNo=396900778304" target="_blank" rel="noopener noreferrer" className="block w-[120px] h-[120px] bg-white rounded-[10px] mb-3 flex items-center justify-center border-[3px] border-[#E4002B] overflow-hidden p-[8px] hover:scale-105 transition-transform shadow-[0_0_15px_rgba(228,0,43,0.3)] cursor-pointer">
                            <img src="/jkopay.png" alt="JKO Pay QR" className="w-full h-full object-contain" />
                        </a>

                        <span className="text-[#666] text-[11px] mb-2 text-center">↑ 點擊 QR Code 可直接跳轉街口 APP ↑</span>

                        <div className="text-center bg-[#111] py-2 px-4 rounded-full border border-[#333] mt-1">
                            <span className="text-[#888] text-[11px] mr-2">直接轉帳街口帳號</span>
                            <span className="text-[#E4002B] font-mono text-[14px] font-bold tracking-widest">396 900778304</span>
                        </div>
                    </div>
                </div>
            </div>

            <h2 className="text-[20px] font-bold text-[#ffca28] mt-[40px] mb-4">
                回報問題與建議
            </h2>
            <div className="bg-[#1a1a1a] p-[20px] rounded-[8px] border border-[#333] flex flex-col md:flex-row items-center justify-between gap-4">
                <div>
                    <h3 className="text-[#fff] text-[16px] font-bold mb-1">發現網站 Bug 或有新點子嗎？</h3>
                    <p className="text-[#aaa] text-[13px] leading-relaxed">
                        TPE GOSS 是為了解決地勤痛點而生，非常歡迎您提供任何介面上的建議、發現的錯誤、或是未來希望新增的功能！
                    </p>
                </div>
                <a href="mailto:iamfrogtoo@gmail.com?subject=TPE%20GOSS%20系統反饋與建議" className="shrink-0 bg-[#333] hover:bg-[#444] text-white px-5 py-3 rounded-lg font-bold text-[14px] border border-[#555] transition-colors flex items-center gap-2 no-underline">
                    ✉️ 寫信給開發者
                </a>
            </div>
        </div>
    );
}
