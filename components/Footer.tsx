"use client";

import Script from "next/script";

export default function Footer() {
    return (
        <>
            <div className="text-center p-5 text-[#444] text-[10px] mt-5">
                System by <strong>TIAS RS XinZhi</strong> & Gemini<br />
                <span
                    id="busuanzi_container_site_pv"
                    style={{ display: "none", color: "#666", fontSize: "9px", marginTop: "5px" }}
                >
                    戰情室累計瀏覽:{" "}
                    <span id="busuanzi_value_site_pv" style={{ color: "#ffca28", fontWeight: "bold" }}></span>{" "}
                    次
                </span>
            </div>
            <Script src="//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js" strategy="lazyOnload" />
        </>
    );
}
