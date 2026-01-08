"""
Окно управления моделями нейросетей.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QMessageBox,
    QHeaderView, QDialogButtonBox
)
from PyQt5.QtCore import Qt
import db
import model


class ModelsWindow(QDialog):
    """Окно для управления моделями."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление моделями")
        self.setGeometry(200, 200, 900, 600)
        self.init_ui()
        self.load_models()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Таблица моделей
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(6)
        self.models_table.setHorizontalHeaderLabels([
            "ID", "Название", "API URL", "API ID", "Тип", "Активна"
        ])
        
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.models_table.setAlternatingRowColors(True)
        self.models_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.models_table)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_model)
        buttons_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_model)
        buttons_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_model)
        buttons_layout.addWidget(self.delete_button)
        
        self.toggle_button = QPushButton("Активировать/Деактивировать")
        self.toggle_button.clicked.connect(self.toggle_model)
        buttons_layout.addWidget(self.toggle_button)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Кнопки диалога
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
    
    def load_models(self):
        """Загружает модели в таблицу."""
        models = db.get_all_models()
        self.models_table.setRowCount(len(models))
        
        for row, model_data in enumerate(models):
            # ID
            id_item = QTableWidgetItem(str(model_data['id']))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.models_table.setItem(row, 0, id_item)
            
            # Название
            name_item = QTableWidgetItem(model_data['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.models_table.setItem(row, 1, name_item)
            
            # API URL
            url_item = QTableWidgetItem(model_data['api_url'])
            url_item.setFlags(url_item.flags() & ~Qt.ItemIsEditable)
            self.models_table.setItem(row, 2, url_item)
            
            # API ID
            api_id_item = QTableWidgetItem(model_data['api_id'])
            api_id_item.setFlags(api_id_item.flags() & ~Qt.ItemIsEditable)
            self.models_table.setItem(row, 3, api_id_item)
            
            # Тип
            type_item = QTableWidgetItem(model_data['model_type'])
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.models_table.setItem(row, 4, type_item)
            
            # Активна
            active_checkbox = QCheckBox()
            active_checkbox.setChecked(model_data['is_active'] == 1)
            active_checkbox.setEnabled(False)
            self.models_table.setCellWidget(row, 5, active_checkbox)
    
    def get_selected_model_id(self) -> int:
        """Получает ID выбранной модели."""
        selected_rows = self.models_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        id_item = self.models_table.item(row, 0)
        return int(id_item.text()) if id_item else None
    
    def add_model(self):
        """Открывает диалог добавления модели."""
        dialog = ModelEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                model.create_model(
                    name=dialog.name_edit.text(),
                    api_url=dialog.url_edit.text(),
                    api_id=dialog.api_id_edit.text(),
                    model_type=dialog.type_combo.currentText(),
                    is_active=1 if dialog.active_checkbox.isChecked() else 0
                )
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель добавлена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить модель: {str(e)}")
    
    def edit_model(self):
        """Открывает диалог редактирования модели."""
        model_id = self.get_selected_model_id()
        if not model_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для редактирования.")
            return
        
        model_data = db.get_model(model_id)
        if not model_data:
            QMessageBox.warning(self, "Ошибка", "Модель не найдена.")
            return
        
        dialog = ModelEditDialog(self, model_data)
        if dialog.exec_() == QDialog.Accepted:
            try:
                db.update_model(
                    model_id,
                    name=dialog.name_edit.text(),
                    api_url=dialog.url_edit.text(),
                    api_id=dialog.api_id_edit.text(),
                    model_type=dialog.type_combo.currentText(),
                    is_active=1 if dialog.active_checkbox.isChecked() else 0
                )
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель обновлена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить модель: {str(e)}")
    
    def delete_model(self):
        """Удаляет выбранную модель."""
        model_id = self.get_selected_model_id()
        if not model_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для удаления.")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение", "Вы уверены, что хотите удалить эту модель?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if db.delete_model(model_id):
                    self.load_models()
                    QMessageBox.information(self, "Успех", "Модель удалена.")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить модель.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def toggle_model(self):
        """Переключает статус активности модели."""
        model_id = self.get_selected_model_id()
        if not model_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель.")
            return
        
        try:
            if model.toggle_model_active(model_id):
                self.load_models()
                QMessageBox.information(self, "Успех", "Статус модели изменен.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось изменить статус модели.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")


class ModelEditDialog(QDialog):
    """Диалог для добавления/редактирования модели."""
    
    def __init__(self, parent=None, model_data=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать модель" if model_data else "Добавить модель")
        self.setModal(True)
        self.init_ui(model_data)
    
    def init_ui(self, model_data):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Название
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название:"))
        self.name_edit = QLineEdit()
        if model_data:
            self.name_edit.setText(model_data['name'])
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # API URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("API URL:"))
        self.url_edit = QLineEdit()
        if model_data:
            self.url_edit.setText(model_data['api_url'])
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)
        
        # API ID
        api_id_layout = QHBoxLayout()
        api_id_layout.addWidget(QLabel("API ID (имя переменной в .env):"))
        self.api_id_edit = QLineEdit()
        if model_data:
            self.api_id_edit.setText(model_data['api_id'])
        api_id_layout.addWidget(self.api_id_edit)
        layout.addLayout(api_id_layout)
        
        # Тип модели
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип API:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['openai', 'groq', 'openrouter'])
        if model_data:
            index = self.type_combo.findText(model_data['model_type'])
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Активна
        self.active_checkbox = QCheckBox("Активна")
        if model_data:
            self.active_checkbox.setChecked(model_data['is_active'] == 1)
        else:
            self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)





