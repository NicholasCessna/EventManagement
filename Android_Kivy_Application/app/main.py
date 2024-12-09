from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform
from kivy.clock import mainthread

if platform == "android":
    from jnius import autoclass

    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')

class WebViewApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if platform == "android":
            self.webview = WebView(PythonActivity.mActivity)
            self.webview.getSettings().setJavaScriptEnabled(True)
            self.webview.setWebViewClient(WebViewClient())
            self.add_widget(self.webview)
            self.load_url("https://eventmanagement-153p.onrender.com/")

    @mainthread
    def load_url(self, url):
        if platform == "android":
            self.webview.loadUrl(url)

class MyApp(App):
    def build(self):
        return WebViewApp()

if __name__ == '__main__':
    MyApp().run()
