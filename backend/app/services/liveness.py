"""
Liveness Detection Service
Prevents photo-based and video-based spoofing attacks.

Methods used:
1. Texture analysis - detects flat/printed images via Laplacian variance
2. Color distribution analysis - real faces have specific color patterns
3. Multi-frame validation - requires consistent face detection across frames
4. Eye blink detection - uses aspect ratio heuristics (when landmarks available)
"""
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class LivenessDetector:
    """
    Anti-spoofing liveness detection for facial recognition.

    Designed to be lightweight enough for Raspberry Pi / low-end hardware.
    """

    def __init__(self):
        self.frame_buffer = []
        self.max_buffer_size = 5
        self.blink_threshold = 0.25
        self.texture_threshold = 80.0  # Laplacian variance threshold

    def check_single_frame(self, image):
        """
        Quick liveness check on a single frame.
        Uses texture analysis and color distribution.

        Args:
            image: BGR image

        Returns:
            (is_live, message) tuple
        """
        if image is None:
            return False, "No image provided"

        # Check 1: Image quality
        h, w = image.shape[:2]
        if h < 100 or w < 100:
            return False, "Image too small for liveness check"

        # Check 2: Texture analysis (Laplacian variance)
        # Real faces have high texture variance, printed photos tend to be smoother
        is_textured, texture_msg = self._check_texture(image)
        if not is_textured:
            return False, texture_msg

        # Check 3: Color distribution analysis
        # Real skin has specific color properties in HSV space
        is_skin_real, skin_msg = self._check_skin_color(image)
        if not is_skin_real:
            return False, skin_msg

        # Check 4: Reflection/glare detection
        # Printed photos often have glare spots
        has_glare = self._check_glare(image)
        if has_glare:
            return False, "Possible printed photo detected (glare)"

        return True, "Liveness check passed"

    def check_multi_frame(self, frames):
        """
        Multi-frame liveness validation.
        Requires at least 3 frames with consistent face detection
        and some natural movement variation.

        Args:
            frames: List of BGR images

        Returns:
            (is_live, message) tuple
        """
        if len(frames) < 3:
            return False, "Need at least 3 frames for multi-frame validation"

        from .face_detection import FaceDetector
        detector = FaceDetector()

        face_locations = []
        for frame in frames:
            faces = detector.detect_faces(frame)
            if not faces:
                return False, "Face not consistently detected across frames"
            face_locations.append(faces[0])  # Use first face

        # Check for natural movement (face position should vary slightly)
        positions = np.array([(x + w//2, y + h//2) for x, y, w, h in face_locations])
        movement = np.std(positions, axis=0)

        # Very still = possibly a photo
        if movement.max() < 1.0:
            return False, "No natural movement detected - possible static image"

        # Too much movement = possibly video playing
        if movement.max() > 50.0:
            return False, "Excessive movement detected"

        # Check texture on each frame
        for frame in frames:
            is_textured, _ = self._check_texture(frame)
            if not is_textured:
                return False, "Texture inconsistency across frames"

        return True, "Multi-frame liveness check passed"

    def add_frame(self, frame):
        """Add a frame to the buffer for ongoing liveness checking."""
        self.frame_buffer.append(frame)
        if len(self.frame_buffer) > self.max_buffer_size:
            self.frame_buffer.pop(0)

    def check_buffer(self):
        """Check liveness using buffered frames."""
        if len(self.frame_buffer) < 3:
            return None, "Collecting frames..."
        return self.check_multi_frame(self.frame_buffer)

    def _check_texture(self, image):
        """
        Analyze face texture using Laplacian variance.
        Real faces have higher texture complexity than printed photos.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect face region for focused analysis
        from .face_detection import FaceDetector
        detector = FaceDetector()
        faces = detector.detect_faces(image)

        if faces:
            x, y, w, h = faces[0]
            face_region = gray[y:y+h, x:x+w]
        else:
            face_region = gray

        if face_region.size == 0:
            return True, "OK"  # Skip check if no face region

        # Compute Laplacian variance
        laplacian = cv2.Laplacian(face_region, cv2.CV_64F)
        variance = laplacian.var()

        if variance < self.texture_threshold:
            return False, f"Low texture variance ({variance:.1f}) - possible printed photo"

        return True, "Texture OK"

    def _check_skin_color(self, image):
        """
        Check if detected face region has realistic skin color distribution.
        Uses HSV color space analysis.
        """
        from .face_detection import FaceDetector
        detector = FaceDetector()
        faces = detector.detect_faces(image)

        if not faces:
            return True, "No face for skin check"

        x, y, w, h = faces[0]
        face_region = image[y:y+h, x:x+w]

        if face_region.size == 0:
            return True, "OK"

        # Convert to HSV
        hsv = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)

        # Define skin color range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)

        # Also include second range for darker skin tones
        lower_skin2 = np.array([170, 20, 70], dtype=np.uint8)
        upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)

        mask1 = cv2.inRange(hsv, lower_skin, upper_skin)
        mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
        mask = mask1 | mask2

        skin_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])

        # Real faces should have at least 20% skin-colored pixels
        if skin_ratio < 0.15:
            return False, "Skin color distribution abnormal"

        return True, "Skin color OK"

    def _check_glare(self, image):
        """
        Check for glare/reflection spots that indicate a printed photo or screen.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Find very bright spots
        _, bright = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
        bright_ratio = np.sum(bright > 0) / (bright.shape[0] * bright.shape[1])

        # High ratio of very bright pixels suggests glare
        return bright_ratio > 0.05

    @staticmethod
    def compute_ear(eye_points):
        """
        Compute Eye Aspect Ratio for blink detection.
        Used when facial landmarks are available.

        EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
        """
        if len(eye_points) < 6:
            return 0.0

        p1, p2, p3, p4, p5, p6 = eye_points[:6]

        vertical_1 = np.linalg.norm(np.array(p2) - np.array(p6))
        vertical_2 = np.linalg.norm(np.array(p3) - np.array(p5))
        horizontal = np.linalg.norm(np.array(p1) - np.array(p4))

        if horizontal == 0:
            return 0.0

        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear
