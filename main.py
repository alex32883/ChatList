"""
Основной модуль с графическим интерфейсом приложения Chatlist.
"""
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QLabel, QCheckBox, QMessageBox, QHeaderView, QProgressBar, QFileDialog, QMenuBar, QAction, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from typing import List, Dict, Optional
import db
import model
from network import send_request_to_model
import logger
from version import __version__


class RequestThread(QThread):
    """Поток для асинхронной отправки запросов к API."""
    finished = pyqtSignal(list)  # Сигнал с результатами
    progress = pyqtSignal(int, dict)  # Сигнал прогресса (model_id, result)
    status_update = pyqtSignal(str)  # Сигнал для обновления статуса
    
    def __init__(self, prompt: str, model_ids: Optional[List[int]] = None):
        super().__init__()
        self.prompt = prompt
        self.model_ids = model_ids
    
    def run(self):
        """Выполняет отправку запросов к моделям."""
        import concurrent.futures
        import threading
        
        # Получаем список моделей
        if self.model_ids:
            models = [db.get_model(mid) for mid in self.model_ids if db.get_model(mid)]
        else:
            models = model.get_active_models()
        
        if not models:
            self.finished.emit([])
            return
        
        results = []
        completed = 0
        total = len(models)
        
        # Отправляем запросы параллельно
        with concurrent.futures.ThreadPoolExecutor(max_workers=total) as executor:
            # Создаем задачи для каждой модели
            future_to_model = {}
            for model_data in models:
                future = executor.submit(self._send_single_request, model_data, self.prompt)
                future_to_model[future] = model_data
            
            # Обрабатываем результаты по мере их получения
            for future in concurrent.futures.as_completed(future_to_model):
                model_data = future_to_model[future]
                try:
                    result = future.result()
                    completed += 1
                    self.status_update.emit(f"Получен ответ от {model_data['name']} ({completed}/{total})")
                    self.progress.emit(result['model_id'], result)
                    results.append(result)
                except Exception as e:
                    # Обрабатываем ошибки
                    result = {
                        'model_id': model_data['id'],
                        'model_name': model_data['name'],
                        'response': None,
                        'error': str(e),
                        'tokens_used': None,
                        'response_time': None
                    }
                    completed += 1
                    self.status_update.emit(f"Ошибка для {model_data['name']} ({completed}/{total})")
                    self.progress.emit(result['model_id'], result)
                    results.append(result)
        
        # Отправляем все результаты
        self.finished.emit(results)
    
    def _send_single_request(self, model_data: Dict, prompt: str) -> Dict:
        """Отправляет запрос к одной модели."""
        self.status_update.emit(f"Отправка запроса к {model_data['name']}...")
        
        model_result = {
            'model_id': model_data['id'],
            'model_name': model_data['name'],
            'response': None,
            'error': None,
            'tokens_used': None,
            'response_time': None
        }
        
        # Валидация настроек модели
        is_valid, error_msg = model.validate_model_settings(model_data)
        if not is_valid:
            model_result['error'] = error_msg
            return model_result
        
        # Отправка запроса
        try:
            # Для OpenRouter используем маппинг имен моделей
            if model_data['model_type'] == 'openrouter' and model_data['name'] in model.OPENROUTER_MODEL_MAP:
                model_for_api = model_data.copy()
                model_for_api['name'] = model.OPENROUTER_MODEL_MAP[model_data['name']]
                response_data = send_request_to_model(model_for_api, prompt)
            else:
                response_data = send_request_to_model(model_data, prompt)
            
            model_result['response'] = response_data.get('response')
            model_result['tokens_used'] = response_data.get('tokens_used')
            model_result['response_time'] = response_data.get('response_time')
        except Exception as e:
            model_result['error'] = str(e)
        
        return model_result


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Chatlist - Сравнение ответов нейросетей v{__version__}")
        self.setGeometry(100, 100, 1400, 800)
        
        # Устанавливаем иконку окна
        try:
            icon_path = "app.ico"
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # Пытаемся использовать ресурсы PyQt5 если иконка не найдена
                pass
        except Exception as e:
            logger.log_error(f"Error setting window icon: {str(e)}")
        
        # Инициализация БД
        db.init_database()
        
        # Временная таблица результатов в памяти
        self.temp_results: List[Dict] = []
        self.current_prompt_id: Optional[int] = None
        
        # Поток для запросов
        self.request_thread: Optional[RequestThread] = None
        
        self.init_ui()
        self.load_saved_prompts()
        self.create_menu_bar()
        self.apply_settings()
    
    def create_menu_bar(self):
        """Создает меню приложения."""
        menubar = self.menuBar()
        
        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        
        models_action = QAction("Управление моделями", self)
        models_action.triggered.connect(self.open_models_window)
        settings_menu.addAction(models_action)
        
        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.open_settings_window)
        settings_menu.addAction(settings_action)
        
        # Меню "Просмотр"
        view_menu = menubar.addMenu("Просмотр")
        
        saved_results_action = QAction("Сохраненные результаты", self)
        saved_results_action.triggered.connect(self.open_saved_results_window)
        view_menu.addAction(saved_results_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def open_models_window(self):
        """Открывает окно управления моделями."""
        from models_window import ModelsWindow
        window = ModelsWindow(self)
        window.exec_()
        # Обновляем список моделей после закрытия окна
        logger.log_info("Models window closed, models may have been updated")
    
    def open_saved_results_window(self):
        """Открывает окно просмотра сохраненных результатов."""
        from saved_results_window import SavedResultsWindow
        window = SavedResultsWindow(self)
        window.exec_()
    
    def open_settings_window(self):
        """Открывает окно настроек."""
        from settings_window import SettingsWindow
        window = SettingsWindow(self)
        if window.exec_() == QDialog.Accepted:
            # Применяем настройки после сохранения
            self.apply_settings()
    
    def apply_settings(self):
        """Применяет настройки темы и размера шрифта."""
        # Загружаем настройки
        theme = db.get_setting('theme', 'light')
        font_size = db.get_setting('font_size', '10')
        
        try:
            font_size_int = int(font_size)
        except ValueError:
            font_size_int = 10
        
        # Применяем тему
        if theme == 'dark':
            self.apply_dark_theme(font_size_int)
        else:
            self.apply_light_theme(font_size_int)
    
    def apply_dark_theme(self, font_size: int):
        """Применяет темную тему."""
        dark_stylesheet = f"""
        QMainWindow {{
            background-color: #2b2b2b;
            color: #ffffff;
        }}
        QWidget {{
            background-color: #2b2b2b;
            color: #ffffff;
            font-size: {font_size}pt;
        }}
        QTextEdit, QLineEdit, QComboBox {{
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 5px;
            font-size: {font_size}pt;
        }}
        QPushButton {{
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: {font_size}pt;
        }}
        QPushButton:hover {{
            background-color: #106ebe;
        }}
        QPushButton:pressed {{
            background-color: #005a9e;
        }}
        QPushButton:disabled {{
            background-color: #555555;
            color: #999999;
        }}
        QTableWidget {{
            background-color: #3c3c3c;
            color: #ffffff;
            gridline-color: #555555;
            font-size: {font_size}pt;
        }}
        QHeaderView::section {{
            background-color: #404040;
            color: #ffffff;
            padding: 5px;
            border: none;
            font-size: {font_size}pt;
        }}
        QLabel {{
            color: #ffffff;
            font-size: {font_size}pt;
        }}
        QProgressBar {{
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background-color: #3c3c3c;
            color: #ffffff;
            font-size: {font_size}pt;
        }}
        QProgressBar::chunk {{
            background-color: #0078d4;
            border-radius: 3px;
        }}
        QMenuBar {{
            background-color: #2b2b2b;
            color: #ffffff;
            font-size: {font_size}pt;
        }}
        QMenuBar::item:selected {{
            background-color: #404040;
        }}
        QMenu {{
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            font-size: {font_size}pt;
        }}
        QMenu::item:selected {{
            background-color: #0078d4;
        }}
        QGroupBox {{
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            font-size: {font_size}pt;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }}
        QCheckBox {{
            color: #ffffff;
            font-size: {font_size}pt;
        }}
        """
        self.setStyleSheet(dark_stylesheet)
        # Применяем к дочерним виджетам
        for widget in self.findChildren(QWidget):
            if widget != self:
                widget.setStyleSheet("")
    
    def apply_light_theme(self, font_size: int):
        """Применяет светлую тему."""
        light_stylesheet = f"""
        QMainWindow {{
            background-color: #ffffff;
            color: #000000;
        }}
        QWidget {{
            background-color: #ffffff;
            color: #000000;
            font-size: {font_size}pt;
        }}
        QTextEdit, QLineEdit, QComboBox {{
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 5px;
            font-size: {font_size}pt;
        }}
        QPushButton {{
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: {font_size}pt;
        }}
        QPushButton:hover {{
            background-color: #106ebe;
        }}
        QPushButton:pressed {{
            background-color: #005a9e;
        }}
        QPushButton:disabled {{
            background-color: #e0e0e0;
            color: #999999;
        }}
        QTableWidget {{
            background-color: #ffffff;
            color: #000000;
            gridline-color: #e0e0e0;
            font-size: {font_size}pt;
        }}
        QHeaderView::section {{
            background-color: #f0f0f0;
            color: #000000;
            padding: 5px;
            border: none;
            font-size: {font_size}pt;
        }}
        QLabel {{
            color: #000000;
            font-size: {font_size}pt;
        }}
        QProgressBar {{
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            background-color: #ffffff;
            color: #000000;
            font-size: {font_size}pt;
        }}
        QProgressBar::chunk {{
            background-color: #0078d4;
            border-radius: 3px;
        }}
        QMenuBar {{
            background-color: #f0f0f0;
            color: #000000;
            font-size: {font_size}pt;
        }}
        QMenuBar::item:selected {{
            background-color: #e0e0e0;
        }}
        QMenu {{
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            font-size: {font_size}pt;
        }}
        QMenu::item:selected {{
            background-color: #0078d4;
            color: #ffffff;
        }}
        QGroupBox {{
            border: 1px solid #cccccc;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            font-size: {font_size}pt;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }}
        QCheckBox {{
            color: #000000;
            font-size: {font_size}pt;
        }}
        """
        self.setStyleSheet(light_stylesheet)
        # Применяем к дочерним виджетам
        for widget in self.findChildren(QWidget):
            if widget != self:
                widget.setStyleSheet("")
    
    def improve_prompt(self):
        """Открывает окно улучшения промпта."""
        prompt_text = self.prompt_input.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите промпт перед улучшением.")
            return
        
        from prompt_improvement_window import PromptImprovementDialog
        dialog = PromptImprovementDialog(self, prompt_text)
        if dialog.exec_() == QDialog.Accepted:
            selected_variant = dialog.get_selected_variant()
            if selected_variant:
                self.prompt_input.setPlainText(selected_variant)
                QMessageBox.information(
                    self, 
                    "Успех", 
                    "Выбранный вариант промпта вставлен в поле ввода."
                )
    
    def show_about(self):
        """Показывает диалоговое окно 'О программе'."""
        about_text = f"""
        <h2>Chatlist</h2>
        <p><b>Версия:</b> {__version__}</p>
        <p><b>Описание:</b></p>
        <p>Приложение для отправки одного промта в несколько нейросетей и сравнения их ответов.</p>
        <p><b>Возможности:</b></p>
        <ul>
            <li>Отправка промта в несколько моделей одновременно</li>
            <li>Улучшение промптов с помощью AI-ассистента</li>
            <li>Сохранение промтов с тегами</li>
            <li>Сохранение выбранных результатов в базу данных</li>
            <li>Экспорт результатов в Markdown и JSON</li>
            <li>Управление моделями через графический интерфейс</li>
            <li>Настройка темы оформления (светлая/темная)</li>
            <li>Настройка размера шрифта</li>
        </ul>
        <p><b>Технологии:</b> Python 3.11+, PyQt5, SQLite</p>
        <p><b>API:</b> OpenAI, Groq, OpenRouter</p>
        <p>© 2024 Chatlist Application</p>
        """
        QMessageBox.about(self, "О программе", about_text)
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # === Область ввода промта ===
        prompt_group = QWidget()
        prompt_layout = QVBoxLayout()
        prompt_group.setLayout(prompt_layout)
        
        prompt_label = QLabel("Промт:")
        prompt_layout.addWidget(prompt_label)
        
        # Поле ввода промта
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Введите ваш запрос здесь...")
        self.prompt_input.setMaximumHeight(100)
        prompt_layout.addWidget(self.prompt_input)
        
        # Выпадающий список сохраненных промтов
        saved_prompts_layout = QHBoxLayout()
        saved_prompts_label = QLabel("Сохраненные промты:")
        self.saved_prompts_combo = QComboBox()
        self.saved_prompts_combo.setEditable(True)  # Разрешаем поиск
        self.saved_prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        saved_prompts_layout.addWidget(saved_prompts_label)
        saved_prompts_layout.addWidget(self.saved_prompts_combo)
        saved_prompts_layout.addStretch()
        prompt_layout.addLayout(saved_prompts_layout)
        
        # Поле для тегов
        tags_layout = QHBoxLayout()
        tags_label = QLabel("Теги (через запятую):")
        self.tags_input = QTextEdit()
        self.tags_input.setPlaceholderText("например: наука, физика, объяснение")
        self.tags_input.setMinimumHeight(30)
        self.tags_input.setMaximumHeight(50)
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_input)
        prompt_layout.addLayout(tags_layout)
        
        # Кнопки управления промтом
        prompt_buttons_layout = QHBoxLayout()
        self.save_prompt_button = QPushButton("Сохранить промт")
        self.save_prompt_button.clicked.connect(self.save_prompt)
        self.save_prompt_button.setEnabled(True)
        
        self.improve_prompt_button = QPushButton("Улучшить промпт")
        self.improve_prompt_button.clicked.connect(self.improve_prompt)
        self.improve_prompt_button.setEnabled(True)
        
        self.send_button = QPushButton("Отправить запрос")
        self.send_button.clicked.connect(self.send_requests)
        self.send_button.setEnabled(True)
        
        self.new_request_button = QPushButton("Новый запрос")
        self.new_request_button.clicked.connect(self.new_request)
        self.new_request_button.setEnabled(False)
        
        prompt_buttons_layout.addWidget(self.save_prompt_button)
        prompt_buttons_layout.addWidget(self.improve_prompt_button)
        prompt_buttons_layout.addWidget(self.send_button)
        prompt_buttons_layout.addWidget(self.new_request_button)
        prompt_buttons_layout.addStretch()
        prompt_layout.addLayout(prompt_buttons_layout)
        
        main_layout.addWidget(prompt_group)
        
        # === Индикатор загрузки ===
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("%p% (%v/%m)")
        self.progress_status_label = QLabel("")
        self.progress_status_label.setVisible(False)
        self.progress_status_label.setStyleSheet("color: #666; font-style: italic;")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_status_label)
        progress_widget = QWidget()
        progress_widget.setLayout(progress_layout)
        main_layout.addWidget(progress_widget)
        
        # === Таблица результатов ===
        results_label = QLabel("Результаты:")
        main_layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Выбрать", "Название модели", "Текст ответа"])
        
        # Настройка таблицы
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)
        main_layout.addWidget(self.results_table)
        
        # === Кнопки управления результатами ===
        results_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить выбранные")
        self.save_button.clicked.connect(self.save_selected_results)
        self.save_button.setEnabled(False)
        
        self.open_button = QPushButton("Открыть")
        self.open_button.clicked.connect(self.open_selected_answer)
        self.open_button.setEnabled(False)
        
        results_buttons_layout.addWidget(self.save_button)
        results_buttons_layout.addWidget(self.open_button)
        results_buttons_layout.addStretch()
        main_layout.addLayout(results_buttons_layout)
        
        # === Кнопки внизу ===
        bottom_buttons_layout = QHBoxLayout()
        self.save_bottom_button = QPushButton("Сохранить")
        self.save_bottom_button.clicked.connect(self.save_selected_results)
        self.save_bottom_button.setEnabled(False)
        
        self.export_md_button = QPushButton("Экспорт в Markdown")
        self.export_md_button.clicked.connect(lambda: self.export_results('markdown'))
        self.export_md_button.setEnabled(False)
        
        self.export_json_button = QPushButton("Экспорт в JSON")
        self.export_json_button.clicked.connect(lambda: self.export_results('json'))
        self.export_json_button.setEnabled(False)
        
        self.clear_all_button = QPushButton("Очистить все")
        self.clear_all_button.clicked.connect(self.clear_all)
        self.clear_all_button.setEnabled(False)
        
        bottom_buttons_layout.addWidget(self.save_bottom_button)
        bottom_buttons_layout.addWidget(self.export_md_button)
        bottom_buttons_layout.addWidget(self.export_json_button)
        bottom_buttons_layout.addWidget(self.clear_all_button)
        bottom_buttons_layout.addStretch()
        main_layout.addLayout(bottom_buttons_layout)
    
    def load_saved_prompts(self):
        """Загружает сохраненные промты в выпадающий список."""
        self.saved_prompts_combo.clear()
        self.saved_prompts_combo.addItem("-- Выберите промт --", None)
        
        prompts = db.get_all_prompts()
        for prompt in prompts:
            display_text = f"{prompt['date']}: {prompt['prompt'][:50]}..."
            self.saved_prompts_combo.addItem(display_text, prompt['id'])
    
    def on_prompt_selected(self, index):
        """Обработчик выбора промта из списка."""
        if index > 0:  # Пропускаем первый элемент "-- Выберите промт --"
            prompt_id = self.saved_prompts_combo.itemData(index)
            if prompt_id:
                prompt_data = db.get_prompt(prompt_id)
                if prompt_data:
                    self.prompt_input.setPlainText(prompt_data['prompt'])
                    # Всегда обновляем поле тегов, даже если они пустые
                    tags = prompt_data.get('tags', '') or ''
                    self.tags_input.setPlainText(tags)
        else:
            # Если выбран "-- Выберите промт --", очищаем поля
            self.prompt_input.clear()
            self.tags_input.clear()
    
    def save_prompt(self):
        """Сохраняет промт в БД с тегами."""
        prompt_text = self.prompt_input.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите промт перед сохранением.")
            return
        
        tags = self.tags_input.toPlainText().strip()
        tags = tags if tags else None
        
        try:
            prompt_id = db.create_prompt(prompt_text, tags)
            QMessageBox.information(self, "Успех", f"Промт сохранен (ID: {prompt_id})")
            self.load_saved_prompts()
            # Выбираем только что сохраненный промт
            for i in range(self.saved_prompts_combo.count()):
                if self.saved_prompts_combo.itemData(i) == prompt_id:
                    self.saved_prompts_combo.setCurrentIndex(i)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить промт: {str(e)}")
    
    def send_requests(self):
        """Отправляет запросы ко всем активным моделям."""
        prompt_text = self.prompt_input.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите промт перед отправкой запроса.")
            return
        
        # Сохраняем промт в БД
        tags = self.tags_input.toPlainText().strip()
        tags = tags if tags else None
        self.current_prompt_id = db.create_prompt(prompt_text, tags)
        
        # Очищаем временную таблицу
        self.temp_results = []
        self.results_table.setRowCount(0)
        
        # Блокируем кнопки
        self.send_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.save_bottom_button.setEnabled(False)
        self.export_md_button.setEnabled(False)
        self.export_json_button.setEnabled(False)
        self.clear_all_button.setEnabled(False)
        self.new_request_button.setEnabled(False)
        
        # Показываем индикатор загрузки
        active_models = model.get_active_models()
        self.progress_bar.setMaximum(len(active_models))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_status_label.setText("Инициализация запросов...")
        self.progress_status_label.setVisible(True)
        
        # Запускаем поток для отправки запросов
        self.request_thread = RequestThread(prompt_text)
        self.request_thread.progress.connect(self.on_result_received)
        self.request_thread.status_update.connect(self.on_status_update)
        self.request_thread.finished.connect(self.on_requests_finished)
        self.request_thread.start()
    
    def on_result_received(self, model_id: int, result: Dict):
        """Обработчик получения результата от модели."""
        # Добавляем результат во временную таблицу
        self.temp_results.append(result)
        
        # Обновляем таблицу
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Checkbox "Выбрать" (первая колонка)
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        self.results_table.setCellWidget(row, 0, checkbox)
        
        # Название модели (вторая колонка)
        model_name_item = QTableWidgetItem(result['model_name'])
        model_name_item.setFlags(model_name_item.flags() & ~Qt.ItemIsEditable)
        self.results_table.setItem(row, 1, model_name_item)
        
        # Текст ответа или ошибка (третья колонка)
        if result['error']:
            response_text = f"Ошибка: {result['error']}"
            response_item = QTableWidgetItem(response_text)
            response_item.setForeground(Qt.red)
        else:
            response_text = result['response'] or "Нет ответа"
            response_item = QTableWidgetItem(response_text)
        response_item.setFlags(response_item.flags() & ~Qt.ItemIsEditable)
        self.results_table.setItem(row, 2, response_item)
        
        # Обновляем прогресс
        current_value = self.progress_bar.value()
        self.progress_bar.setValue(current_value + 1)
    
    def on_status_update(self, status: str):
        """Обработчик обновления статуса."""
        self.progress_status_label.setText(status)
    
    def on_requests_finished(self, results: List[Dict]):
        """Обработчик завершения всех запросов."""
        self.progress_bar.setVisible(False)
        self.progress_status_label.setVisible(False)
        self.progress_status_label.setText("")
        self.send_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.open_button.setEnabled(True)
        self.save_bottom_button.setEnabled(True)
        self.export_md_button.setEnabled(True)
        self.export_json_button.setEnabled(True)
        self.clear_all_button.setEnabled(True)
        self.new_request_button.setEnabled(True)
        
        if not results:
            QMessageBox.information(self, "Информация", "Нет активных моделей для отправки запросов.")
    
    def on_selection_changed(self):
        """Обработчик изменения выбора в таблице."""
        selected_rows = self.results_table.selectionModel().selectedRows()
        self.open_button.setEnabled(len(selected_rows) > 0)
    
    def open_selected_answer(self):
        """Открывает выбранный ответ в markdown формате."""
        selected_rows = self.results_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку с ответом для просмотра.")
            return
        
        row = selected_rows[0].row()
        
        # Получаем название модели
        model_name_item = self.results_table.item(row, 1)
        if not model_name_item:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить информацию о модели.")
            return
        
        model_name = model_name_item.text()
        
        # Находим результат во временной таблице
        result = next((r for r in self.temp_results if r['model_name'] == model_name), None)
        
        if not result:
            QMessageBox.warning(self, "Ошибка", "Результат не найден.")
            return
        
        # Открываем диалоговое окно с markdown
        dialog = MarkdownViewDialog(self, result, self.prompt_input.toPlainText())
        dialog.exec_()
    
    def save_selected_results(self):
        """Сохраняет выбранные результаты в БД."""
        if not self.current_prompt_id:
            QMessageBox.warning(self, "Ошибка", "Нет активного промта для сохранения результатов.")
            return
        
        saved_count = 0
        errors = []
        
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # Находим соответствующий результат
                model_name_item = self.results_table.item(row, 1)
                if model_name_item:
                    model_name = model_name_item.text()
                    
                    # Находим результат в temp_results
                    result = next((r for r in self.temp_results if r['model_name'] == model_name), None)
                    if not result:
                        errors.append(f"Результат для модели '{model_name}' не найден во временной таблице")
                        logger.log_error(f"Result not found for model: {model_name}")
                        continue
                    
                    if result.get('error'):
                        errors.append(f"Модель '{model_name}': {result['error']}")
                        logger.log_error(f"Model {model_name} has error: {result['error']}")
                        continue
                    
                    # Находим модель по имени
                    models = db.get_all_models()
                    model_data = next((m for m in models if m['name'] == model_name), None)
                    
                    if not model_data:
                        errors.append(f"Модель '{model_name}' не найдена в базе данных")
                        logger.log_error(f"Model not found in DB: {model_name}")
                        continue
                    
                    # Проверяем наличие ответа
                    if not result.get('response'):
                        errors.append(f"Модель '{model_name}': нет ответа для сохранения")
                        logger.log_error(f"Model {model_name} has no response")
                        continue
                    
                    try:
                        result_id = db.create_result(
                            prompt_id=self.current_prompt_id,
                            model_id=model_data['id'],
                            response=result['response'],
                            tokens_used=result.get('tokens_used'),
                            response_time=result.get('response_time')
                        )
                        saved_count += 1
                        logger.log_info(f"Saved result ID {result_id} for model {model_name}, prompt {self.current_prompt_id}")
                    except Exception as e:
                        error_msg = f"Ошибка при сохранении результата для модели '{model_name}': {str(e)}"
                        errors.append(error_msg)
                        logger.log_error(error_msg, e)
        
        if saved_count > 0:
            message = f"Сохранено результатов: {saved_count}"
            if errors:
                message += f"\n\nОшибки ({len(errors)}):\n" + "\n".join(errors[:5])  # Показываем первые 5 ошибок
            QMessageBox.information(self, "Успех", message)
            # Очищаем временную таблицу
            self.temp_results = []
            self.results_table.setRowCount(0)
            self.save_button.setEnabled(False)
            self.open_button.setEnabled(False)
            self.save_bottom_button.setEnabled(False)
            self.export_md_button.setEnabled(False)
            self.export_json_button.setEnabled(False)
            self.clear_all_button.setEnabled(False)
        else:
            error_message = "Не выбрано ни одного результата для сохранения."
            if errors:
                error_message += f"\n\nОшибки:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Предупреждение", error_message)
    
    def new_request(self):
        """Очищает форму для нового запроса."""
        self.prompt_input.clear()
        self.tags_input.clear()
        self.temp_results = []
        self.results_table.setRowCount(0)
        self.current_prompt_id = None
        self.saved_prompts_combo.setCurrentIndex(0)
        self.save_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.save_bottom_button.setEnabled(False)
        self.export_md_button.setEnabled(False)
        self.export_json_button.setEnabled(False)
        self.clear_all_button.setEnabled(False)
        self.progress_bar.setVisible(False)
    
    def clear_all(self):
        """Очищает все результаты и временные данные."""
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            "Вы уверены, что хотите очистить все результаты?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.temp_results = []
            self.results_table.setRowCount(0)
            self.save_button.setEnabled(False)
            self.open_button.setEnabled(False)
            self.save_bottom_button.setEnabled(False)
            self.export_md_button.setEnabled(False)
            self.export_json_button.setEnabled(False)
            self.clear_all_button.setEnabled(False)
    
    def export_results(self, format_type: str):
        """Экспортирует выбранные результаты в файл."""
        if not self.temp_results:
            QMessageBox.warning(self, "Предупреждение", "Нет результатов для экспорта.")
            return
        
        # Получаем выбранные результаты
        selected_results = []
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                model_name_item = self.results_table.item(row, 1)
                if model_name_item:
                    model_name = model_name_item.text()
                    result = next((r for r in self.temp_results if r['model_name'] == model_name), None)
                    if result:
                        selected_results.append(result)
        
        if not selected_results:
            QMessageBox.warning(self, "Предупреждение", "Не выбрано ни одного результата для экспорта.")
            return
        
        # Выбираем файл для сохранения
        if format_type == 'markdown':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как Markdown", "", "Markdown Files (*.md);;All Files (*)"
            )
            extension = '.md'
        else:  # json
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как JSON", "", "JSON Files (*.json);;All Files (*)"
            )
            extension = '.json'
        
        if not file_path:
            return
        
        if not file_path.endswith(extension):
            file_path += extension
        
        try:
            if format_type == 'markdown':
                self._export_to_markdown(file_path, selected_results)
            else:
                self._export_to_json(file_path, selected_results)
            QMessageBox.information(self, "Успех", f"Результаты экспортированы в {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать результаты: {str(e)}")
    
    def _export_to_markdown(self, file_path: str, results: List[Dict]):
        """Экспортирует результаты в Markdown."""
        prompt_text = self.prompt_input.toPlainText()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Результаты сравнения моделей\n\n")
            f.write(f"## Промт\n\n{prompt_text}\n\n")
            f.write(f"## Результаты\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"### {i}. {result['model_name']}\n\n")
                if result.get('error'):
                    f.write(f"**Ошибка:** {result['error']}\n\n")
                else:
                    f.write(f"{result.get('response', 'Нет ответа')}\n\n")
                    if result.get('tokens_used'):
                        f.write(f"*Токенов использовано: {result['tokens_used']}*\n\n")
                    if result.get('response_time'):
                        f.write(f"*Время ответа: {result['response_time']:.2f} сек*\n\n")
                f.write("---\n\n")
    
    def _export_to_json(self, file_path: str, results: List[Dict]):
        """Экспортирует результаты в JSON."""
        import json
        from datetime import datetime
        prompt_text = self.prompt_input.toPlainText()
        export_data = {
            'prompt': prompt_text,
            'export_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'results': results
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)


class MarkdownViewDialog(QDialog):
    """Диалоговое окно для просмотра ответа в markdown формате."""
    
    def __init__(self, parent=None, result: Dict = None, prompt: str = ""):
        super().__init__(parent)
        self.setWindowTitle(f"Ответ от {result['model_name']}")
        self.setGeometry(200, 200, 900, 700)
        self.result = result
        self.prompt = prompt
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Заголовок с информацией о модели
        header_label = QLabel(f"<h2>Ответ от: {self.result['model_name']}</h2>")
        layout.addWidget(header_label)
        
        # Промт (если есть)
        if self.prompt:
            prompt_label = QLabel("<b>Промт:</b>")
            layout.addWidget(prompt_label)
            prompt_text = QTextEdit()
            prompt_text.setPlainText(self.prompt)
            prompt_text.setReadOnly(True)
            prompt_text.setMaximumHeight(80)
            prompt_text.setStyleSheet("background-color: #f5f5f5;")
            layout.addWidget(prompt_text)
        
        # Ответ в markdown формате
        response_label = QLabel("<b>Ответ:</b>")
        layout.addWidget(response_label)
        
        response_text = QTextEdit()
        response_text.setReadOnly(True)
        
        # Форматируем ответ как markdown
        if self.result.get('error'):
            markdown_content = f"## Ошибка\n\n**{self.result['error']}**"
        else:
            response = self.result.get('response', 'Нет ответа')
            markdown_content = response
            
            # Добавляем метаданные в конец
            metadata = []
            if self.result.get('tokens_used'):
                metadata.append(f"**Токенов использовано:** {self.result['tokens_used']}")
            if self.result.get('response_time'):
                metadata.append(f"**Время ответа:** {self.result['response_time']:.2f} сек")
            
            if metadata:
                markdown_content += f"\n\n---\n\n" + " | ".join(metadata)
        
        # Устанавливаем markdown контент
        response_text.setMarkdown(markdown_content)
        
        # Настройка стилей для лучшего отображения
        response_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                padding: 10px;
            }
        """)
        
        layout.addWidget(response_text)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


def main():
    app = QApplication(sys.argv)
    
    # Устанавливаем иконку приложения
    try:
        icon_path = "app.ico"
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            logger.log_info(f"Icon file '{icon_path}' not found, using default icon")
    except Exception as e:
        logger.log_error(f"Error loading icon: {str(e)}")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
