"""
Окно для просмотра сохраненных результатов из базы данных.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QHeaderView,
    QDialogButtonBox, QTextEdit
)
from PyQt5.QtCore import Qt
from typing import List, Dict
import db
from main import MarkdownViewDialog


class SavedResultsWindow(QDialog):
    """Окно для просмотра сохраненных результатов."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сохраненные результаты")
        self.setGeometry(200, 200, 1000, 700)
        self.init_ui()
        self.load_prompts()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Выбор промта
        prompt_layout = QHBoxLayout()
        prompt_label = QLabel("Выберите промт:")
        self.prompts_combo = QComboBox()
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(self.prompts_combo)
        prompt_layout.addStretch()
        layout.addLayout(prompt_layout)
        
        # Таблица результатов
        results_label = QLabel("Сохраненные результаты:")
        layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Модель", "Дата сохранения", "Токены", "Время ответа"
        ])
        
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.itemDoubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.results_table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.view_button = QPushButton("Просмотреть")
        self.view_button.clicked.connect(self.view_selected_result)
        self.view_button.setEnabled(False)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_selected_result)
        self.delete_button.setEnabled(False)
        
        buttons_layout.addWidget(self.view_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Подключение сигнала выбора
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Кнопки диалога
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_prompts(self):
        """Загружает список промтов."""
        self.prompts_combo.clear()
        self.prompts_combo.addItem("-- Все промты --", None)
        
        prompts = db.get_all_prompts()
        for prompt in prompts:
            display_text = f"{prompt['date']}: {prompt['prompt'][:50]}..."
            self.prompts_combo.addItem(display_text, prompt['id'])
    
    def on_prompt_selected(self, index):
        """Обработчик выбора промта."""
        if index == 0:  # "Все промты"
            self.load_all_results()
        else:
            prompt_id = self.prompts_combo.itemData(index)
            if prompt_id:
                self.load_results_for_prompt(prompt_id)
    
    def load_all_results(self):
        """Загружает все сохраненные результаты."""
        results = db.get_all_results()
        self.display_results(results)
    
    def load_results_for_prompt(self, prompt_id: int):
        """Загружает результаты для конкретного промта."""
        results = db.get_results_by_prompt(prompt_id)
        self.display_results(results)
    
    def display_results(self, results: List[Dict]):
        """Отображает результаты в таблице."""
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # Модель
            model_name = result.get('model_name', 'Неизвестно')
            model_item = QTableWidgetItem(model_name)
            model_item.setData(Qt.UserRole, result)  # Сохраняем весь результат
            model_item.setFlags(model_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 0, model_item)
            
            # Дата сохранения
            saved_date = result.get('saved_date', '')
            date_item = QTableWidgetItem(saved_date)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 1, date_item)
            
            # Токены
            tokens = result.get('tokens_used')
            tokens_item = QTableWidgetItem(str(tokens) if tokens else '-')
            tokens_item.setFlags(tokens_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 2, tokens_item)
            
            # Время ответа
            response_time = result.get('response_time')
            time_item = QTableWidgetItem(
                f"{response_time:.2f} сек" if response_time else '-'
            )
            time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 3, time_item)
    
    def on_selection_changed(self):
        """Обработчик изменения выбора."""
        selected_rows = self.results_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.view_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def on_row_double_clicked(self, item):
        """Обработчик двойного клика по строке."""
        self.view_selected_result()
    
    def view_selected_result(self):
        """Просматривает выбранный результат."""
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        model_item = self.results_table.item(row, 0)
        if not model_item:
            return
        
        result = model_item.data(Qt.UserRole)
        if not result:
            return
        
        # Получаем промт
        prompt_id = result.get('prompt_id')
        prompt_text = ""
        if prompt_id:
            prompt_data = db.get_prompt(prompt_id)
            if prompt_data:
                prompt_text = prompt_data.get('prompt', '')
        
        # Формируем результат в нужном формате для MarkdownViewDialog
        formatted_result = {
            'model_name': result.get('model_name', 'Неизвестно'),
            'response': result.get('response', ''),
            'error': None,
            'tokens_used': result.get('tokens_used'),
            'response_time': result.get('response_time')
        }
        
        # Открываем диалоговое окно
        dialog = MarkdownViewDialog(self, formatted_result, prompt_text)
        dialog.exec_()
    
    def delete_selected_result(self):
        """Удаляет выбранный результат."""
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        model_item = self.results_table.item(row, 0)
        if not model_item:
            return
        
        result = model_item.data(Qt.UserRole)
        if not result:
            return
        
        result_id = result.get('id')
        if not result_id:
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить результат от {result.get('model_name', 'модели')}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if db.delete_result(result_id):
                    QMessageBox.information(self, "Успех", "Результат удален.")
                    # Перезагружаем результаты
                    current_index = self.prompts_combo.currentIndex()
                    self.on_prompt_selected(current_index)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить результат.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")

