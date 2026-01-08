"""
Окно настроек приложения.
Позволяет выбрать тему (светлая/темная) и размер шрифта.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt
import db
import logger


class SettingsWindow(QDialog):
    """Окно настроек приложения."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setGeometry(300, 300, 500, 300)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Группа "Тема"
        theme_group = QGroupBox("Тема оформления")
        theme_layout = QVBoxLayout()
        
        theme_label = QLabel("Выберите тему:")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Темная", "dark")
        theme_layout.addWidget(self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Группа "Размер шрифта"
        font_group = QGroupBox("Размер шрифта")
        font_layout = QVBoxLayout()
        
        font_label = QLabel("Размер шрифта для панелей (8-24 pt):")
        font_layout.addWidget(font_label)
        
        font_size_layout = QHBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(24)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setSuffix(" pt")
        font_size_layout.addWidget(self.font_size_spin)
        font_size_layout.addStretch()
        font_layout.addLayout(font_size_layout)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_settings)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
    
    def load_settings(self):
        """Загружает настройки из базы данных."""
        # Загружаем тему
        theme = db.get_setting('theme', 'light')
        if theme == 'dark':
            index = 1
        else:
            index = 0
        self.theme_combo.setCurrentIndex(index)
        
        # Загружаем размер шрифта
        font_size = db.get_setting('font_size', '10')
        try:
            font_size_int = int(font_size)
            if 8 <= font_size_int <= 24:
                self.font_size_spin.setValue(font_size_int)
        except ValueError:
            pass
    
    def save_settings(self):
        """Сохраняет настройки в базу данных."""
        # Сохраняем тему
        theme = self.theme_combo.currentData()
        db.set_setting('theme', theme)
        
        # Сохраняем размер шрифта
        font_size = str(self.font_size_spin.value())
        db.set_setting('font_size', font_size)
        
        logger.log_info(f"Settings saved: theme={theme}, font_size={font_size}")
        QMessageBox.information(
            self, 
            "Сохранено", 
            "Настройки сохранены. Перезапустите приложение для применения изменений."
        )
        self.accept()


