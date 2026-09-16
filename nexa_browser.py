import os
import sys
import math  # Moved to the top to fix the NameError in draw_nexa_star_logo
from PyQt5.QtCore import QPointF, QRectF, QSize, QUrl, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPixmap
)
from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import (
    QAction, QApplication, QComboBox, QDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton, QToolBar,
    QVBoxLayout, QWidget
)

SEARCH_ENGINES = {
    "DuckDuckGo (Default)": "https://html.duckduckgo.com/html/?q=",
    "SearXNG (Open Source)": "https://searx.be/search?q=",
    "Wikipedia": "https://en.wikipedia.org/w/index.php?search="
}

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# ------------------------------------------------------------------- #
# DYNAMIC GRAPHICS: Purple & Magenta 5-Point Gradient Star Logo       #
# ------------------------------------------------------------------- #
def draw_nexa_star_logo(size=36):
    """Generates a custom 5-corner star with a double purple-to-magenta gradient."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 1. Outer Star Path
    path = QPainterPath()
    center = size / 2.0
    r_outer = size * 0.45
    r_inner = size * 0.20

    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = (i * 36 - 90) * (3.14159 / 180.0)
        x = center + r * math.cos(angle)
        y = center + r * math.sin(angle)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()

    # 2. Linear Double Gradient (Purple #8A2BE2 -> Magenta #FF007F)
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#8A2BE2"))  # Deep Purple
    gradient.setColorAt(0.5, QColor("#D100D1"))  # Vivid Violet
    gradient.setColorAt(1.0, QColor("#FF007F"))  # Bright Magenta

    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.NoPen)
    painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)


class NexaSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nexa Engine Settings")
        self.resize(380, 200)

        layout = QFormLayout()
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(list(SEARCH_ENGINES.keys()))
        layout.addRow("Default Search Engine:", self.engine_combo)

        self.homepage_input = QLineEdit("https://html.duckduckgo.com")
        layout.addRow("Homepage URL:", self.homepage_input)

        self.clear_cache_btn = QPushButton("Clear Session & Cookies")
        self.clear_cache_btn.clicked.connect(self.clear_data)
        layout.addRow("Privacy:", self.clear_cache_btn)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.accept)
        layout.addRow(self.save_btn)
        self.setLayout(layout)

    def clear_data(self):
        profile = QWebEngineProfile.defaultProfile()
        profile.clearHttpCache()
        profile.cookieStore().deleteAllCookies()
        QMessageBox.information(self, "Nexa Privacy", "Session data cleared!")


class NexaBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nexa Browser")
        self.setGeometry(100, 100, 1280, 800)

        # Config persistent user session storage
        storage_path = os.path.join(os.path.expanduser("~"), ".nexa_browser_profile")
        self.profile = QWebEngineProfile("NexaProfile", self)
        self.profile.setPersistentStoragePath(storage_path)
        self.profile.setCachePath(storage_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        self.profile.setHttpUserAgent(DEFAULT_USER_AGENT)

        # Central Layout
        main_layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Top Navigation & Header Bar
        toolbar = QToolBar()
        main_layout.addWidget(toolbar)

        # --- LOGO SYMBOL ---
        star_icon = draw_nexa_star_logo(36)
        logo_label = QLabel()
        logo_label.setPixmap(star_icon.pixmap(32, 32))
        logo_label.setContentsMargins(5, 0, 10, 0)
        toolbar.addWidget(logo_label)

        # Navigation Controls
        self.back_btn = QPushButton("←")
        self.back_btn.clicked.connect(lambda: self.browser.back())
        toolbar.addWidget(self.back_btn)

        self.forward_btn = QPushButton("→")
        self.forward_btn.clicked.connect(lambda: self.browser.forward())
        toolbar.addWidget(self.forward_btn)

        self.reload_btn = QPushButton("↻")
        self.reload_btn.clicked.connect(lambda: self.browser.reload())
        toolbar.addWidget(self.reload_btn)

        # Address / Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search with Nexa or type a URL...")
        self.search_bar.returnPressed.connect(self.process_query)
        toolbar.addWidget(self.search_bar)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.process_query)
        toolbar.addWidget(self.search_btn)

        # Settings
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.clicked.connect(self.open_settings)
        toolbar.addWidget(self.settings_btn)

        # --- RIGHT UPPER CORNER: GOOGLE-STYLE PROFILE ICON ---
        self.profile_btn = QPushButton("👤 Profile")
        self.profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #8A2BE2;
                color: white;
                border-radius: 14px;
                padding: 5px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF007F;
            }
        """)
        self.profile_menu = QMenu(self)
        
        # Account Dropdown Actions
        google_signin_action = QAction("🔑 Sign In / Manage Google Account", self)
        google_signin_action.triggered.connect(lambda: self.browser.setUrl(QUrl("https://accounts.google.com")))
        
        gmail_action = QAction("📧 Open Gmail Inbox", self)
        gmail_action.triggered.connect(lambda: self.browser.setUrl(QUrl("https://mail.google.com")))
        
        clear_session_action = QAction("🚪 Sign Out / Clear Sessions", self)
        clear_session_action.triggered.connect(self.sign_out)
        
        self.profile_menu.addAction(google_signin_action)
        self.profile_menu.addAction(gmail_action)
        self.profile_menu.addSeparator()
        self.profile_menu.addAction(clear_session_action)
        self.profile_btn.setMenu(self.profile_menu)
        toolbar.addWidget(self.profile_btn)

        # Main Browser Engine View - Bound explicitly to the configured profile
        self.browser = QWebEngineView()
        web_page = QWebEnginePage(self.profile, self.browser)
        self.browser.setPage(web_page)
        
        self.current_engine_prefix = SEARCH_ENGINES["DuckDuckGo (Default)"]
        self.browser.setUrl(QUrl("https://html.duckduckgo.com"))
        self.browser.urlChanged.connect(self.update_address_bar)
        main_layout.addWidget(self.browser)

    def process_query(self):
        text = self.search_bar.text().strip()
        if not text:
            return
        if text.startswith("http://") or text.startswith("https://"):
            url = text
        elif "." in text and " " not in text:
            url = f"https://{text}"
        else:
            formatted_query = text.replace(" ", "+")
            url = f"{self.current_engine_prefix}{formatted_query}"
        self.browser.setUrl(QUrl(url))

    def update_address_bar(self, qurl):
        self.search_bar.setText(qurl.toString())

    def open_settings(self):
        dialog = NexaSettingsDialog(self)
        if dialog.exec_():
            selected = dialog.engine_combo.currentText()
            self.current_engine_prefix = SEARCH_ENGINES[selected]
            hp = dialog.homepage_input.text().strip()
            if hp:
                self.browser.setUrl(QUrl(hp))

    def sign_out(self):
        self.profile.cookieStore().deleteAllCookies()
        QMessageBox.information(self, "Nexa Profile", "Logged out of all accounts and cleared session tokens.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexaBrowser()
    window.show()
    sys.exit(app.exec_())
