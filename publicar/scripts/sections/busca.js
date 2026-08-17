const LIMITE = 40;

const semAcento = (s) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
               "jul", "ago", "set", "out", "nov", "dez"];

const dataCurta = (iso) => {
  const [ano, mes, dia] = iso.split("-");
  return `${dia} ${MESES[Number(mes) - 1]} ${ano}`;
};

const realcar = (original, termos) => {
  const alvo = semAcento(original);
  const faixas = [];
  for (const termo of termos) {
    let de = alvo.indexOf(termo);
    while (de !== -1) {
      faixas.push([de, de + termo.length]);
      de = alvo.indexOf(termo, de + termo.length);
    }
  }
  if (!faixas.length) return document.createTextNode(original);

  faixas.sort((a, b) => a[0] - b[0]);
  const juntas = [faixas[0]];
  for (const [de, ate] of faixas.slice(1)) {
    const ultima = juntas[juntas.length - 1];
    if (de <= ultima[1]) ultima[1] = Math.max(ultima[1], ate);
    else juntas.push([de, ate]);
  }

  const caixa = document.createDocumentFragment();
  let cursor = 0;
  for (const [de, ate] of juntas) {
    if (de > cursor) caixa.append(original.slice(cursor, de));
    const marca = document.createElement("mark");
    marca.textContent = original.slice(de, ate);
    caixa.append(marca);
    cursor = ate;
  }
  if (cursor < original.length) caixa.append(original.slice(cursor));
  return caixa;
};

export function initBusca(root) {
  const campo = root.querySelector("[data-busca-campo]");
  const saida = root.querySelector("[data-busca-resultados]");
  const contagem = root.querySelector("[data-busca-contagem]");
  const limpar = root.querySelector("[data-busca-limpar]");
  const painel = document.querySelector("[data-busca-esconder]");
  if (!campo || !saida) return;

  const fonte = root.dataset.src || "assets/data/busca.json";
  let indice = null;
  let baixando = null;

  const buscar = () => {
    if (!baixando) {
      baixando = fetch(fonte)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((dados) => {

          indice = [...dados.textos, ...dados.episodios].map((i) => ({
            ...i,
            _b: semAcento(`${i.t} ${i.r}`),
          }));
          return indice;
        });
      baixando.catch(() => (baixando = null));
    }
    return baixando;
  };

  const mostrar = (termo) => {
    const termos = semAcento(termo).split(/\s+/).filter((t) => t.length >= 2);
    saida.replaceChildren();

    if (!termos.length) {
      root.dataset.buscando = "nao";
      if (painel) painel.hidden = false;
      contagem.textContent = "";
      return;
    }

    const achados = indice.filter((i) => termos.every((t) => i._b.includes(t)));

    root.dataset.buscando = "sim";
    if (painel) painel.hidden = true;

    contagem.textContent = achados.length
      ? `${achados.length} ${achados.length === 1 ? "resultado" : "resultados"} para “${termo.trim()}”`
      : `nada encontrado para “${termo.trim()}”`;

    if (!achados.length) {
      const vazio = document.createElement("p");
      vazio.className = "busca__vazio";
      vazio.textContent =
        "A busca olha o título e o começo de cada texto. Tente outra palavra, " +
        "ou procure pela categoria na lista ao lado.";
      saida.append(vazio);
      return;
    }

    const lista = document.createElement("ul");
    lista.className = "busca__lista";

    for (const item of achados.slice(0, LIMITE)) {
      const li = document.createElement("li");
      const alvo =
        item.c === "episódio"
          ? `episodios.html#ep-${item.s}`
          : `escrita.html#${item.s}`;

      const link = document.createElement("a");
      link.className = "busca-item";
      link.href = alvo;
      if (item.c !== "episódio") link.dataset.slug = item.s;

      const cat = document.createElement("span");
      cat.className = "t-eyebrow busca-item__cat";
      cat.textContent = item.c;

      const titulo = document.createElement("span");
      titulo.className = "busca-item__titulo";
      titulo.append(realcar(item.t, termos));

      const data = document.createElement("time");
      data.className = "t-footnote busca-item__data tabular";
      data.dateTime = item.d;
      data.textContent = dataCurta(item.d);

      const resumo = document.createElement("span");
      resumo.className = "t-footnote busca-item__resumo";
      resumo.append(realcar(item.r, termos));

      link.append(cat, titulo, data, resumo);
      li.append(link);
      lista.append(li);
    }

    saida.append(lista);

    if (achados.length > LIMITE) {
      const nota = document.createElement("p");
      nota.className = "busca__vazio";
      nota.textContent =
        `Mostrando os ${LIMITE} mais recentes de ${achados.length}. ` +
        "Acrescente uma palavra para estreitar.";
      saida.append(nota);
    }
  };

  let agendado = null;
  campo.addEventListener("input", () => {
    const termo = campo.value;
    root.dataset.temTexto = termo.trim() ? "sim" : "nao";
    clearTimeout(agendado);

    agendado = setTimeout(() => {
      buscar()
        .then(() => mostrar(termo))
        .catch((erro) => {
          contagem.textContent = "não consegui carregar a busca.";
          console.error("[busca]", erro);
        });
    }, 140);
  });

  limpar?.addEventListener("click", () => {
    campo.value = "";
    root.dataset.temTexto = "nao";
    mostrar("");
    campo.focus();
  });

  campo.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && campo.value) {
      evento.stopPropagation();
      campo.value = "";
      root.dataset.temTexto = "nao";
      mostrar("");
    }
  });
}
