/* 搜绎项目页 - 轻量交互 */

// 平滑滚动（兼容老浏览器）
document.querySelectorAll('a[href^="#"]').forEach((a) => {
  a.addEventListener("click", (e) => {
    const id = a.getAttribute("href");
    if (id === "#") return;
    const el = document.querySelector(id);
    if (!el) return;
    e.preventDefault();
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    history.replaceState(null, "", id);
  });
});

// Header 阴影（滚动时）
const header = document.querySelector(".site-header");
if (header) {
  window.addEventListener("scroll", () => {
    if (window.scrollY > 10) {
      header.style.boxShadow = "0 2px 12px var(--shadow)";
    } else {
      header.style.boxShadow = "none";
    }
  }, { passive: true });
}

// 当前年（footer）
const yearEl = document.querySelector("[data-current-year]");
if (yearEl) yearEl.textContent = String(new Date().getFullYear());
