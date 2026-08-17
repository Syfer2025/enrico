"""leitor.py — a marcação da janela de leitura, em um só lugar."""

MARCACAO = """\
      <!--
        ==================================================================
        Janela de leitura — UMA para as 577 publicações

        O <dialog> é único e reaproveitado: o esc-leitor.js troca o conteúdo
        conforme o texto pedido. 577 diálogos no HTML seriam um arquivo
        gigante para nada.

        O texto rola DENTRO da janela (.esc-leitor__scroll), então abrir uma
        publicação não muda a altura da página. Era esse o problema do
        <details> que expandia no lugar.
        ==================================================================
      -->
      <dialog class="esc-leitor" id="esc-leitor" aria-labelledby="esc-leitor-titulo">
        <article class="esc-leitor__frame">
          <header class="esc-leitor__bar">
            <div class="esc-leitor__meta">
              <p class="t-eyebrow esc-leitor__cat" data-leitor="categoria"></p>
              <time class="t-footnote esc-leitor__data tabular" data-leitor="data"></time>
            </div>
            <button class="esc-leitor__fechar" type="button" data-leitor="fechar" aria-label="Fechar leitura">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.9"
                   stroke-linecap="round" aria-hidden="true">
                <path d="M4 4l8 8M12 4l-8 8" />
              </svg>
            </button>
          </header>

          <div class="esc-leitor__scroll" data-leitor="scroll" tabindex="-1">
            <h2 class="esc-item__leitura-titulo" id="esc-leitor-titulo" data-leitor="titulo"></h2>
            <div class="esc-item__body" data-leitor="corpo"></div>
          </div>

          <footer class="esc-leitor__share">
            <p class="t-footnote esc-leitor__share-label">Compartilhar</p>
            <div class="esc-leitor__share-row">
              <!-- Botão nativo: só aparece onde o navegador tem navigator.share
                   (o JS revela). É o único caminho para Instagram e Stories —
                   o Instagram não tem endereço de compartilhamento na web, então
                   não existe botão direto honesto para ele. -->
              <button class="esc-share esc-share--nativo" type="button" data-leitor="nativo" hidden>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M12 16V3.5M8 7l4-3.5L16 7" />
                  <path d="M4.5 13v6a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-6" />
                </svg>
                <span>Compartilhar</span>
              </button>

              <a class="esc-share esc-share--whatsapp" data-leitor="whatsapp" href="#" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.347-.347.52-.52.174-.174.232-.298.347-.497.115-.198.057-.371-.058-.52-.116-.148-.66-1.595-.904-2.185-.238-.574-.48-.497-.66-.506l-.563-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.572-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884a9.82 9.82 0 0 1 6.988 2.898 9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0 0 20.464 3.488" /></svg>
                <span>WhatsApp</span>
              </a>

              <a class="esc-share esc-share--x" data-leitor="x" href="#" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>
                <span>X</span>
              </a>

              <a class="esc-share esc-share--facebook" data-leitor="facebook" href="#" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.412c0-3.025 1.792-4.696 4.533-4.696 1.313 0 2.686.236 2.686.236v2.953H15.83c-1.491 0-1.956.929-1.956 1.882v2.286h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z" /></svg>
                <span>Facebook</span>
              </a>

              <button class="esc-share esc-share--copiar" type="button" data-leitor="copiar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <rect x="9" y="9" width="11" height="11" rx="2.5" />
                  <path d="M15 5.5A2.5 2.5 0 0 0 12.5 3h-7A2.5 2.5 0 0 0 3 5.5v7A2.5 2.5 0 0 0 5.5 15" />
                </svg>
                <span data-leitor="copiar-rotulo">Copiar link</span>
              </button>
            </div>

          </footer>
        </article>
      </dialog>
"""
