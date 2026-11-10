/* ==========================================================================
   TOMUS — INTERAÇÕES E COPIADORES RÁPIDOS
   ========================================================================== */

(function () {
  "use strict";

  // 1. Cópia da Chave Pix
  const btnCopyPix = document.getElementById("btnCopyPix");
  const pixKeyDisplay = document.getElementById("pixKeyDisplay");
  const pixBtnText = document.getElementById("pixBtnText");

  if (btnCopyPix && pixKeyDisplay) {
    btnCopyPix.addEventListener("click", function () {
      const text = pixKeyDisplay.textContent.trim();
      navigator.clipboard.writeText(text).then(function () {
        const origText = pixBtnText.textContent;
        pixBtnText.textContent = "✔ Chave Copiada!";
        btnCopyPix.style.background = "#15803d";

        setTimeout(function () {
          pixBtnText.textContent = origText;
          btnCopyPix.style.background = "";
        }, 2200);
      });
    });
  }

  // 2. Cópia do Comando Gatekeeper
  document.querySelectorAll(".btn-copy-code").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const code = btn.getAttribute("data-code");
      if (code) {
        navigator.clipboard.writeText(code).then(function () {
          const orig = btn.textContent;
          btn.textContent = "Copiado!";
          btn.style.background = "#0284c7";

          setTimeout(function () {
            btn.textContent = orig;
            btn.style.background = "";
          }, 2000);
        });
      }
    });
  });

  // 3. Demo do Mockup de Fichamento
  const demoCopyBtn = document.getElementById("demoCopyBtn");
  if (demoCopyBtn) {
    demoCopyBtn.addEventListener("click", function () {
      const citationText = "RAWLS, John. Uma Teoria da Justiça. Tradução de Almiro Pisetta e Lenita Maria Rímoli Esteves. São Paulo: Martins Fontes, 1997. 708 p. ISBN 85-336-0681-X.";
      navigator.clipboard.writeText(citationText).then(function () {
        const span = demoCopyBtn.querySelector("span");
        if (span) {
          const orig = span.textContent;
          span.textContent = "✔ Citação ABNT Copiada!";
          demoCopyBtn.style.background = "#dcfce7";
          demoCopyBtn.style.color = "#15803d";
          demoCopyBtn.style.borderColor = "#86efac";

          setTimeout(function () {
            span.textContent = orig;
            demoCopyBtn.style.background = "";
            demoCopyBtn.style.color = "";
            demoCopyBtn.style.borderColor = "";
          }, 2200);
        }
      });
    });
  }

  // 4. Scroll suave para âncoras internas
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (event) {
      const targetId = anchor.getAttribute("href");
      if (targetId === "#") return;

      const target = document.querySelector(targetId);
      if (target) {
        event.preventDefault();
        const navHeight = document.getElementById("navbar") ? 70 : 0;
        const targetPos = target.getBoundingClientRect().top + window.pageYOffset - navHeight;

        window.scrollTo({
          top: targetPos,
          behavior: "smooth"
        });
      }
    });
  });
})();
