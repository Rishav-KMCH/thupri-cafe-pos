import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QLineEdit,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox, QSpinBox, QDialog, QInputDialog
)
from PyQt6.QtCore import Qt
from datetime import datetime
import pytz

RECEIPT_DIR = "receipts"
if not os.path.exists(RECEIPT_DIR):
    os.makedirs(RECEIPT_DIR)

class ThupriCafe(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thupri Cafe POS")
        self.setGeometry(200, 200, 600, 400)
        self.cashier_code = self.get_cashier_code()
        self.init_ui()

    def get_cashier_code(self):
        try:
            with open("code.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "UNKNOWN"

    def init_ui(self):
        layout = QVBoxLayout()
        welcome_label = QLabel(f"Welcome, {self.cashier_code}!")
        welcome_label.setStyleSheet("font-size: 20px; font-weight: bold; color: green;")
        layout.addWidget(welcome_label)

        create_btn = QPushButton("Create New Receipt")
        open_btn = QPushButton("Open Existing Receipt")
        create_btn.clicked.connect(self.create_receipt)
        open_btn.clicked.connect(self.open_receipt)

        layout.addWidget(create_btn)
        layout.addWidget(open_btn)
        self.setLayout(layout)

    def create_receipt(self):
        self.entry_window = ReceiptEntryWindow()
        self.entry_window.show()

    def open_receipt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Receipt", RECEIPT_DIR, "Text Files (*.txt)")
        if file_path:
            if sys.platform == "darwin":
                os.system(f"open \"{file_path}\"")
            elif sys.platform == "win32":
                os.startfile(file_path)
            else:
                os.system(f"xdg-open \"{file_path}\"")

class ReceiptEntryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Receipt - Thupri Cafe")
        self.setGeometry(200, 200, 800, 500)
        self.entries = []
        self.max_entries = 10
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Item Name", "Quantity", "Diabetic", "Price ($)"])
        self.layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Create New Entry")
        self.finish_btn = QPushButton("Finish")
        self.add_btn.clicked.connect(self.add_entry)
        self.finish_btn.clicked.connect(self.finish_receipt)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.finish_btn)
        self.layout.addLayout(btn_layout)

        self.setLayout(self.layout)

    def add_entry(self):
        if len(self.entries) >= self.max_entries:
            QMessageBox.warning(self, "Limit Reached", "You can't add more than 10 items.")
            return

        entry_dialog = EntryDialog(self)
        if entry_dialog.exec() == QDialog.DialogCode.Accepted and entry_dialog.result_data:
            name, qty, diabetic, price = entry_dialog.result_data
            self.entries.append((name, qty, diabetic, price))
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.table.setItem(row, 2, QTableWidgetItem(diabetic))
            self.table.setItem(row, 3, QTableWidgetItem(f"${price:.2f}"))

    def finish_receipt(self):
        if not self.entries:
            QMessageBox.warning(self, "No Items", "Please add at least one item.")
            return

        payment_method, ok = QInputDialog.getItem(
            self, "Payment Method", "How was this paid?", ["Card", "Cash", "Digital", "Not Paid Yet"], 0, False
        )
        if not ok:
            return

        diabetic_customer, ok = QInputDialog.getItem(
            self, "Diabetic Customer", "Is the customer diabetic?", ["Yes", "No"], 0, False
        )
        if not ok:
            return

        discount_text, ok = QInputDialog.getText(
            self, "Discount", "Enter discount amount (leave blank if none):"
        )
        if not ok:
            return

        try:
            discount = float(discount_text) if discount_text else 0.0
        except ValueError:
            QMessageBox.warning(self, "Invalid Discount", "Discount must be a number.")
            return

        total = sum(qty * price for _, qty, _, price in self.entries)
        final_price = total - discount if discount else total
        timestamp = datetime.now(pytz.timezone("America/New_York")).strftime("%B %d, %Y - %I:%M %p %Z")
        filename = f"{RECEIPT_DIR}/receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        self.generate_txt(filename, payment_method, diabetic_customer, timestamp, total, discount, final_price)
        QMessageBox.information(self, "Saved", f"Receipt saved to:\n{filename}")

        if sys.platform == "darwin":
            os.system(f"open \"{filename}\"")
        elif sys.platform == "win32":
            os.startfile(filename)
        else:
            os.system(f"xdg-open \"{filename}\"")

        self.close()

    def generate_txt(self, path, payment_method, diabetic_customer, timestamp, total, discount, final_price):
        with open(path, "w") as file:
            file.write("=== THUPRI Cafe ===\n")
            file.write("123 Cafe Street, MacTown\n")
            file.write("------------------------------------------\n")
            file.write(f"Payment: {payment_method if payment_method != 'Not Paid Yet' else 'NOT PAID YET'}\n")
            file.write(f"Date/Time: {timestamp}\n")
            file.write(f"Diabetic Customer: {'Yes, alternate sweeteners used' if diabetic_customer == 'Yes' else 'No, sugar used'}\n")
            file.write("------------------------------------------\n")
            file.write(f"{'#':<3} {'Item Name':<20} {'Qty':<5} {'Price($)':<10}\n")
            for i, (name, qty, diabetic, price) in enumerate(self.entries, start=1):
                file.write(f"{i:<3} {name:<20} {qty:<5} ${price:<10.2f}\n")
            file.write("------------------------------------------\n")
            file.write(f"Total: ${total:.2f}\n")
            file.write(f"Discount: ${discount:.2f}\n")
            file.write(f"Final Price: ${final_price:.2f}\n")
            file.write("------------------------------------------\n")
            file.write("Thanks for coming, please come again!\n")

class EntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Item Entry")
        self.result_data = None

        self.layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.qty_input = QSpinBox()
        self.diabetic_input = QComboBox()
        self.price_input = QLineEdit()
        self.qty_input.setMinimum(1)
        self.diabetic_input.addItems(["Yes", "No"])

        self.layout.addWidget(QLabel("Item Name:"))
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(QLabel("Quantity:"))
        self.layout.addWidget(self.qty_input)
        self.layout.addWidget(QLabel("Diabetic (Yes/No):"))
        self.layout.addWidget(self.diabetic_input)
        self.layout.addWidget(QLabel("Price ($):"))
        self.layout.addWidget(self.price_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        ok_button.clicked.connect(self.accept_data)
        cancel_button.clicked.connect(self.reject)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def accept_data(self):
        try:
            name = self.name_input.text().strip()
            if not name:
                raise ValueError("Item name cannot be empty.")
            qty = self.qty_input.value()
            diabetic = self.diabetic_input.currentText()
            price = float(self.price_input.text())
            if price < 0:
                raise ValueError("Price must be positive.")
            self.result_data = (name, qty, diabetic, price)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThupriCafe()
    window.show()
    sys.exit(app.exec())
