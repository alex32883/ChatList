"""
Основной модуль с графическим интерфейсом приложения Chatlist.
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QLabel, QCheckBox, QMessageBox, QHeaderView, QProgressBar, QFileDialog, QMenuBar, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import List, Dict, Optional
import db
import model
import logger


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
        self.create_menu_bar()
    
    def create_menu_bar(self):
        """Создает меню приложения."""
        menubar = self.menuBar()
        
        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        
        models_action = QAction("Управление моделями", self)
        models_action.triggered.connect(self.open_models_window)
        settings_menu.addAction(models_action)
    
    def open_models_window(self):
        """Открывает окно управления моделями."""
        from models_window import ModelsWindow
        window = ModelsWindow(self)
        window.exec_()
        # Обновляем список моделей после закрытия окна
        logger.log_info("Models window closed, models may have been updated")
    
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
        self.tags_input.setMaximumHeight(30)
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_input)
        prompt_layout.addLayout(tags_layout)
        
        # Кнопки управления промтом
        prompt_buttons_layout = QHBoxLayout()
        self.save_prompt_button = QPushButton("Сохранить промт")
        self.save_prompt_button.clicked.connect(self.save_prompt)
        self.save_prompt_button.setEnabled(True)
        
        self.send_button = QPushButton("Отправить запрос")
        self.send_button.clicked.connect(self.send_requests)
        self.send_button.setEnabled(True)
        
        self.new_request_button = QPushButton("Новый запрос")
        self.new_request_button.clicked.connect(self.new_request)
        self.new_request_button.setEnabled(False)
        
        prompt_buttons_layout.addWidget(self.save_prompt_button)
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
                    if prompt_data.get('tags'):
                        self.tags_input.setPlainText(prompt_data['tags'])
    
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
        self.export_md_button.setEnabled(True)
        self.export_json_button.setEnabled(True)
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


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
