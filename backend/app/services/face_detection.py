"""
Face Detection Service
Uses OpenCV DNN-based face detector for robust detection even on low-end hardware.
Falls back to Haar cascades if DNN model is not available.
"""
import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detects faces in images using OpenCV."""

    def __init__(self):
        self.detector = None
        self.detection_method = None
        self._init_detector()

    def _init_detector(self):
        """Initialize face detector, prefer DNN, fallback to Haar cascade."""
        # Try DNN-based detector (more accurate)
        try:
            prototxt = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models',
                                     'deploy.prototxt')
            caffemodel = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models',
                                      'res10_300x300_ssd_iter_140000.caffemodel')

            if os.path.exists(prototxt) and os.path.exists(caffemodel):
                self.detector = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
                self.detection_method = 'dnn'
                logger.info("Using DNN-based face detector")
                return
        except Exception as e:
            logger.warning(f"DNN detector init failed: {e}")

        # Fallback to Haar cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.detector = cv2.CascadeClassifier(cascade_path)
        self.detection_method = 'haar'
        logger.info("Using Haar cascade face detector")

    def detect_faces(self, image, min_confidence=0.5):
        """
        Detect faces in an image.

        Args:
            image: BGR image (numpy array)
            min_confidence: Minimum detection confidence (for DNN)

        Returns:
            List of face bounding boxes [(x, y, w, h), ...]
        """
        if image is None or image.size == 0:
            return []

        if self.detection_method == 'dnn':
            return self._detect_dnn(image, min_confidence)
        else:
            return self._detect_haar(image)

    def _detect_dnn(self, image, min_confidence):
        """DNN-based face detection."""
        h, w = image.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0, (300, 300),
            (104.0, 177.0, 123.0)
        )
        self.detector.setInput(blob)
        detections = self.detector.forward()

        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > min_confidence:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype(int)
                # Clamp to image boundaries
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 > x1 and y2 > y1:
                    faces.append((x1, y1, x2 - x1, y2 - y1))

        return faces

    def _detect_haar(self, image):
        """Haar cascade face detection (fallback)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)  # Improve contrast for low-light

        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        return [(x, y, w, h) for (x, y, w, h) in faces] if len(faces) > 0 else []

    def extract_face(self, image, bbox, target_size=(160, 160)):
        """
        Extract and preprocess a face from an image.

        Args:
            image: BGR image
            bbox: (x, y, w, h) bounding box
            target_size: Output face size

        Returns:
            Preprocessed face image (RGB, normalized)
        """
        x, y, w, h = bbox
        # Add margin
        margin = int(min(w, h) * 0.2)
        x1 = max(0, x - margin)
        y1 = max(0, y - margin)
        x2 = min(image.shape[1], x + w + margin)
        y2 = min(image.shape[0], y + h + margin)

        face = image[y1:y2, x1:x2]
        if face.size == 0:
            return None

        # Resize to target
        face = cv2.resize(face, target_size)
        # Convert BGR to RGB
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        # Normalize pixel values
        face = face.astype(np.float32) / 255.0

        return face

    def check_image_quality(self, image):
        """
        Check if image quality is sufficient for face recognition.
        Returns (is_ok, message).
        """
        if image is None:
            return False, "No image provided"

        h, w = image.shape[:2]
        if h < 100 or w < 100:
            return False, "Image too small"

        # Check brightness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)

        if brightness < 40:
            return False, "Image too dark - please improve lighting"
        if brightness > 240:
            return False, "Image too bright - reduce lighting"

        # Check contrast (standard deviation of grayscale)
        contrast = np.std(gray)
        if contrast < 20:
            return False, "Low contrast - adjust camera position"

        return True, "Image quality OK"
