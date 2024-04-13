import sys
import os
import pandas as pd
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget, QPushButton
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

class DatasetEditor(QMainWindow):
    def __init__(self, csv_file):
        super().__init__()
        self.csv_file = csv_file
        self.data = pd.read_csv(csv_file)
        self.current_index = 0
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Dataset Editor")
        self.setGeometry(100, 100, 800, 600)  # Измените размеры окна здесь

        self.image_label = QLabel()
        self.image_label.setScaledContents(True)

        self.text_edit = QLineEdit()
        self.text_edit.setMinimumHeight(40)  # Увеличить размер поля ввода
        self.text_edit.setFont(QFont("Arial", 14))  # Изменить шрифт и размер шрифта

        self.text_edit.returnPressed.connect(self.saveText)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.nextImage)
        
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prevImage)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.deleteImage)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.delete_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.showImage()

    def resizeEvent(self, event):
        self.showImage()  # Перезагрузить изображение при изменении размера окна

    def showImage(self):
        if self.current_index < 0 or self.current_index >= len(self.data):
            return

        filename = self.data.iloc[self.current_index]['filename']
        filename = os.path.join('dataset', filename)
        words = self.data.iloc[self.current_index]['words']

        pixmap = QPixmap(filename)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))

        self.text_edit.setText(words)

    def nextImage(self):
        if self.current_index + 1 < len(self.data):
            self.current_index += 1
            self.showImage()

    def prevImage(self):
        if self.current_index - 1 >= 0:
            self.current_index -= 1
            self.showImage()

    def saveText(self):
        self.data.at[self.current_index, 'words'] = self.text_edit.text()
        self.data.to_csv(self.csv_file, index=False)

    def deleteImage(self):
        if 0 <= self.current_index < len(self.data):
            filename = self.data.iloc[self.current_index]['filename']
            filename = os.path.join('dataset', filename)
            os.remove(filename)  # Удалить файл изображения
            self.data = self.data.drop(self.data.index[self.current_index])
            self.data.reset_index(drop=True, inplace=True)  # Сбросить индекс после удаления строки
            self.data.to_csv(self.csv_file, index=False)
            if self.current_index == len(self.data):  # Если было удалено последнее изображение
                self.current_index -= 1  # Уменьшить индекс, чтобы остаться в пределах допустимых значений
            self.showImage()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = DatasetEditor('output.csv')
    editor.show()
    sys.exit(app.exec())