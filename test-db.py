"""
Тестовая программа для просмотра и редактирования SQLite базы данных.
Позволяет просматривать таблицы, данные с пагинацией и выполнять CRUD операции.
"""
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QFileDialog, QHeaderView, QDialog, QLineEdit,
    QTextEdit, QDialogButtonBox, QSpinBox, QComboBox
)
from PyQt5.QtCore import Qt
from typing import Optional, List, Dict, Any


class EditRecordDialog(QDialog):
    """Диалог для редактирования записи."""
    
    def __init__(self, parent=None, table_name: str = "", columns: List[str] = None, 
                 data: Dict = None, is_new: bool = False):
        super().__init__(parent)
        self.table_name = table_name
        self.columns = columns or []
        self.data = data or {}
        self.is_new = is_new
        self.setWindowTitle(f"{'Создать' if is_new else 'Редактировать'} запись в {table_name}")
        self.setGeometry(300, 300, 500, 400)
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.fields = {}
        
        for col in self.columns:
            if col.lower() == 'id' and not self.is_new:
                # ID не редактируется при редактировании
                continue
            
            field_layout = QHBoxLayout()
            label = QLabel(f"{col}:")
            label.setMinimumWidth(120)
            
            value = self.data.get(col, '') if self.data else ''
            
            # Используем QTextEdit для больших текстовых полей
            if isinstance(value, str) and len(str(value)) > 100:
                field = QTextEdit()
                field.setPlainText(str(value))
                field.setMaximumHeight(100)
            else:
                field = QLineEdit()
                field.setText(str(value))
            
            field_layout.addWidget(label)
            field_layout.addWidget(field)
            layout.addLayout(field_layout)
            
            self.fields[col] = field
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_data(self) -> Dict[str, Any]:
        """Получает данные из полей формы."""
        result = {}
        for col, field in self.fields.items():
            if isinstance(field, QTextEdit):
                result[col] = field.toPlainText()
            else:
                result[col] = field.text()
        return result


class DatabaseViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLite Database Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        self.db_path: Optional[str] = None
        self.conn: Optional[sqlite3.Connection] = None
        self.current_table: Optional[str] = None
        self.current_page = 1
        self.page_size = 50
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Левая панель - список таблиц
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        file_label = QLabel("База данных:")
        left_layout.addWidget(file_label)
        
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("Не выбрана")
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setStyleSheet("color: #666; padding: 5px;")
        file_layout.addWidget(self.file_path_label)
        left_layout.addLayout(file_layout)
        
        open_file_button = QPushButton("Выбрать файл...")
        open_file_button.clicked.connect(self.open_database_file)
        left_layout.addWidget(open_file_button)
        
        tables_label = QLabel("Таблицы:")
        left_layout.addWidget(tables_label)
        
        self.tables_list = QListWidget()
        self.tables_list.itemDoubleClicked.connect(self.on_table_selected)
        left_layout.addWidget(self.tables_list)
        
        self.open_table_button = QPushButton("Открыть")
        self.open_table_button.clicked.connect(self.on_open_table_clicked)
        self.open_table_button.setEnabled(False)
        left_layout.addWidget(self.open_table_button)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # Правая панель - таблица данных
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Заголовок таблицы
        table_header_layout = QHBoxLayout()
        self.table_name_label = QLabel("Выберите таблицу")
        self.table_name_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        table_header_layout.addWidget(self.table_name_label)
        table_header_layout.addStretch()
        right_layout.addLayout(table_header_layout)
        
        # Пагинация сверху
        pagination_top_layout = QHBoxLayout()
        self.page_info_label = QLabel("")
        pagination_top_layout.addWidget(self.page_info_label)
        pagination_top_layout.addStretch()
        
        self.prev_page_button = QPushButton("◀ Предыдущая")
        self.prev_page_button.clicked.connect(self.prev_page)
        self.prev_page_button.setEnabled(False)
        
        self.next_page_button = QPushButton("Следующая ▶")
        self.next_page_button.clicked.connect(self.next_page)
        self.next_page_button.setEnabled(False)
        
        page_size_layout = QHBoxLayout()
        page_size_layout.addWidget(QLabel("Записей на странице:"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setMinimum(10)
        self.page_size_spin.setMaximum(500)
        self.page_size_spin.setValue(50)
        self.page_size_spin.valueChanged.connect(self.on_page_size_changed)
        page_size_layout.addWidget(self.page_size_spin)
        
        pagination_top_layout.addLayout(page_size_layout)
        pagination_top_layout.addWidget(self.prev_page_button)
        pagination_top_layout.addWidget(self.next_page_button)
        right_layout.addLayout(pagination_top_layout)
        
        # Таблица данных
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        right_layout.addWidget(self.data_table)
        
        # Кнопки CRUD
        crud_layout = QHBoxLayout()
        
        self.create_button = QPushButton("Создать")
        self.create_button.clicked.connect(self.create_record)
        self.create_button.setEnabled(False)
        
        self.read_button = QPushButton("Просмотреть")
        self.read_button.clicked.connect(self.read_record)
        self.read_button.setEnabled(False)
        
        self.update_button = QPushButton("Изменить")
        self.update_button.clicked.connect(self.update_record)
        self.update_button.setEnabled(False)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_record)
        self.delete_button.setEnabled(False)
        
        crud_layout.addWidget(self.create_button)
        crud_layout.addWidget(self.read_button)
        crud_layout.addWidget(self.update_button)
        crud_layout.addWidget(self.delete_button)
        crud_layout.addStretch()
        
        right_layout.addLayout(crud_layout)
        
        main_layout.addWidget(right_panel)
    
    def open_database_file(self):
        """Открывает диалог выбора файла базы данных."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл базы данных", "", "SQLite Files (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        
        if file_path:
            try:
                self.load_database(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть базу данных:\n{str(e)}")
    
    def load_database(self, file_path: str):
        """Загружает базу данных и список таблиц."""
        if self.conn:
            self.conn.close()
        
        self.db_path = file_path
        self.conn = sqlite3.connect(file_path)
        self.conn.row_factory = sqlite3.Row
        
        self.file_path_label.setText(file_path)
        self.file_path_label.setStyleSheet("color: #000; padding: 5px;")
        
        # Загружаем список таблиц
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        self.tables_list.clear()
        for table in tables:
            self.tables_list.addItem(table)
        
        if tables:
            self.open_table_button.setEnabled(True)
        else:
            QMessageBox.information(self, "Информация", "В базе данных нет таблиц.")
    
    def on_table_selected(self, item: QListWidgetItem):
        """Обработчик выбора таблицы."""
        self.open_table()
    
    def on_open_table_clicked(self):
        """Обработчик нажатия кнопки 'Открыть'."""
        current_item = self.tables_list.currentItem()
        if current_item:
            self.open_table()
    
    def open_table(self):
        """Открывает выбранную таблицу."""
        current_item = self.tables_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите таблицу из списка.")
            return
        
        self.current_table = current_item.text()
        self.current_page = 1
        self.load_table_data()
    
    def load_table_data(self):
        """Загружает данные таблицы с пагинацией."""
        if not self.conn or not self.current_table:
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Получаем общее количество записей
            cursor.execute(f"SELECT COUNT(*) FROM `{self.current_table}`")
            total_records = cursor.fetchone()[0]
            
            # Получаем названия колонок
            cursor.execute(f"PRAGMA table_info(`{self.current_table}`)")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            # Вычисляем пагинацию
            total_pages = (total_records + self.page_size - 1) // self.page_size if total_records > 0 else 1
            offset = (self.current_page - 1) * self.page_size
            
            # Загружаем данные
            cursor.execute(f"SELECT * FROM `{self.current_table}` LIMIT ? OFFSET ?", 
                          (self.page_size, offset))
            rows = cursor.fetchall()
            
            # Обновляем интерфейс
            self.table_name_label.setText(f"Таблица: {self.current_table}")
            self.page_info_label.setText(
                f"Страница {self.current_page} из {total_pages} | "
                f"Записей: {total_records} | "
                f"Показано: {len(rows)}"
            )
            
            # Настройка кнопок пагинации
            self.prev_page_button.setEnabled(self.current_page > 1)
            self.next_page_button.setEnabled(self.current_page < total_pages)
            
            # Заполняем таблицу
            self.data_table.setColumnCount(len(columns))
            self.data_table.setHorizontalHeaderLabels(columns)
            self.data_table.setRowCount(len(rows))
            
            for row_idx, row in enumerate(rows):
                for col_idx, col_name in enumerate(columns):
                    value = row[col_name]
                    item = QTableWidgetItem(str(value) if value is not None else '')
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.data_table.setItem(row_idx, col_idx, item)
            
            # Настройка ширины колонок
            header = self.data_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            
            # Включаем кнопки CRUD
            self.create_button.setEnabled(True)
            self.read_button.setEnabled(True)
            self.update_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            
            # Сохраняем информацию о колонках для использования в CRUD
            self.table_columns = columns
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
    
    def prev_page(self):
        """Переход на предыдущую страницу."""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_table_data()
    
    def next_page(self):
        """Переход на следующую страницу."""
        self.current_page += 1
        self.load_table_data()
    
    def on_page_size_changed(self, value: int):
        """Обработчик изменения размера страницы."""
        self.page_size = value
        self.current_page = 1
        if self.current_table:
            self.load_table_data()
    
    def get_selected_row_data(self) -> Optional[Dict]:
        """Получает данные выбранной строки."""
        selected_rows = self.data_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        data = {}
        
        for col_idx, col_name in enumerate(self.table_columns):
            item = self.data_table.item(row, col_idx)
            if item:
                data[col_name] = item.text()
        
        return data
    
    def create_record(self):
        """Создает новую запись."""
        if not self.conn or not self.current_table:
            return
        
        dialog = EditRecordDialog(self, self.current_table, self.table_columns, is_new=True)
        if dialog.exec_() == QDialog.Accepted:
            try:
                new_data = dialog.get_data()
                columns = list(new_data.keys())
                values = list(new_data.values())
                placeholders = ', '.join(['?' for _ in values])
                columns_str = ', '.join([f'`{col}`' for col in columns])
                
                cursor = self.conn.cursor()
                cursor.execute(
                    f"INSERT INTO `{self.current_table}` ({columns_str}) VALUES ({placeholders})",
                    values
                )
                self.conn.commit()
                QMessageBox.information(self, "Успех", "Запись создана.")
                self.load_table_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать запись:\n{str(e)}")
    
    def read_record(self):
        """Просматривает выбранную запись."""
        data = self.get_selected_row_data()
        if not data:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для просмотра.")
            return
        
        # Создаем диалог только для чтения
        dialog = EditRecordDialog(self, self.current_table, self.table_columns, data, is_new=False)
        # Делаем все поля только для чтения
        for field in dialog.fields.values():
            if isinstance(field, QTextEdit):
                field.setReadOnly(True)
            else:
                field.setReadOnly(True)
        dialog.exec_()
    
    def update_record(self):
        """Обновляет выбранную запись."""
        data = self.get_selected_row_data()
        if not data:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для редактирования.")
            return
        
        # Находим ID для WHERE условия
        id_column = None
        id_value = None
        for col in self.table_columns:
            if col.lower() == 'id':
                id_column = col
                id_value = data.get(col)
                break
        
        if not id_column or not id_value:
            QMessageBox.warning(self, "Ошибка", "Не найдено поле ID для обновления записи.")
            return
        
        dialog = EditRecordDialog(self, self.current_table, self.table_columns, data, is_new=False)
        if dialog.exec_() == QDialog.Accepted:
            try:
                new_data = dialog.get_data()
                # Убираем ID из данных для обновления
                update_data = {k: v for k, v in new_data.items() if k.lower() != 'id'}
                
                set_clause = ', '.join([f'`{col}` = ?' for col in update_data.keys()])
                values = list(update_data.values())
                values.append(id_value)  # Для WHERE условия
                
                cursor = self.conn.cursor()
                cursor.execute(
                    f"UPDATE `{self.current_table}` SET {set_clause} WHERE `{id_column}` = ?",
                    values
                )
                self.conn.commit()
                QMessageBox.information(self, "Успех", "Запись обновлена.")
                self.load_table_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись:\n{str(e)}")
    
    def delete_record(self):
        """Удаляет выбранную запись."""
        data = self.get_selected_row_data()
        if not data:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для удаления.")
            return
        
        # Находим ID для WHERE условия
        id_column = None
        id_value = None
        for col in self.table_columns:
            if col.lower() == 'id':
                id_column = col
                id_value = data.get(col)
                break
        
        if not id_column or not id_value:
            QMessageBox.warning(self, "Ошибка", "Не найдено поле ID для удаления записи.")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить запись с ID {id_value}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    f"DELETE FROM `{self.current_table}` WHERE `{id_column}` = ?",
                    (id_value,)
                )
                self.conn.commit()
                QMessageBox.information(self, "Успех", "Запись удалена.")
                self.load_table_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись:\n{str(e)}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна."""
        if self.conn:
            self.conn.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = DatabaseViewer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

