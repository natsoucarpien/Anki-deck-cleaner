#!/usr/bin/env python3
"""
Anki Image Cropper
Crop les images (AVIF/PNG/JPEG) d'un deck Anki pour supprimer la mini-carte
Supporte: crop depuis une direction (droite/gauche/haut/bas) ou masquage d'un coin
"""

import zipfile
import shutil
import os
from pathlib import Path
from io import BytesIO

try:
    import pillow_avif
except ImportError:
    print("Installation de pillow-avif-plugin...")
    os.system("pip install pillow-avif-plugin")
    import pillow_avif

try:
    import zstandard as zstd
except ImportError:
    print("Installation de zstandard...")
    os.system("pip install zstandard")
    import zstandard as zstd

from PIL import Image


class AnkiImageCropper:
    """Classe pour cropper ou masquer les images d'un deck Anki"""

    # Modes disponibles
    MODE_CROP = "crop"
    MODE_MASK = "mask"

    # Directions de crop
    DIR_RIGHT = "right"
    DIR_LEFT = "left"
    DIR_TOP = "top"
    DIR_BOTTOM = "bottom"

    # Coins pour masquage
    CORNER_TOP_LEFT = "top_left"
    CORNER_TOP_RIGHT = "top_right"
    CORNER_BOTTOM_LEFT = "bottom_left"
    CORNER_BOTTOM_RIGHT = "bottom_right"

    # Couleurs de masque
    COLOR_BLACK = "black"
    COLOR_WHITE = "white"

    def __init__(self, input_file, mode=MODE_CROP, direction=DIR_RIGHT,
                 crop_percent=35, width_percent=35, height_percent=35,
                 mask_color=COLOR_BLACK):
        """
        Initialise le cropper

        Args:
            input_file: Chemin vers le fichier .apkg
            mode: "crop" pour recadrer, "mask" pour masquer un coin
            direction: Pour crop: "right", "left", "top", "bottom"
                       Pour mask: "top_left", "top_right", "bottom_left", "bottom_right"
            crop_percent: Pourcentage a retirer (pour mode crop)
            width_percent: Pourcentage de largeur du masque (pour mode mask)
            height_percent: Pourcentage de hauteur du masque (pour mode mask)
            mask_color: "black" ou "white" (pour mode mask)
        """
        self.input_file = Path(input_file)
        self.mode = mode
        self.direction = direction
        self.crop_percent = crop_percent
        self.width_percent = width_percent
        self.height_percent = height_percent
        self.mask_color = mask_color
        self.temp_dir = Path("temp_anki_crop")

        if not self.input_file.exists():
            raise FileNotFoundError(f"Le fichier {input_file} n'existe pas")

        if not self.input_file.suffix.lower() == '.apkg':
            raise ValueError("Le fichier doit etre un .apkg")

    def extract_apkg(self):
        """Extrait le contenu du fichier .apkg"""
        print(f"Extraction de {self.input_file.name}...")

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir()

        with zipfile.ZipFile(self.input_file, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

        print(f"Extraction terminee dans {self.temp_dir}")

    def decompress_zstd(self, data):
        """Decompresse des donnees zstd"""
        dctx = zstd.ZstdDecompressor()
        try:
            return dctx.decompress(data, max_output_size=10*1024*1024)
        except zstd.ZstdError:
            reader = dctx.stream_reader(BytesIO(data))
            result = reader.read()
            reader.close()
            return result

    def compress_zstd(self, data):
        """Compresse des donnees avec zstd"""
        cctx = zstd.ZstdCompressor()
        return cctx.compress(data)

    def is_zstd(self, data):
        """Verifie si les donnees sont compressees avec zstd"""
        return data[:4] == b'(\xb5/\xfd' or data[:2] == b'\xb5\xfd'

    def find_media_files(self):
        """Trouve tous les fichiers media (images) dans le deck"""
        import json

        images = []
        skip_files = ['media', 'collection.anki2', 'collection.anki21', 'collection.anki21b', 'meta']

        print("Scan des fichiers...")

        for file_path in self.temp_dir.iterdir():
            if file_path.is_file() and file_path.name not in skip_files:
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()

                    # Decompresser si zstd
                    is_compressed = self.is_zstd(data)
                    if is_compressed:
                        data = self.decompress_zstd(data)

                    # Detecter le type d'image
                    img_type = None
                    if data[:8] == b'\x89PNG\r\n\x1a\n':
                        img_type = 'png'
                    elif b'ftyp' in data[:32] and (b'avif' in data[:32] or b'avis' in data[:32] or b'mif1' in data[:32]):
                        img_type = 'avif'
                    elif data[:2] == b'\xff\xd8':
                        img_type = 'jpeg'

                    if img_type:
                        images.append({
                            'id': file_path.name,
                            'path': file_path,
                            'type': img_type,
                            'compressed': is_compressed
                        })

                except Exception as e:
                    print(f"  Erreur {file_path.name}: {e}")

        print(f"Trouve {len(images)} images")
        return images

    def process_image(self, image_info):
        """
        Traite une image selon le mode choisi (crop ou mask)

        Args:
            image_info: Dict avec 'path', 'type', 'compressed'

        Returns:
            True si succes, False sinon
        """
        try:
            file_path = image_info['path']
            is_compressed = image_info.get('compressed', False)
            img_type = image_info.get('type', 'png')

            # Lire le fichier
            with open(file_path, 'rb') as f:
                data = f.read()

            # Decompresser si necessaire
            if is_compressed:
                data = self.decompress_zstd(data)

            # Ouvrir l'image
            img = Image.open(BytesIO(data))
            width, height = img.size

            if self.mode == self.MODE_CROP:
                result = self._crop_directional(img, width, height)
            else:
                result = self._mask_corner(img, width, height)

            # Sauvegarder dans le bon format
            output = BytesIO()
            if img_type == 'png':
                result.save(output, 'PNG')
            elif img_type == 'jpeg':
                if result.mode in ('RGBA', 'P'):
                    result = result.convert('RGB')
                result.save(output, 'JPEG', quality=85)
            else:  # avif
                if result.mode in ('RGBA', 'P'):
                    result = result.convert('RGB')
                result.save(output, 'AVIF', quality=80)

            # Recompresser si necessaire
            result_data = output.getvalue()
            if is_compressed:
                result_data = self.compress_zstd(result_data)

            # Ecrire le fichier
            with open(file_path, 'wb') as f:
                f.write(result_data)

            return True

        except Exception as e:
            print(f"  Erreur: {e}")
            return False

    def _crop_directional(self, img, width, height):
        """
        Crop l'image depuis une direction donnee

        Args:
            img: Image PIL
            width: Largeur originale
            height: Hauteur originale

        Returns:
            Image croppee
        """
        if self.direction == self.DIR_RIGHT:
            # Retirer depuis la droite
            new_width = int(width * (100 - self.crop_percent) / 100)
            return img.crop((0, 0, new_width, height))

        elif self.direction == self.DIR_LEFT:
            # Retirer depuis la gauche
            crop_width = int(width * self.crop_percent / 100)
            return img.crop((crop_width, 0, width, height))

        elif self.direction == self.DIR_TOP:
            # Retirer depuis le haut
            crop_height = int(height * self.crop_percent / 100)
            return img.crop((0, crop_height, width, height))

        elif self.direction == self.DIR_BOTTOM:
            # Retirer depuis le bas
            new_height = int(height * (100 - self.crop_percent) / 100)
            return img.crop((0, 0, width, new_height))

        return img

    def _mask_corner(self, img, width, height):
        """
        Masque un coin de l'image avec une couleur unie

        Args:
            img: Image PIL
            width: Largeur originale
            height: Hauteur originale

        Returns:
            Image avec le coin masque
        """
        from PIL import ImageDraw

        # Copier l'image pour ne pas modifier l'originale
        result = img.copy()
        draw = ImageDraw.Draw(result)

        # Determiner la couleur
        color = (0, 0, 0) if self.mask_color == self.COLOR_BLACK else (255, 255, 255)
        if img.mode == 'RGBA':
            color = color + (255,)

        # Calculer les dimensions du masque
        mask_width = int(width * self.width_percent / 100)
        mask_height = int(height * self.height_percent / 100)

        # Dessiner le rectangle selon le coin choisi
        if self.direction == self.CORNER_TOP_LEFT:
            draw.rectangle([0, 0, mask_width, mask_height], fill=color)

        elif self.direction == self.CORNER_TOP_RIGHT:
            draw.rectangle([width - mask_width, 0, width, mask_height], fill=color)

        elif self.direction == self.CORNER_BOTTOM_LEFT:
            draw.rectangle([0, height - mask_height, mask_width, height], fill=color)

        elif self.direction == self.CORNER_BOTTOM_RIGHT:
            draw.rectangle([width - mask_width, height - mask_height, width, height], fill=color)

        return result

    def process_all_images(self):
        """Traite toutes les images du deck selon le mode choisi"""
        images = self.find_media_files()

        if not images:
            print("Aucune image a traiter")
            return 0

        # Message adapte au mode
        if self.mode == self.MODE_CROP:
            direction_names = {
                self.DIR_RIGHT: "droite",
                self.DIR_LEFT: "gauche",
                self.DIR_TOP: "haut",
                self.DIR_BOTTOM: "bas"
            }
            dir_name = direction_names.get(self.direction, self.direction)
            print(f"\nCrop de {len(images)} images ({self.crop_percent}% depuis {dir_name})...")
        else:
            corner_names = {
                self.CORNER_TOP_LEFT: "haut-gauche",
                self.CORNER_TOP_RIGHT: "haut-droite",
                self.CORNER_BOTTOM_LEFT: "bas-gauche",
                self.CORNER_BOTTOM_RIGHT: "bas-droite"
            }
            corner_name = corner_names.get(self.direction, self.direction)
            color_name = "noir" if self.mask_color == self.COLOR_BLACK else "blanc"
            print(f"\nMasquage coin {corner_name} de {len(images)} images "
                  f"({self.width_percent}% x {self.height_percent}%, {color_name})...")

        success_count = 0
        for i, img_info in enumerate(images, 1):
            print(f"  [{i}/{len(images)}] {img_info['id']}.{img_info['type']}", end="")

            if self.process_image(img_info):
                print(" - OK")
                success_count += 1
            else:
                print(" - ECHEC")

        return success_count

    def create_cropped_apkg(self, output_file=None):
        """Cree un nouveau fichier .apkg avec les images croppees"""
        if output_file is None:
            output_file = self.input_file.stem + "_cropped.apkg"

        output_path = Path(output_file)
        print(f"\nCreation de {output_path.name}...")

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.temp_dir)
                    zipf.write(file_path, arcname)

        print(f"Fichier cree: {output_path.absolute()}")
        return output_path

    def cleanup(self):
        """Supprime les fichiers temporaires"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        print("Fichiers temporaires supprimes")

    def process(self, output_file=None):
        """
        Processus complet de traitement

        Args:
            output_file: Nom du fichier de sortie (optionnel)

        Returns:
            Chemin vers le fichier traite
        """
        try:
            self.extract_apkg()
            processed_count = self.process_all_images()

            if processed_count > 0:
                output_path = self.create_cropped_apkg(output_file)
                return output_path
            else:
                print("Aucune image traitee, pas de fichier genere")
                return None
        finally:
            self.cleanup()


def get_int_input(prompt, default, min_val=1, max_val=90):
    """Demande un entier a l'utilisateur avec valeur par defaut"""
    user_input = input(prompt).strip()
    try:
        value = int(user_input) if user_input else default
    except ValueError:
        value = default
    if value < min_val or value > max_val:
        print(f"Valeur invalide, utilisation de {default}%")
        value = default
    return value


def main():
    """Fonction principale"""
    print("=" * 60)
    print("ANKI IMAGE CROPPER")
    print("Crop ou masque les images d'un deck Anki")
    print("=" * 60)
    print()

    # Demander le fichier
    input_file = input("Chemin vers le fichier .apkg : ").strip().strip('"').strip("'")
    print()

    # Choix du mode
    print("Mode de traitement:")
    print("  1. Crop (recadrer l'image)")
    print("  2. Masquer un coin")
    mode_input = input("Choix [1] : ").strip()
    mode = AnkiImageCropper.MODE_MASK if mode_input == "2" else AnkiImageCropper.MODE_CROP
    print()

    if mode == AnkiImageCropper.MODE_CROP:
        # Options pour le crop
        print("Direction du crop (bord a retirer):")
        print("  1. Droite")
        print("  2. Gauche")
        print("  3. Haut")
        print("  4. Bas")
        dir_input = input("Choix [1] : ").strip()

        directions = {
            "1": AnkiImageCropper.DIR_RIGHT,
            "2": AnkiImageCropper.DIR_LEFT,
            "3": AnkiImageCropper.DIR_TOP,
            "4": AnkiImageCropper.DIR_BOTTOM
        }
        direction = directions.get(dir_input, AnkiImageCropper.DIR_RIGHT)
        print()

        crop_percent = get_int_input("Pourcentage a retirer [35] : ", 35)
        print()

        cropper = AnkiImageCropper(
            input_file,
            mode=mode,
            direction=direction,
            crop_percent=crop_percent
        )

    else:
        # Options pour le masquage
        print("Coin a masquer:")
        print("  1. Bas-droite")
        print("  2. Bas-gauche")
        print("  3. Haut-droite")
        print("  4. Haut-gauche")
        corner_input = input("Choix [1] : ").strip()

        corners = {
            "1": AnkiImageCropper.CORNER_BOTTOM_RIGHT,
            "2": AnkiImageCropper.CORNER_BOTTOM_LEFT,
            "3": AnkiImageCropper.CORNER_TOP_RIGHT,
            "4": AnkiImageCropper.CORNER_TOP_LEFT
        }
        direction = corners.get(corner_input, AnkiImageCropper.CORNER_BOTTOM_RIGHT)
        print()

        width_percent = get_int_input("Largeur du masque en % [35] : ", 35)
        height_percent = get_int_input("Hauteur du masque en % [35] : ", 35)
        print()

        print("Couleur du masque:")
        print("  1. Noir")
        print("  2. Blanc")
        color_input = input("Choix [1] : ").strip()
        mask_color = AnkiImageCropper.COLOR_WHITE if color_input == "2" else AnkiImageCropper.COLOR_BLACK
        print()

        cropper = AnkiImageCropper(
            input_file,
            mode=mode,
            direction=direction,
            width_percent=width_percent,
            height_percent=height_percent,
            mask_color=mask_color
        )

    try:
        output_path = cropper.process()

        print()
        print("=" * 60)
        if output_path:
            print("TRAITEMENT TERMINE AVEC SUCCES !")
            print("=" * 60)
            print(f"Fichier original : {input_file}")
            print(f"Fichier traite   : {output_path}")
            print()
            print("Vous pouvez importer le fichier dans Anki.")
        else:
            print("AUCUNE IMAGE TRAITEE")
            print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print("ERREUR")
        print("=" * 60)
        print(f"Une erreur s'est produite : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print()
        input("Appuyez sur Entree pour fermer...")
