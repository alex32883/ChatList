"""
Основной модуль с графическим интерфейсом приложения Chatlist.
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QLabel, QCheckBox, QMessageBox, QHeaderView, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import List, Dict, Optional
import db
import model


class RequestThread(QThread):
    """Поток для асинхронной отправки запросов к API."""
    finished = pyqtSignal(list)  # Сигнал с результатами
    progress = pyqtSignal(int, dict)  # Сигнал прогресса (model_id, result)
    
    def __init__(self, prompt: str, model_ids: Optional[List[int]] = None):
        super().__init__()
        self.prompt = prompt
        self.model_ids = model_ids
    
    def run(self):
        """Выполняет отправку запросов к моделям."""
        results = model.send_prompt_to_models(self.prompt, self.model_ids)
        
        # Отправляем результаты по мере получения
        for result in results:
            self.progress.emit(result['model_id'], result)
        
        # Отправляем все результаты
        self.finished.emit(results)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chatlist - Сравнение ответов нейросетей")
        self.setGeometry(100, 100, 1400, 800)
        
        # Инициализация БД
        db.init_database()
        
        # Временная таблица результатов в памяти
        self.temp_results: List[Dict] = []
        self.current_prompt_id: Optional[int] = None
        
        # Поток для запросов
        self.request_thread: Optional[RequestThread] = None
        
        self.init_ui()
        self.load_saved_prompts()
    
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
        self.saved_prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        saved_prompts_layout.addWidget(saved_prompts_label)
        saved_prompts_layout.addWidget(self.saved_prompts_combo)
        saved_prompts_layout.addStretch()
        prompt_layout.addLayout(saved_prompts_layout)
        
        # Кнопки управления промтом
        prompt_buttons_layout = QHBoxLayout()
        self.send_button = QPushButton("Отправить запрос")
        self.send_button.clicked.connect(self.send_requests)
        self.send_button.setEnabled(True)
        
        self.new_request_button = QPushButton("Новый запрос")
        self.new_request_button.clicked.connect(self.new_request)
        self.new_request_button.setEnabled(False)
        
        prompt_buttons_layout.addWidget(self.send_button)
        prompt_buttons_layout.addWidget(self.new_request_button)
        prompt_buttons_layout.addStretch()
        prompt_layout.addLayout(prompt_buttons_layout)
        
        main_layout.addWidget(prompt_group)
        
        # === Индикатор загрузки ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
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
        main_layout.addWidget(self.results_table)
        
        # === Кнопки управления результатами ===
        results_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить выбранные")
        self.save_button.clicked.connect(self.save_selected_results)
        self.save_button.setEnabled(False)
        
        results_buttons_layout.addWidget(self.save_button)
        results_buttons_layout.addStretch()
        main_layout.addLayout(results_buttons_layout)
        
        # === Кнопки внизу ===
        bottom_buttons_layout = QHBoxLayout()
        self.save_bottom_button = QPushButton("Сохранить")
        self.save_bottom_button.clicked.connect(self.save_selected_results)
        self.save_bottom_button.setEnabled(False)
        
        self.clear_all_button = QPushButton("Очистить все")
        self.clear_all_button.clicked.connect(self.clear_all)
        self.clear_all_button.setEnabled(False)
        
        bottom_buttons_layout.addWidget(self.save_bottom_button)
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
    
    def send_requests(self):
        """Отправляет запросы ко всем активным моделям."""
        prompt_text = self.prompt_input.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите промт перед отправкой запроса.")
            return
        
        # Сохраняем промт в БД
        tags = None  # Можно добавить поле для тегов позже
        self.current_prompt_id = db.create_prompt(prompt_text, tags)
        
        # Очищаем временную таблицу
        self.temp_results = []
        self.results_table.setRowCount(0)
        
        # Блокируем кнопки
        self.send_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.save_bottom_button.setEnabled(False)
        self.clear_all_button.setEnabled(False)
        self.new_request_button.setEnabled(False)
        
        # Показываем индикатор загрузки
        active_models = model.get_active_models()
        self.progress_bar.setMaximum(len(active_models))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Запускаем поток для отправки запросов
        self.request_thread = RequestThread(prompt_text)
        self.request_thread.progress.connect(self.on_result_received)
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
        self.progress_bar.setValue(self.progress_bar.value() + 1)
    
    def on_requests_finished(self, results: List[Dict]):
        """Обработчик завершения всех запросов."""
        self.progress_bar.setVisible(False)
        self.send_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.save_bottom_button.setEnabled(True)
        self.clear_all_button.setEnabled(True)
        self.new_request_button.setEnabled(True)
        
        if not results:
            QMessageBox.information(self, "Информация", "Нет активных моделей для отправки запросов.")
    
    def save_selected_results(self):
        """Сохраняет выбранные результаты в БД."""
        if not self.current_prompt_id:
            QMessageBox.warning(self, "Ошибка", "Нет активного промта для сохранения результатов.")
            return
        
        saved_count = 0
        
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # Находим соответствующий результат
                model_name_item = self.results_table.item(row, 1)
                if model_name_item:
                    model_name = model_name_item.text()
                    
                    # Находим результат в temp_results
                    result = next((r for r in self.temp_results if r['model_name'] == model_name), None)
                    if result and not result.get('error'):
                        # Находим модель по имени
                        models = db.get_all_models()
                        model_data = next((m for m in models if m['name'] == model_name), None)
                        
                        if model_data:
                            db.create_result(
                                prompt_id=self.current_prompt_id,
                                model_id=model_data['id'],
                                response=result['response'],
                                tokens_used=result.get('tokens_used'),
                                response_time=result.get('response_time')
                            )
                            saved_count += 1
        
        if saved_count > 0:
            QMessageBox.information(self, "Успех", f"Сохранено результатов: {saved_count}")
            # Очищаем временную таблицу
            self.temp_results = []
            self.results_table.setRowCount(0)
            self.save_button.setEnabled(False)
            self.save_bottom_button.setEnabled(False)
            self.clear_all_button.setEnabled(False)
        else:
            QMessageBox.warning(self, "Предупреждение", "Не выбрано ни одного результата для сохранения.")
    
    def new_request(self):
        """Очищает форму для нового запроса."""
        self.prompt_input.clear()
        self.temp_results = []
        self.results_table.setRowCount(0)
        self.current_prompt_id = None
        self.saved_prompts_combo.setCurrentIndex(0)
        self.save_button.setEnabled(False)
        self.save_bottom_button.setEnabled(False)
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
            self.save_bottom_button.setEnabled(False)
            self.clear_all_button.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
