from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QComboBox, QSlider, QFileDialog, QVBoxLayout, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
class ImageProcessWorker(QObject):
    finished = Signal(str)
    progress = Signal(str)

    def __init__(self, folder, scale_factor, dpi, resample_method, noise_level, remove_bg, crop_func, resize_func):
        super().__init__()
        self.folder = folder
        self.scale_factor = scale_factor
        self.dpi = dpi
        self.resample_method = resample_method
        self.noise_level = noise_level
        self.remove_bg = remove_bg
        self.crop_func = crop_func
        self.resize_func = resize_func

    def run(self):
        output_folder_resize = os.path.join(self.folder, "output_resize")
        os.makedirs(output_folder_resize, exist_ok=True)
        for filename in os.listdir(self.folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(self.folder, filename)
                resized_image_path = os.path.join(output_folder_resize, f"{filename}")
                cropped_image = self.crop_func(image_path)
                if cropped_image:
                    if self.remove_bg:
                        cropped_image = self.remove_bg(cropped_image)
                    with BytesIO() as temp_cropped_io:
                        cropped_image.save(temp_cropped_io, format='PNG')
                        temp_cropped_io.seek(0)
                        temp_cropped_image = Image.open(temp_cropped_io)
                        orig_w, orig_h = temp_cropped_image.size
                        size = (orig_w * self.scale_factor, orig_h * self.scale_factor)
                        self.resize_func(temp_cropped_image, resized_image_path, size, (self.dpi, self.dpi), self.resample_method, self.noise_level)
        self.finished.emit(output_folder_resize)
import sys, os
from PIL import Image, ImageFilter
from rembg import remove
import numpy as np
from io import BytesIO
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resize Image")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Grid layout cho scale và DPI
        grid_row1 = QGridLayout()
        label_scale = QLabel("Hệ số phóng to (x):")
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(["5", "6", "7", "8", "9", "10"])
        label_dpi = QLabel("DPI:")
        self.combo_dpi = QComboBox()
        self.combo_dpi.addItems(["72", "96", "150", "300"])
        grid_row1.addWidget(label_scale, 0, 0)
        grid_row1.addWidget(self.combo_scale, 0, 1)
        grid_row1.addWidget(label_dpi, 0, 2)
        grid_row1.addWidget(self.combo_dpi, 0, 3)
        layout.addLayout(grid_row1)

        # Grid layout cho resample method và remove background cùng một hàng
        grid_row2 = QGridLayout()
        label_resample = QLabel("Resample method:")
        self.combo_resample = QComboBox()
        self.combo_resample.addItems(["Nearest", "Box", "Bilinear", "Hamming", "Bicubic", "Lanczos"])
        label_remove_bg = QLabel("Remove background:")
        self.combo_remove_bg = QComboBox()
        self.combo_remove_bg.addItems(["Tách nền", "Không tách nền"])
        grid_row2.addWidget(label_resample, 0, 0)
        grid_row2.addWidget(self.combo_resample, 0, 1)
        grid_row2.addWidget(label_remove_bg, 0, 2)
        grid_row2.addWidget(self.combo_remove_bg, 0, 3)
        layout.addLayout(grid_row2)

        # Slider noise
        self.h_noise = QSlider(Qt.Horizontal)
        self.h_noise.setMinimum(0)
        self.h_noise.setMaximum(100)
        self.h_noise.setValue(70)
        layout.addWidget(QLabel("Noise level:"))
        layout.addWidget(self.h_noise)

        # Label phần trăm
        self.lb_phantram = QLabel("70%")
        layout.addWidget(self.lb_phantram)

        # Button run
        self.bt_run = QPushButton("Chạy xử lý folder ảnh")
        layout.addWidget(self.bt_run)

        # Label trạng thái
        self.label_text = QLabel("")
        layout.addWidget(self.label_text)

        # Resample methods
        self.resample_methods = {
            "Nearest": Image.NEAREST,
            "Box": Image.BOX,
            "Bilinear": Image.BILINEAR,
            "Hamming": Image.HAMMING,
            "Bicubic": Image.BICUBIC,
            "Lanczos": Image.LANCZOS
        }

        # Kết nối signal/slot
        self.h_noise.valueChanged.connect(self.updateLabel)
        self.bt_run.clicked.connect(self.select_folder)

        # Thêm CSS tổng cho toàn bộ giao diện
        self.setStyleSheet("""
            QWidget {
                font-family: Arial;
                font-size: 14px;
            }
            QLabel {
                color: #333;
                border: 1px solid #bbb;
                border-radius: 6px;
                padding: 2px 8px;
                background: #f8f8f8;
            }
            QComboBox {
                min-height: 28px;
                border: 1.5px solid #4CAF50;
                border-radius: 8px;
                padding: 2px 8px;
                background: #fff;
            }
            QSlider {
                min-height: 28px;
                border: 1.5px solid #4CAF50;
                border-radius: 8px;
                background: #fff;
            }
            QPushButton {
                min-height: 28px;
                background-color: #4CAF50;
                color: white;
                border: 2px solid #388E3C;
                border-radius: 10px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #ddd;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #999;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
    def remove_background(self, input_image):
        img_bytes = BytesIO()
        input_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        output_bytes = remove(img_bytes.getvalue())
        output_img = Image.open(BytesIO(output_bytes)).convert("RGBA")
        return output_img
    def updateLabel(self, value):
        self.lb_phantram.setText(f'{value}%')

    def resize_and_set_dpi_with_padding(self, input_image, output_image_path, size, dpi, resample_method, noise_level):
        img = input_image.copy()
        img_ratio = img.width / img.height
        target_ratio = size[0] / size[1]

        if img_ratio > target_ratio:
            new_width = size[0]
            new_height = int(new_width / img_ratio)
        else:
            new_height = size[1]
            new_width = int(new_height * img_ratio)

        img = img.resize((new_width, new_height), resample=resample_method)

        new_img = Image.new("RGBA", size, (0, 0, 0, 0))
        paste_position = ((size[0] - new_width) // 2, 0)
        new_img.paste(img, paste_position)

        if noise_level > 0:
            new_img = new_img.filter(ImageFilter.GaussianBlur(radius=noise_level / 100.0))

        new_img.save(output_image_path, dpi=dpi)

    def crop_image_to_content(self, image_path):
        image = Image.open(image_path).convert("RGBA")
        image_array = np.array(image)
        mask = image_array[:, :, 3] > 0 if image_array.shape[2] == 4 else np.all(image_array[:, :, :3] != [255, 255, 255], axis=-1)
        
        non_empty_columns = np.where(mask.any(axis=0))[0]
        non_empty_rows = np.where(mask.any(axis=1))[0]
        if non_empty_columns.size and non_empty_rows.size:
            crop_box = (min(non_empty_columns), min(non_empty_rows), max(non_empty_columns), max(non_empty_rows))
            return image.crop(crop_box)
        else:
            return None

    def select_folder(self):
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_selected:
            self.label_text.setText("Processing, please wait...")
            self.bt_run.setEnabled(False)
            scale_factor = int(self.combo_scale.currentText())
            dpi = int(self.combo_dpi.currentText())
            resample_method = self.resample_methods[f"{self.combo_resample.currentText()}"]
            noise_level = self.h_noise.value()
            remove_bg = self.combo_remove_bg.currentText() == "Tách nền"
            # Tạo QThread và worker
            self.thread = QThread()
            self.worker = ImageProcessWorker(
                folder_selected, scale_factor, dpi, resample_method, noise_level,
                self.remove_background if remove_bg else None,
                self.crop_image_to_content,
                self.resize_and_set_dpi_with_padding
            )
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_processing_finished)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

    def on_processing_finished(self, output_folder_resize):
        self.label_text.setText("Completed!")
        self.bt_run.setEnabled(True)
        self.show_notification("Completed", f"Images have been cropped and resized, and saved to {output_folder_resize}")

    # Đã chuyển xử lý ảnh sang QThread, không cần hàm này nữa
    def show_notification(self,title="Notification",text="Notification"):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(text)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
        return msg_box

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
