export function initAutorizar(secao) {
  const titulo = secao.querySelector('[data-autorizar="titulo"]');
  const caixa = secao.querySelector('[data-autorizar="codigo"]');
  const painelOk = secao.querySelector('[data-autorizar="ok"]');
  const painelSem = secao.querySelector('[data-autorizar="sem"]');
  const painelErro = secao.querySelector('[data-autorizar="erro"]');
  const motivo = secao.querySelector('[data-autorizar="motivo"]');
  const botaoCopiar = secao.querySelector('[data-autorizar="copiar"]');
  const botaoZap = secao.querySelector('[data-autorizar="whatsapp"]');

  if (!caixa || !painelOk || !painelSem || !painelErro) return;

  const url = new URL(location.href);
  const codigo = url.searchParams.get("code");
  const erro = url.searchParams.get("error_description") || url.searchParams.get("error");

  const TITULOS = new Map([
    [painelOk, "pronto, enrico"],
    [painelSem, "nada por aqui"],
    [painelErro, "não deu"],
  ]);

  const mostrar = (qual) => {
    for (const p of [painelOk, painelSem, painelErro]) p.hidden = p !== qual;
    if (titulo) titulo.textContent = TITULOS.get(qual) || titulo.textContent;
  };

  if (erro) {
    if (motivo) motivo.textContent = erro;
    mostrar(painelErro);
    return;
  }

  if (!codigo) {
    mostrar(painelSem);
    return;
  }

  const limpo = codigo.split("#")[0].trim();
  caixa.textContent = limpo;
  mostrar(painelOk);

  if (botaoZap) {
    const texto = `código do instagram\n\n${limpo}`;

    botaoZap.href = `https://wa.me/?text=${encodeURIComponent(texto)}`;
  }

  if (botaoCopiar) {
    botaoCopiar.addEventListener("click", async () => {
      const rotulo = botaoCopiar.querySelector(".btn__label") || botaoCopiar;
      const antes = rotulo.textContent;
      try {
        await navigator.clipboard.writeText(limpo);
        rotulo.textContent = "copiado";
      } catch {

        const faixa = document.createRange();
        faixa.selectNodeContents(caixa);
        const selecao = window.getSelection();
        selecao.removeAllRanges();
        selecao.addRange(faixa);
        rotulo.textContent = "selecionado, toque e copie";
      }
      setTimeout(() => {
        rotulo.textContent = antes;
      }, 2600);
    });
  }
}
