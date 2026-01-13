"""
Image Validator - LOCAL IMAGES ONLY (NON-NEGOTIABLE)
"""
import os
import re
from pathlib import Path
from typing import Optional, Set
from dataclasses import dataclass


@dataclass
class ImageValidationResult:
    is_valid: bool
    path: Optional[str]
    reason: str


class ImageValidator:
    """
    STRICT RULES:
    1. Images ONLY from local images folder
    2. Valid extensions: jpg, jpeg, png, gif, webp
    3. FORBIDDEN: Wikipedia images, disease images, external URLs
    """
    
    VALID_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    FORBIDDEN_PATTERNS = [
        r'wikipedia', r'wikimedia', r'anatomy', r'diagram',
        r'disease', r'symptom', r'http[s]?://', r'www\.',
        r'upload\.', r'\.com/', r'\.org/'
    ]
    
    def __init__(self, images_dir: str = "static/uploads/medicines"):
        """Initialize with images directory path"""
        self.images_dir = images_dir
        self._cache: dict = {}
    
    def validate(self, medication_name: str) -> ImageValidationResult:
        """Validate and get image path for medication"""
        if not medication_name:
            return ImageValidationResult(False, None, "No name provided")
        
        normalized = self._normalize_name(medication_name)
        
        if normalized in self._cache:
            path = self._cache[normalized]
            if path:
                return ImageValidationResult(True, path, "Found")
            return ImageValidationResult(False, None, "Not found")
        
        image_path = self._find_image(normalized)
        self._cache[normalized] = image_path
        
        if image_path:
            return ImageValidationResult(True, image_path, "Valid local image")
        return ImageValidationResult(False, None, f"No image for: {normalized}")
    
    def validate_path(self, path: str) -> ImageValidationResult:
        """Validate a given image path is safe"""
        if not path:
            return ImageValidationResult(False, None, "Empty path")
        
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, path.lower()):
                return ImageValidationResult(False, None, f"BLOCKED: {pattern}")
        
        if path.startswith('http://') or path.startswith('https://'):
            return ImageValidationResult(False, None, "External URLs FORBIDDEN")
        
        ext = os.path.splitext(path)[1].lower()
        if ext not in self.VALID_EXTENSIONS:
            return ImageValidationResult(False, None, f"Invalid extension: {ext}")
        
        local_path = os.path.join(self.images_dir, os.path.basename(path))
        if os.path.exists(local_path):
            return ImageValidationResult(True, f"/{self.images_dir}/{os.path.basename(path)}", "Valid")
        
        return ImageValidationResult(False, None, "File not found")
    
    def block_external_url(self, url: str) -> bool:
        """Returns True if URL should be BLOCKED"""
        if not url:
            return True
        
        url_lower = url.lower()
        
        if url_lower.startswith('http://') or url_lower.startswith('https://'):
            return True
        
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        
        return False
    
    def _normalize_name(self, name: str) -> str:
        """Normalize medication name for image lookup"""
        normalized = name.lower().strip()
        normalized = re.sub(r'\d+\s*(mg|ml|mcg|g|iu|%)', '', normalized)
        for form in ['tablet', 'capsule', 'syrup', 'cream', 'gel']:
            normalized = re.sub(rf'\b{form}s?\b', '', normalized)
        return '_'.join(normalized.split()).strip('_')
    
    def _find_image(self, normalized_name: str) -> Optional[str]:
        """Find image file in local folder"""
        if not os.path.exists(self.images_dir):
            return None
        
        for ext in self.VALID_EXTENSIONS:
            path = os.path.join(self.images_dir, f"{normalized_name}{ext}")
            if os.path.exists(path):
                return f"/{self.images_dir}/{normalized_name}{ext}"
        
        for filename in os.listdir(self.images_dir):
            name_part = os.path.splitext(filename)[0].lower()
            ext = os.path.splitext(filename)[1].lower()
            if ext in self.VALID_EXTENSIONS:
                if name_part.startswith(normalized_name) or normalized_name.startswith(name_part):
                    return f"/{self.images_dir}/{filename}"
        
        return None
    
    def clear_cache(self):
        """Clear image cache"""
        self._cache.clear()
