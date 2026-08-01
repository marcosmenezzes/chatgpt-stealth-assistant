import sys
import json
import AppKit
import Foundation
from WebKit import WKWebView, WKWebViewConfiguration
from Foundation import NSURL, NSURLRequest

try:
    import Vision
    import Quartz
    HAS_VISION = True
except ImportError:
    HAS_VISION = False

NSWindowSharingNone = 0

class InvisibleChatGPTApp:
    def __init__(self):
        self.app = AppKit.NSApplication.sharedApplication()
        self.app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)

        self.setup_menu()

        # Janela com proteção contra compartilhamento de tela (NSWindowSharingNone)
        rect = AppKit.NSMakeRect(100, 100, 950, 750)
        style_mask = (
            AppKit.NSWindowStyleMaskTitled |
            AppKit.NSWindowStyleMaskClosable |
            AppKit.NSWindowStyleMaskResizable |
            AppKit.NSWindowStyleMaskMiniaturizable
        )

        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style_mask, AppKit.NSBackingStoreBuffered, False
        )
        self.window.setTitle_("ChatGPT (Oculto + Auto-Prompt + OCR + Auto-Scroll)")
        self.window.setSharingType_(NSWindowSharingNone)
        self.window.setLevel_(3)  # Sempre visível no topo

        config = WKWebViewConfiguration.alloc().init()
        self.web_view = WKWebView.alloc().initWithFrame_configuration_(
            self.window.contentView().bounds(), config
        )
        self.web_view.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable
        )

        url = NSURL.URLWithString_("https://chatgpt.com")
        request = NSURLRequest.requestWithURL_(url)
        self.web_view.loadRequest_(request)

        self.window.contentView().addSubview_(self.web_view)
        self.window.makeKeyAndOrderFront_(None)

        # Monitor da Área de Transferência (Clipboard)
        self.pasteboard = AppKit.NSPasteboard.generalPasteboard()
        self.last_change_count = self.pasteboard.changeCount()

        # Verifica a área de transferência a cada 1 segundo
        self.timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, "check_clipboard:", None, True
        )
        print("🟢 Aplicativo iniciado (Monitorando Prints/Texto + Auto-Scroll ativado)...")

    def check_clipboard_(self, timer):
        try:
            current_count = self.pasteboard.changeCount()
            if current_count != self.last_change_count:
                self.last_change_count = current_count
                
                # 1. Tenta ler texto (Cmd + C)
                text = self.pasteboard.stringForType_(AppKit.NSPasteboardTypeString)
                if text and len(text.strip()) > 3:
                    print("📋 Texto detectado no clipboard! Enviando ao ChatGPT...")
                    self.send_to_chatgpt(text.strip())
                    return

                # 2. Tenta ler imagem (Cmd + Ctrl + Shift + 4)
                if HAS_VISION:
                    image = AppKit.NSImage.alloc().initWithPasteboard_(self.pasteboard)
                    if image and image.isValid():
                        print("📸 Imagem detectada no clipboard! Processando OCR...")
                        tiff_data = image.TIFFRepresentation()
                        if tiff_data:
                            bitmap = AppKit.NSBitmapImageRep.imageRepWithData_(tiff_data)
                            if bitmap:
                                cg_image = bitmap.CGImage()
                                if cg_image:
                                    extracted_text = self.ocr_from_cg_image(cg_image)
                                    if extracted_text and len(extracted_text.strip()) > 3:
                                        print(f"✅ OCR bem-sucedido:\n{extracted_text[:100]}...\n")
                                        self.send_to_chatgpt(extracted_text.strip())
                                        return
        except Exception as e:
            print(f"Erro no monitor do clipboard: {e}")

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
                        
                        // NOVIDADE: Forçar a rolagem para baixo enquanto a resposta gera
                        let scrollCount = 0;
                        let scrollInterval = setInterval(() => {{
                            window.scrollTo(0, document.body.scrollHeight);
                            let scrollers = document.querySelectorAll('main, [class*="react-scroll-to-bottom"], [class*="overflow-y-auto"]');
                            scrollers.forEach(el => {{ el.scrollTop = el.scrollHeight; }});
                            
                            scrollCount++;
                            // Para de rolar após 30 segundos (tempo suficiente para a resposta terminar)
                            if (scrollCount > 60) clearInterval(scrollInterval);
                        }}, 500);
                    }}
                }}, 300);
            }}
        }})();
        """
        self.web_view.evaluateJavaScript_completionHandler_(js_code, None)

    def setup_menu(self):
        main_menu = AppKit.NSMenu.alloc().init()

        app_menu_item = AppKit.NSMenuItem.alloc().init()
        app_menu = AppKit.NSMenu.alloc().init()
        app_menu_item.setSubmenu_(app_menu)
        main_menu.addItem_(app_menu_item)

        edit_menu_item = AppKit.NSMenuItem.alloc().init()
        edit_menu = AppKit.NSMenu.alloc().initWithTitle_("Editar")

        edit_menu.addItemWithTitle_action_keyEquivalent_("Desfazer", "undo:", "z")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Refazer", "redo:", "Z")
        edit_menu.addItem_(AppKit.NSMenuItem.separatorItem())
        edit_menu.addItemWithTitle_action_keyEquivalent_("Recortar", "cut:", "x")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Copiar", "copy:", "c")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Colar", "paste:", "v")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Selecionar Tudo", "selectAll:", "a")

        edit_menu_item.setSubmenu_(edit_menu)
        main_menu.addItem_(edit_menu_item)

        self.app.setMainMenu_(main_menu)

    def run(self):
        self.app.run()

if __name__ == "__main__":
    app = InvisibleChatGPTApp()
    app.run()
