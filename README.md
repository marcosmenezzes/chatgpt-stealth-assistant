# chatgpt-stealth-assistant
O ChatGPT Invisível para macOS é uma ferramenta de produtividade projetada para integrar o acesso ao ChatGPT diretamente ao fluxo de trabalho do sistema operacional de forma discreta, rápida e automatizada.

Aplicativo desktop nativo desenvolvido em Python utilizando o framework PyObjC (AppKit e WebKit), projetado para executar o ChatGPT em uma janela segura com recursos avançados de automação de fluxo, incluindo OCR de tela via inteligência artificial nativa do sistema e injeção de comandos.

Arquitetura e Funcionamento
O sistema opera através de um loop contínuo em segundo plano gerenciado pelos componentes nativos do macOS:

Monitoramento do Clipboard: Um timer do AppKit (NSTimer) verifica a cada 1 segundo se houve alteração no contador de mudanças do NSPasteboard geral.

Identificação e Tratamento de Conteúdo:

Texto Direto: Caso o conteúdo copiado (Cmd + C) seja texto, ele é capturado diretamente.

Captura de Tela (OCR): Caso seja um print de tela (Cmd + Ctrl + Shift + 4), a imagem é extraída da área de transferência, convertida para NSBitmapImageRep e submetida ao framework Vision (VNImageRequestHandler + VNRecognizeTextRequest) para extração de texto de alta precisão com suporte a múltiplos idiomas (pt-BR e en-US).

Injeção de Automação (WebKit): O conteúdo obtido é injetado programaticamente no elemento DOM do campo de texto do ChatGPT (WKWebView) através da execução de scripts JavaScript. Os eventos de input e change são disparados nativamente e o botão de envio é ativado e acionado de forma automatizada.

Auto-Scroll Dinâmico: Um temporizador executa varreduras periódicas nos elementos de rolagem da página para garantir que a resposta gerada pelo modelo seja acompanhada automaticamente até o término da geração.

Privacidade Visual: A janela é configurada com a política de compartilhamento NSWindowSharingNone, garantindo que o conteúdo permaneça oculto em capturas de tela do sistema ou transmissões de vídeo.

Trechos Principais do Código
1. Processamento de OCR com o Framework Vision
Este método recebe um CGImage obtido do clipboard e utiliza o motor de reconhecimento de texto do macOS para extrair o conteúdo textual:

Python
def ocr_from_cg_image(self, cg_image):
    try:
        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        try:
            request.setRecognitionLanguages_(["pt-BR", "en-US"])
        except Exception:
            pass
        success, error = handler.performRequests_error_([request], None)
        if not success:
            return ""
        results = []
        for result in request.results():
            top_candidate = result.topCandidates_(1)[0]
            results.append(top_candidate.string())
        return "\n".join(results)
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return ""
        
2. Injeção de JavaScript para Auto-Prompt e Auto-Scroll
Responsável por manipular o DOM da interface web do ChatGPT, preencher o prompt, simular o clique no botão de envio e forçar a rolagem contínua para baixo:


def send_to_chatgpt(self, text):
    json_text = json.dumps(text)
    js_code = f"""
    (function() {{
        let promptText = {json_text};
        let area = document.querySelector('#prompt-textarea') || document.querySelector('div[contenteditable="true"]');
        if (area) {{
            area.focus();
            if (area.tagName === 'TEXTAREA') {{
                area.value = promptText;
            }} else {{
                area.innerText = promptText;
            }}
            area.dispatchEvent(new Event('input', {{ bubbles: true }}));
            area.dispatchEvent(new Event('change', {{ bubbles: true }}));
            setTimeout(() => {{
                let btn = document.querySelector('button[data-testid="send-button"]') || 
                          document.querySelector('button[data-testid="fruitjuice-send-button"]') ||
                          document.querySelector('button[aria-label*="Send"]') ||
                          document.querySelector('button[aria-label*="Enviar"]');
                if (btn) {{
                    btn.disabled = false;
                    btn.click();                   
                    let scrollCount = 0;
                    let scrollInterval = setInterval(() => {{
                        window.scrollTo(0, document.body.scrollHeight);
                        let scrollers = document.querySelectorAll('main, [class*="react-scroll-to-bottom"], [class*="overflow-y-auto"]');
                        scrollers.forEach(el => {{ el.scrollTop = el.scrollHeight; }});                        
                        scrollCount++;
                        if (scrollCount > 60) clearInterval(scrollInterval);
                    }}, 500);
                }}
            }}, 300);
        }}
    }})();
    """
    self.web_view.evaluateJavaScript_completionHandler_(js_code, None)
    
Requisitos do Sistema
Sistema Operacional: macOS (compatível com arquitetura Intel e Apple Silicon M1/M2/M3/M4)

Linguagem: Python 3.8+

Instalação e Execução
1. Criar e acessar o diretório do projeto
Abra o Terminal e execute os comandos abaixo:

Bash
cd "$HOME"
mkdir chatgpt_invisivel
cd chatgpt_invisivel

2. Configurar o ambiente virtual
Bash
python3 -m venv venv
source venv/bin/activate

4. Instalar as dependências do PyObjC
Bash
pip install --upgrade pip
pip install pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-WebKit pyobjc-framework-Vision pyobjc-framework-Quartz

5. Executar a aplicação
Salve o código principal como chatgpt_invisivel.py dentro da pasta do projeto e inicie o script:

Bash
python chatgpt_invisivel.py
