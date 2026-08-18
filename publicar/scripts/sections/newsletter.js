const FRASES = {
  confirme:
    "falta um clique. um e-mail acabou de sair para {email} — abra e confirme, " +
    "e é só isso. sem essa confirmação o endereço não entra na lista.",
  "email-invalido":
    "esse endereço não parece completo. confira e tente de novo.",
  "muitas-tentativas":
    "muitas tentativas deste aparelho em pouco tempo. espere um minuto.",
  indisponivel:
    "não deu para inscrever agora — o problema é aqui, não no seu endereço. " +
    "tente mais tarde.",
};

function pareceEmail(valor) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(valor.trim());
}

export function initNewsletter(secao) {

  if (secao.dataset.modo !== "formulario") return;

  const form = secao.querySelector(".newsletter__form");
  const entrada = secao.querySelector(".newsletter__entrada");
  const botao = secao.querySelector(".newsletter__botao");
  const aviso = secao.querySelector('[data-newsletter="aviso"]');
  const endpoint = form?.dataset.endpoint;

  if (!form || !entrada || !botao || !aviso || !endpoint) return;

  function mostrar(tipo, texto) {
    aviso.textContent = texto;
    aviso.dataset.tipo = tipo;
    aviso.hidden = false;
  }

  function limpar() {
    aviso.hidden = true;
    aviso.textContent = "";
    delete aviso.dataset.tipo;
    entrada.removeAttribute("aria-invalid");
  }

  entrada.addEventListener("input", () => {
    if (!aviso.hidden) limpar();
  });

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limpar();

    const email = entrada.value.trim();
    if (!pareceEmail(email)) {
      entrada.setAttribute("aria-invalid", "true");
      mostrar("erro", FRASES["email-invalido"]);
      entrada.focus();
      return;
    }

    botao.setAttribute("aria-busy", "true");
    botao.disabled = true;

    try {
      const resposta = await fetch(`${endpoint}/inscrever`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, origem: location.pathname }),
      });

      const dados = await resposta.json().catch(() => ({}));
      const estado = dados.estado ?? (resposta.ok ? "confirme" : "indisponivel");
      const frase = FRASES[estado] ?? FRASES.indisponivel;

      if (estado === "confirme") {
        mostrar("ok", frase.replace("{email}", email));

        entrada.disabled = true;
        botao.hidden = true;
      } else {
        mostrar("erro", frase);
        if (estado === "email-invalido") {
          entrada.setAttribute("aria-invalid", "true");
          entrada.focus();
        }
      }
    } catch {

      mostrar(
        "erro",
        "não deu para falar com o serviço agora. confira a conexão e tente " +
          "de novo em um instante.",
      );
    } finally {
      botao.removeAttribute("aria-busy");
      botao.disabled = false;
    }
  });
}
