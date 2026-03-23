"""
Face Recognition Service
Generates 128-dimensional face embeddings and performs matching using cosine similarity.
Uses a lightweight approach suitable for low-end hardware.
"""
import numpy as np
import cv2
import os
import logging

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """
    Face recognition using embeddings and cosine similarity.

    Why pretrained embeddings over training from scratch:
    1. No GPU or large dataset required — critical for rural deployment
    2. 128-d vectors are ~512 bytes vs. megabytes for raw images
    3. Cosine similarity runs in microseconds — enables real-time matching
    4. Pretrained models generalize well across diverse faces
    5. No risk of overfitting on small school datasets

    How proxy attendance is reduced:
    1. Face embeddings are unique biometric identifiers
    2. Liveness detection prevents photo/video spoofing
    3. Confidence thresholding minimizes false positive matches
    4. One-attendance-per-day constraint prevents re-marking
    """

    def __init__(self):
        self.face_detector = None
        self.embedding_model = None
        self.embedding_size = 128
        self._init_services()

    def _init_services(self):
        """Initialize face detector and embedding model."""
        from .face_detection import FaceDetector
        self.face_detector = FaceDetector()

        # Try to load a deep learning embedding model
        model_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'models',
            'openface_nn4.small2.v1.t7'
        )

        if os.path.exists(model_path):
            try:
                self.embedding_model = cv2.dnn.readNetFromTorch(model_path)
                logger.info("Loaded OpenFace embedding model")
                return
            except Exception as e:
                logger.warning(f"Failed to load OpenFace model: {e}")

        # Fallback: use a simpler feature-based approach
        logger.info("Using histogram-based feature extraction (lightweight fallback)")
        self.embedding_model = None

    def generate_embedding(self, image):
        """
        Generate a 128-d face embedding from an image.

        Args:
            image: BGR image (numpy array) containing a face

        Returns:
            numpy array of shape (128,) or None if no face found
        """
        if image is None:
            return None

        # Detect face
        faces = self.face_detector.detect_faces(image)
        if not faces:
            return None

        # Use the largest face
        face_bbox = max(faces, key=lambda f: f[2] * f[3])

        if self.embedding_model is not None:
            return self._generate_dnn_embedding(image, face_bbox)
        else:
            return self._generate_histogram_embedding(image, face_bbox)

    def _generate_dnn_embedding(self, image, bbox):
        """Generate embedding using deep learning model."""
        face = self.face_detector.extract_face(image, bbox, target_size=(96, 96))
        if face is None:
            return None

        # Prepare for DNN
        blob = cv2.dnn.blobFromImage(
            face, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=False, crop=False
        )
        self.embedding_model.setInput(blob)
        embedding = self.embedding_model.forward()

        # Normalize
        embedding = embedding.flatten()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding[:self.embedding_size]

    def _generate_histogram_embedding(self, image, bbox):
        """
        Generate embedding using Local Binary Patterns + histogram features.
        This is a lightweight fallback when no DNN model is available.
        Produces a 128-d feature vector.
        """
        x, y, w, h = bbox
        margin = int(min(w, h) * 0.1)
        x1, y1 = max(0, x - margin), max(0, y - margin)
        x2 = min(image.shape[1], x + w + margin)
        y2 = min(image.shape[0], y + h + margin)

        face = image[y1:y2, x1:x2]
        if face.size == 0:
            return None

        # Resize to standard size
        face = cv2.resize(face, (128, 128))
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # Compute LBP-like features
        features = []

        # Spatial histogram features (divide face into 4x4 grid)
        grid_h, grid_w = gray.shape[0] // 4, gray.shape[1] // 4
        for i in range(4):
            for j in range(4):
                cell = gray[i*grid_h:(i+1)*grid_h, j*grid_w:(j+1)*grid_w]
                hist = cv2.calcHist([cell], [0], None, [8], [0, 256])
                hist = hist.flatten() / (hist.sum() + 1e-7)
                features.extend(hist)

        # Now we have 4*4*8 = 128 features
        embedding = np.array(features, dtype=np.float64)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def compare_embeddings(self, embedding1, embedding2):
        """
        Compare two embeddings using cosine similarity.

        Returns:
            Similarity score between 0 and 1 (higher = more similar)
        """
        if embedding1 is None or embedding2 is None:
            return 0.0

        # Ensure same size
        min_len = min(len(embedding1), len(embedding2))
        e1 = embedding1[:min_len]
        e2 = embedding2[:min_len]

        # Cosine similarity
        dot_product = np.dot(e1, e2)
        norm1 = np.linalg.norm(e1)
        norm2 = np.linalg.norm(e2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, similarity))

    def recognize_faces(self, image, known_embeddings, threshold=None):
        """
        Detect and recognize all faces in an image.

        Args:
            image: BGR image
            known_embeddings: List of dicts with 'student_db_id' and 'embedding'
            threshold: Min similarity for positive match (default from config)

        Returns:
            List of recognition results
        """
        if threshold is None:
            threshold = 0.6

        faces = self.face_detector.detect_faces(image)
        if not faces:
            return []

        results = []
        for bbox in faces:
            x, y, w, h = bbox

            if self.embedding_model is not None:
                embedding = self._generate_dnn_embedding(image, bbox)
            else:
                embedding = self._generate_histogram_embedding(image, bbox)

            if embedding is None:
                results.append({
                    'matched': False,
                    'confidence': 0.0,
                    'bbox': [int(x), int(y), int(w), int(h)],
                })
                continue

            # Compare against all known embeddings
            best_match = None
            best_score = 0.0

            for known in known_embeddings:
                score = self.compare_embeddings(embedding, known['embedding'])
                if score > best_score:
                    best_score = score
                    best_match = known

            if best_score >= threshold and best_match:
                results.append({
                    'matched': True,
                    'student_db_id': best_match['student_db_id'],
                    'confidence': float(best_score),
                    'bbox': [int(x), int(y), int(w), int(h)],
                })
            else:
                results.append({
                    'matched': False,
                    'confidence': float(best_score),
                    'bbox': [int(x), int(y), int(w), int(h)],
                })

        return results

    def get_embedding_info(self):
        """Return information about the current embedding method."""
        return {
            'method': 'dnn' if self.embedding_model else 'histogram_lbp',
            'embedding_size': self.embedding_size,
            'model_loaded': self.embedding_model is not None,
        }
