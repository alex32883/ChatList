"""
Окно для улучшения промптов с помощью AI-ассистента.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QComboBox, QMessageBox, QProgressBar, QGroupBox, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import Dict, Optional, List
import db
import model
from network import send_request_to_model, APIError
import logger


class PromptImprovementThread(QThread):
    """Поток для асинхронного улучшения промпта."""
    finished = pyqtSignal(str)  # Сигнал с результатом улучшения
    error = pyqtSignal(str)  # Сигнал с ошибкой
    
    def __init__(self, prompt: str, model_data: Dict):
        super().__init__()
        self.prompt = prompt
        self.model_data = model_data
    
    def run(self):
        """Выполняет улучшение промпта через выбранную модель."""
        try:
            # Формируем промпт для улучшения
            improvement_prompt = f"""Проанализируй и улучшь следующий промпт для работы с AI-моделью. Верни ответ в следующем формате:

ИСХОДНЫЙ_ПРОМПТ:
[твой улучшенный вариант промпта]

ВАРИАНТ_1:
[первый вариант переформулировки]

ВАРИАНТ_2:
[второй вариант переформулировки]

ВАРИАНТ_3:
[третий вариант переформулировки - опционально, если уместно]

Оригинальный промпт:
{self.prompt}"""

            # Используем маппинг имен для OpenRouter
            if self.model_data['model_type'] == 'openrouter' and self.model_data['name'] in model.OPENROUTER_MODEL_MAP:
                model_for_api = self.model_data.copy()
                model_for_api['name'] = model.OPENROUTER_MODEL_MAP[self.model_data['name']]
                response_data = send_request_to_model(model_for_api, improvement_prompt)
            else:
                response_data = send_request_to_model(self.model_data, improvement_prompt)
            
            result = response_data.get('response', '')
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("Получен пустой ответ от модели")
        except APIError as e:
            self.error.emit(f"Ошибка API: {str(e)}")
        except Exception as e:
            self.error.emit(f"Неожиданная ошибка: {str(e)}")


class PromptImprovementDialog(QDialog):
    """Диалоговое окно для улучшения промптов."""
    
    def __init__(self, parent=None, original_prompt: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Улучшить промпт")
        self.setGeometry(200, 200, 900, 800)
        self.original_prompt = original_prompt
        self.selected_variant = None
        self.improvement_thread: Optional[PromptImprovementThread] = None
        self.init_ui()
        
        # Загружаем модели для выбора
        self.load_models()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Инструкция
        info_label = QLabel(
            "<b>Выберите модель и нажмите 'Улучшить промпт'. "
            "Модель предложит улучшенную версию и несколько вариантов переформулировки.</b>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Выбор модели
        model_layout = QHBoxLayout()
        model_label = QLabel("Модель для улучшения:")
        self.model_combo = QComboBox()
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        layout.addLayout(model_layout)
        
        # Исходный промпт
        original_group = QGroupBox("Исходный промпт:")
        original_layout = QVBoxLayout()
        self.original_text = QTextEdit()
        self.original_text.setPlainText(self.original_prompt)
        self.original_text.setReadOnly(True)
        self.original_text.setMaximumHeight(100)
        original_layout.addWidget(self.original_text)
        original_group.setLayout(original_layout)
        layout.addWidget(original_group)
        
        # Кнопка улучшения
        improve_button_layout = QHBoxLayout()
        self.improve_button = QPushButton("Улучшить промпт")
        self.improve_button.clicked.connect(self.improve_prompt)
        improve_button_layout.addStretch()
        improve_button_layout.addWidget(self.improve_button)
        improve_button_layout.addStretch()
        layout.addLayout(improve_button_layout)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Область со скроллом для результатов
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.results_layout = QVBoxLayout()
        scroll_widget.setLayout(self.results_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        self.insert_button = QPushButton("Подставить выбранный вариант")
        self.insert_button.clicked.connect(self.insert_selected)
        self.insert_button.setEnabled(False)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        
        buttons_layout.addWidget(self.insert_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_button)
        layout.addLayout(buttons_layout)
    
    def load_models(self):
        """Загружает список активных моделей OpenRouter."""
        self.model_combo.clear()
        models = db.get_active_models()
        # Фильтруем только OpenRouter модели, так как это требование
        openrouter_models = [m for m in models if m['model_type'] == 'openrouter']
        
        if not openrouter_models:
            QMessageBox.warning(
                self, 
                "Предупреждение", 
                "Нет активных моделей OpenRouter для улучшения промптов."
            )
            self.improve_button.setEnabled(False)
            return
        
        for model_data in openrouter_models:
            self.model_combo.addItem(model_data['name'], model_data)
    
    def improve_prompt(self):
        """Запускает улучшение промпта."""
        if not self.original_prompt.strip():
            QMessageBox.warning(self, "Ошибка", "Исходный промпт не может быть пустым.")
            return
        
        model_index = self.model_combo.currentIndex()
        if model_index < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите модель для улучшения.")
            return
        
        model_data = self.model_combo.itemData(model_index)
        if not model_data:
            QMessageBox.warning(self, "Ошибка", "Ошибка при получении данных модели.")
            return
        
        # Блокируем кнопку
        self.improve_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Запускаем поток
        self.improvement_thread = PromptImprovementThread(self.original_prompt, model_data)
        self.improvement_thread.finished.connect(self.on_improvement_finished)
        self.improvement_thread.error.connect(self.on_improvement_error)
        self.improvement_thread.start()
    
    def clear_results(self):
        """Очищает область результатов."""
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.selected_variant = None
        self.insert_button.setEnabled(False)
    
    def parse_improvement_result(self, text: str) -> Dict[str, str]:
        """Парсит результат улучшения на варианты."""
        result = {
            'improved': '',
            'variant_1': '',
            'variant_2': '',
            'variant_3': ''
        }
        
        lines = text.split('\n')
        current_section = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('ИСХОДНЫЙ_ПРОМПТ:') or line.startswith('УЛУЧШЕННЫЙ_ПРОМПТ:'):
                if current_section and current_text:
                    result[current_section] = '\n'.join(current_text).strip()
                current_section = 'improved'
                current_text = []
            elif line.startswith('ВАРИАНТ_1:'):
                if current_section and current_text:
                    result[current_section] = '\n'.join(current_text).strip()
                current_section = 'variant_1'
                current_text = []
            elif line.startswith('ВАРИАНТ_2:'):
                if current_section and current_text:
                    result[current_section] = '\n'.join(current_text).strip()
                current_section = 'variant_2'
                current_text = []
            elif line.startswith('ВАРИАНТ_3:'):
                if current_section and current_text:
                    result[current_section] = '\n'.join(current_text).strip()
                current_section = 'variant_3'
                current_text = []
            elif current_section and line:
                current_text.append(line)
        
        # Сохраняем последнюю секцию
        if current_section and current_text:
            result[current_section] = '\n'.join(current_text).strip()
        
        # Если парсинг не удался, просто используем весь текст как улучшенный вариант
        if not any(result.values()):
            result['improved'] = text.strip()
        
        return result
    
    def on_improvement_finished(self, result_text: str):
        """Обработчик завершения улучшения."""
        self.progress_bar.setVisible(False)
        self.improve_button.setEnabled(True)
        
        # Парсим результат
        variants = self.parse_improvement_result(result_text)
        
        # Отображаем варианты
        if variants['improved']:
            self.add_variant("Улучшенный промпт:", variants['improved'], 'improved')
        
        if variants['variant_1']:
            self.add_variant("Вариант 1:", variants['variant_1'], 'variant_1')
        
        if variants['variant_2']:
            self.add_variant("Вариант 2:", variants['variant_2'], 'variant_2')
        
        if variants['variant_3']:
            self.add_variant("Вариант 3:", variants['variant_3'], 'variant_3')
        
        # Если ничего не отобразилось, показываем весь текст
        if not any(variants.values()):
            self.add_variant("Результат улучшения:", result_text, 'improved')
    
    def add_variant(self, title: str, text: str, variant_id: str):
        """Добавляет вариант в область результатов."""
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setPlainText(text)
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(120)
        layout.addWidget(text_edit)
        
        select_button = QPushButton("Выбрать этот вариант")
        select_button.clicked.connect(lambda checked, vid=variant_id, txt=text: self.select_variant(vid, txt))
        select_button.setProperty('variant_id', variant_id)
        layout.addWidget(select_button)
        
        group.setLayout(layout)
        group.setProperty('variant_id', variant_id)
        self.results_layout.addWidget(group)
    
    def select_variant(self, variant_id: str, text: str):
        """Выбирает вариант для подстановки."""
        self.selected_variant = text
        self.insert_button.setEnabled(True)
        
        # Визуально выделяем выбранный вариант
        for i in range(self.results_layout.count()):
            item = self.results_layout.itemAt(i)
            if item.widget():
                group = item.widget()
                if isinstance(group, QGroupBox):
                    # Сбрасываем стиль всех групп
                    if group.property('variant_id') == variant_id:
                        group.setStyleSheet("QGroupBox { border: 2px solid #0078d4; background-color: #f0f8ff; }")
                    else:
                        group.setStyleSheet("")
    
    def on_improvement_error(self, error_msg: str):
        """Обработчик ошибки улучшения."""
        self.progress_bar.setVisible(False)
        self.improve_button.setEnabled(True)
        QMessageBox.critical(self, "Ошибка", f"Не удалось улучшить промпт:\n{error_msg}")
    
    def insert_selected(self):
        """Вставляет выбранный вариант в основное поле промпта."""
        if not self.selected_variant:
            QMessageBox.warning(self, "Предупреждение", "Вариант не выбран.")
            return
        
        # Эмитируем сигнал для вставки в main.py
        self.accept()
        # Сохраняем выбранный вариант в атрибуте для доступа из main.py
        self.result_variant = self.selected_variant
    
    def get_selected_variant(self) -> Optional[str]:
        """Возвращает выбранный вариант промпта."""
        return getattr(self, 'result_variant', None)

