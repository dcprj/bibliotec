/* ==========================================================================
   Tomus — Landing Page Script
   Funcionalidades: menu mobile, cópia da chave Pix, scroll suave
   ========================================================================== */

(function () {
  "use strict";

  // ---------- Menu Mobile ----------
  const navToggle = document.getElementById("nav-toggle");
  const navMenu = document.getElementById("nav-menu");

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      const isOpen = navMenu.classList.contains("active");
      navMenu.classList.toggle("active");
      navToggle.setAttribute("aria-expanded", !isOpen);
    });

    // Fechar menu ao clicar em um link
    const navLinks = navMenu.querySelectorAll(".nav-link");
    navLinks.forEach(function (link) {
      link.addEventListener("click", function () {
        navMenu.classList.remove("active");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // ---------- Cópia da chave Pix ----------
  const btnCopiarPix = document.getElementById("btnCopiarPix");
  const pixChave = document.getElementById("pixChave");

  if (btnCopiarPix && pixChave) {
    btnCopiarPix.addEventListener("click", function () {
      const chave = pixChave.textContent.trim();

      navigator.clipboard
        .writeText(chave)
        .then(function () {
          const textoOriginal = btnCopiarPix.textContent;
          btnCopiarPix.textContent = "Copiado!";
          btnCopiarPix.classList.add("btn-primary");
          btnCopiarPix.classList.remove("btn-outline");

          setTimeout(function () {
            btnCopiarPix.textContent = textoOriginal;
            btnCopiarPix.classList.remove("btn-primary");
            btnCopiarPix.classList.add("btn-outline");
          }, 2000);
        })
        .catch(function (err) {
          console.error("Falha ao copiar a chave Pix: ", err);
          // Fallback para navegadores antigos
          const textoSelecionado = document.createRange();
          textoSelecionado.selectNodeContents(pixChave);
          const selecao = window.getSelection();
          selecao.removeAllRanges();
          selecao.addRange(textoSelecionado);
          document.execCommand("copy");
          selecao.removeAllRanges();
        });
    });
  }

  // ---------- Scroll suave para âncoras ----------
  document.querySelectorAll('a[href^="#"]').forEach(function (ancora) {
    ancora.addEventListener("click", function (event) {
      const alvoId = ancora.getAttribute("href");
      if (alvoId === "#") return;

      const alvo = document.querySelector(alvoId);
      if (alvo) {
        event.preventDefault();
        const navbarAltura = document.getElementById("navbar")
          ? document.getElementById("navbar").offsetHeight
          : 72;
        const posicao =
          alvo.getBoundingClientRect().top +
          window.pageYOffset -
          navbarAltura -
          16;

        window.scrollTo({
          top: posicao,
          behavior: "smooth",
        });
      }
    });
  }

  // ---------- Mudar estilo da navbar ao rolar ----------
  const navbar = document.getElementById("navbar");
  if (navbar) {
    window.addEventListener("scroll", function () {
      if (window.scrollY > 20) {
        navbar.style.boxShadow = "0 4px 12px rgba(15, 23, 42, 0.08)";
      } else {
        navbar.style.boxShadow = "none";
      }
    });
  }
})();
