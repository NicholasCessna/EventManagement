# main.py kivy app to build android app
# Need to update logic for loading screen to stay until URL fully loads. 
# Cathy loading Image flashes with black screen to load. 
# OnRender URL doesnt load very fast. Would use a better solution for actual deployment.

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image
from webviewone import WebView  


class LoadingScreen(ModalView):
    """A modal view for showing a cathedral loading image."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_dismiss = False  
        self.size_hint = (1, 1)  
        self.background = ""  
        self.add_widget(Image(source="assets/loading.png", allow_stretch=True, keep_ratio=False))


class WebViewLauncher(Widget):
    """A custom widget to launch WebView after splash screen"""

    def __init__(self, url, loading_screen, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.browser = None
        self.loading_screen = loading_screen  
        Clock.schedule_once(self.open_webview, 0.5)

    def open_webview(self, *args):
        """Creates WebView Instance and calls the loading screen while URL loads"""
        self.browser = WebView(
            url=self.url,
            enable_javascript=True,
            enable_zoom=True
        )
        
        self.loading_screen.open()
        self.browser.bind(on_load_start=self.on_load_start, on_load_finish=self.on_load_finish)
        self.browser.open()

    def on_load_start(self, *args):
        """Triggered when WebView starts loading."""
        if not self.loading_screen.is_open:
            self.loading_screen.open()

    def on_load_finish(self, *args):
        """Triggered when WebView finishes loading."""
        if self.loading_screen.is_open:
            self.loading_screen.dismiss()


class BrowserApp(App):
    def build(self):
        
        self.root_layout = BoxLayout(orientation="vertical")
        self.loading_screen = LoadingScreen()
        self.root_layout.add_widget(WebViewLauncher(
            url="https://eventmanagement-153p.onrender.com",
            loading_screen=self.loading_screen
        ))
        return self.root_layout

    def on_pause(self):
        """Pause the WebView when the app is paused."""
        if hasattr(self, "browser") and self.browser:
            self.browser.pause()
        return True

    def on_resume(self):
        """Resume the WebView when the app resumes."""
        if hasattr(self, "browser") and self.browser:
            self.browser.resume()



BrowserApp().run()