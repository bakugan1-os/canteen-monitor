import cv2
import threading
import time
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class CameraSource:
    def __init__(self, source: str):
        self.source = source
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self._photo_mode = False
        self._photo = None

    def start(self):
        source_str = str(self.source)

        # Фото-режим
        if Path(source_str).suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp'):
            self._photo = cv2.imread(source_str)
            if self._photo is None:
                raise RuntimeError(f"Не вдалося відкрити фото: {source_str}")
            self._photo_mode = True
            self.running = True
            logger.info(f"Фото-режим: {source_str}")
            return

        # Відео/камера
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Не вдалося відкрити джерело: {self.source}")
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        logger.info("Camera thread started")

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
            else:
                logger.warning("Потік втрачено")
                self.cap.release()
                time.sleep(1)
                self.cap = cv2.VideoCapture(self.source)

    def read(self):
        if self._photo_mode:
            return self._photo.copy()
        return self.frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.cap:
            self.cap.release()