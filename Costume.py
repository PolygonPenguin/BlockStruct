import hashlib
import os
from PIL import Image

class Costume:
    def __init__(self, file_path: str, name: str):
        self.file_path = file_path
        self.name = name
        self.assetId = self._compute_md5()
        self.dataFormat = self._get_data_format()
        self.md5ext = f"{self.assetId}.{self.dataFormat}"
        self.rotationCenterX = 240
        self.rotationCenterY = 180
        self._analyze_image()

    def _compute_md5(self) -> str:
        with open(self.file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_data_format(self) -> str:
        ext = os.path.splitext(self.file_path)[1].lower().strip(".")
        return ext

    def _analyze_image(self):
        try:
            with Image.open(self.file_path) as img:
                self.rotationCenterX = img.width // 2
                self.rotationCenterY = img.height // 2
        except:
            pass

    def toDictionary(self):
        data = {
            "assetId": self.assetId,
            "name": self.name,
            "md5ext": self.md5ext,
            "dataFormat": self.dataFormat,
            "rotationCenterX": self.rotationCenterX,
            "rotationCenterY": self.rotationCenterY,
        }
        return (data, self.file_path, self.md5ext)