"use client";

/**
 * LineBotFab - LINE 錯誤反饋懸浮按鈕
 * 固定於畫面右下角，點擊後開啟 LINE 加入好友頁面。
 * 使用 LINE 官方「加入好友」按鈕圖片。
 */
export default function LineBotFab() {
    return (
        <a
            href="https://lin.ee/yZb5gYR"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="LINE 錯誤反饋"
            className="fixed bottom-6 right-6 z-50
                 hover:scale-105 active:scale-95
                 transition-transform duration-200
                 drop-shadow-lg hover:drop-shadow-2xl"
        >
            {/* LINE 官方「加入好友」按鈕 */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
                src="https://scdn.line-apps.com/n/line_add_friends/btn/zh-Hant.png"
                alt="加入好友"
                height={36}
                className="h-9"
            />
        </a>
    );
}
