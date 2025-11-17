"""
PSD processing utilities
"""
import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
from psd_tools import PSDImage
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

class PSDProcessor:
    def __init__(self, tesseract_cmd: str = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def remove_text_layers_recursive(self, layer, parent=None, parent_layers=None, index=None):
        """
        Recursively remove all text layers
        """
        if hasattr(layer, 'kind') and layer.kind == 'type':
            return True
        
        if hasattr(layer, 'is_group') and layer.is_group():
            for i in range(len(layer) - 1, -1, -1):
                sub_layer = layer[i]
                if self.remove_text_layers_recursive(sub_layer, layer, layer._layers, i):
                    del layer._layers[i]
        
        return False

    def detect_text_in_image(self, image_data, layer_name: str) -> bool:
        """
        Detect if an image contains text using OCR
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(np.array(image_data), cv2.COLOR_RGBA2GRAY)
            
            # Use Tesseract to detect text
            text = pytesseract.image_to_string(gray)
            
            # If we found any text, return True
            return len(text.strip()) > 0
            
        except Exception as e:
            print(f"Error in text detection for layer {layer_name}: {str(e)}")
            return False

    def _layer_to_cloud(self, layer) -> Optional[Dict[str, Any]]:
        """Convert a psd-tools layer to a minimal canvas cloud item for image widgets."""
        try:
            if getattr(layer, 'is_group', lambda: False)():
                return None
            # Skip fully hidden layers
            if hasattr(layer, 'visible') and not layer.visible:
                return None
            # bbox: (x1, y1, x2, y2)
            bbox = getattr(layer, 'bbox', None)
            if not bbox:
                return None
            left, top, right, bottom = bbox
            width = max(0, int(right - left))
            height = max(0, int(bottom - top))
            if width == 0 or height == 0:
                return None
            opacity = getattr(layer, 'opacity', 1)
            # psd-tools opacity may be 0..255
            opacity = float(opacity) / 255.0 if opacity and opacity > 1 else float(opacity or 1.0)
            return {
                "type": "image",
                "width": width,
                "height": height,
                "top": int(top),
                "left": int(left),
                "opacity": max(0.0, min(opacity, 1.0)),
            }
        except Exception as e:
            print(f"_layer_to_cloud error: {e}")
            return None

    def _export_layer_image(self, layer, dest_path: str) -> bool:
        try:
            img = None
            # group layer use composite, normal layer use topil
            if hasattr(layer, 'is_group') and layer.is_group():
                if hasattr(layer, 'composite'):
                    img = layer.composite()
            elif hasattr(layer, 'topil'):
                img = layer.topil()
            if img is None:
                return False
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            # Always export RGBA PNG
            img = img.convert('RGBA')
            img.save(dest_path, format='PNG')
            return True
        except Exception as e:
            print(f"export_layer_image error: {e}")
            return False

    def _remove_text_images_recursive(self, layer, skip_ocr: bool = False):
        """Recursively remove image layers that contain text by OCR."""
        try:
            if hasattr(layer, 'is_group') and layer.is_group():
                # Traverse children from end to start so deletion is safe
                for i in range(len(layer) - 1, -1, -1):
                    sub = layer[i]
                    self._remove_text_images_recursive(sub, skip_ocr)
                return
            # Non-group: optionally OCR check
            if skip_ocr:
                return
            if hasattr(layer, 'topil'):
                try:
                    img = layer.topil()
                    if img and self.detect_text_in_image(img, getattr(layer, 'name', '')):
                        # Remove itself from parent
                        if hasattr(layer, 'parent') and layer.parent is not None:
                            try:
                                parent = layer.parent
                                # parent._layers is used internally in psd-tools
                                idx = None
                                for j, l in enumerate(parent._layers):
                                    if l is layer:
                                        idx = j
                                        break
                                if idx is not None:
                                    del parent._layers[idx]
                            except Exception as e:
                                print(f"remove layer failed: {e}")
                except Exception as e:
                    print(f"OCR check error: {e}")
        except Exception as e:
            print(f"_remove_text_images_recursive error: {e}")

    def _build_canvas_data_grouped(self, psd, assets_root: str, group_dir: str) -> Dict[str, Any]:
        """
        Build canvas data where each TOP-LEVEL group is a basic element; non-group top-level layers are standalone elements.
        Exports each element as a PNG under uploads/canvas/<group_dir> maintaining z-order.
        """
        width, height = psd.size
        background = {"color": "#ffffff00", "image_url": ""}
        clouds: List[Dict[str, Any]] = []

        assets_rel_dir = os.path.join('canvas', group_dir)
        os.makedirs(os.path.join(assets_root, assets_rel_dir), exist_ok=True)

        layers = list(psd)
        # Background detection (bottom-most)
        try:
            if layers:
                bottom = layers[-1]
                if getattr(bottom, 'name', '').lower() in ['background', '背景'] and getattr(bottom, 'visible', True):
                    bg_rel = os.path.join(assets_rel_dir, 'background.png')
                    bg_abs = os.path.join(assets_root, bg_rel)
                    if self._export_layer_image(bottom, bg_abs):
                        background["image_url"] = bg_rel
        except Exception as e:
            print(f"background detection error: {e}")

        # Iterate top-level from bottom to top, insert at head to keep highest at end
        for idx, layer in enumerate(layers):
            if hasattr(layer, 'visible') and not layer.visible:
                continue
            name_lower = str(getattr(layer, 'name', '')).lower()
            if name_lower in ['background', '背景']:
                continue

            # Build cloud from group's bbox or layer bbox
            cloud = self._layer_to_cloud(layer)
            if not cloud:
                continue
            filename = f"elem_{idx}.png"
            rel_path = os.path.join(assets_rel_dir, filename)
            abs_path = os.path.join(assets_root, rel_path)
            if self._export_layer_image(layer, abs_path):
                cloud['image_url'] = rel_path
                clouds.insert(0, cloud)

        return {
            'width': width,
            'height': height,
            'background': background,
            'clouds': clouds,
        }

    def _collect_bottom_layers(self, layer, out: Optional[List] = None) -> List:
        if out is None:
            out = []
        try:
            if hasattr(layer, 'is_group') and layer.is_group():
                for sub in layer:
                    self._collect_bottom_layers(sub, out)
            else:
                out.append(layer)
        except Exception:
            pass
        return out

    def _build_canvas_data_leaf(self, psd, assets_root: str, group_dir: str) -> Dict[str, Any]:
        """
        Emulate back_end/process_psd_layers.py step 3: export all remaining bottom (leaf) layers as individual images,
        and return canvas data based on their bbox and order.
        """
        width, height = psd.size
        background = {"color": "#ffffff00", "image_url": ""}
        clouds: List[Dict[str, Any]] = []

        assets_rel_dir = os.path.join('canvas', group_dir)
        os.makedirs(os.path.join(assets_root, assets_rel_dir), exist_ok=True)

        # Background detection (bottom-most)
        try:
            layers = list(psd)
            if layers:
                bottom = layers[-1]
                if getattr(bottom, 'name', '').lower() in ['background', '背景'] and getattr(bottom, 'visible', True):
                    bg_rel = os.path.join(assets_rel_dir, 'background.png')
                    bg_abs = os.path.join(assets_root, bg_rel)
                    if self._export_layer_image(bottom, bg_abs):
                        background["image_url"] = bg_rel
        except Exception as e:
            print(f"background detection error: {e}")

        # Collect all remaining bottom layers
        bottom_layers: List = []
        for top in psd:
            self._collect_bottom_layers(top, bottom_layers)

        # Export and build clouds
        for idx, layer in enumerate(bottom_layers, start=1):
            if hasattr(layer, 'visible') and not layer.visible:
                continue
            cloud = self._layer_to_cloud(layer)
            if not cloud:
                continue
            safe_name = ''.join(c for c in str(getattr(layer, 'name', 'layer')).strip() if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"leaf_{idx}_{safe_name}.png"
            rel_path = os.path.join(assets_rel_dir, filename)
            abs_path = os.path.join(assets_root, rel_path)
            if self._export_layer_image(layer, abs_path):
                cloud['image_url'] = rel_path
                # Insert in order; leaf order follows traversal order similar to script
                clouds.append(cloud)

        return {
            'width': width,
            'height': height,
            'background': background,
            'clouds': clouds,
        }

    def process_psd(self, *, input_path: str, output_path: str, skip_ocr: bool = False, return_canvas: bool = False, assets_root: Optional[str] = None, canvas_mode: str = 'leaf') -> Dict[str, Any]:
        """Process PSD file - remove text layers, optional OCR removal, export flattened image and optionally return canvas data with per-layer images."""
        try:
            # Load PSD file
            psd = PSDImage.open(input_path)

            # Process layers: remove all text-type layers recursively
            for layer in reversed(psd):
                self.remove_text_layers_recursive(layer)

            # OCR pass for all image layers recursively (if not skipped)
            if not skip_ocr:
                for layer in list(psd):
                    self._remove_text_images_recursive(layer, skip_ocr=False)

            # Save the flattened result
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)

            if hasattr(psd, 'compose'):
                psd.compose().save(output_path)
            else:
                psd.save(output_path)

            result: Dict[str, Any] = {
                "status": "success",
                "output_path": output_path,
                "message": "PSD processed successfully",
            }

            if return_canvas and assets_root:
                # Group dir based on output filename stem
                group_dir = Path(output_path).stem + "_layers"
                if canvas_mode == 'group':
                    canvas = self._build_canvas_data_grouped(psd, assets_root=assets_root, group_dir=group_dir)
                else:
                    canvas = self._build_canvas_data_leaf(psd, assets_root=assets_root, group_dir=group_dir)
                result["canvas"] = canvas

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing PSD: {str(e)}"
            }
