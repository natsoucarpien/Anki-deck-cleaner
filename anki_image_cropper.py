#!/usr/bin/env python3
"""
Anki Image Cropper
Crop les images (AVIF/PNG/JPEG) d'un deck Anki pour supprimer la mini-carte (droite)
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
    """Classe pour cropper les images d'un deck Anki"""

    def __init__(self, input_file, crop_percent=30):
        """
        Initialise le cropper

        Args:
            input_file: Chemin vers le fichier .apkg
            crop_percent: Pourcentage a retirer depuis la droite (defaut: 30%)
        """
        self.input_file = Path(input_file)
        self.crop_percent = crop_percent
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

    def crop_image(self, image_info):
        """
        Crop une image en retirant X% depuis la droite

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
            original_width, height = img.size

            # Calculer la nouvelle largeur
            new_width = int(original_width * (100 - self.crop_percent) / 100)

            # Crop: garder la partie gauche
            cropped = img.crop((0, 0, new_width, height))

            # Sauvegarder dans le bon format
            output = BytesIO()
            if img_type == 'png':
                cropped.save(output, 'PNG')
            elif img_type == 'jpeg':
                if cropped.mode in ('RGBA', 'P'):
                    cropped = cropped.convert('RGB')
                cropped.save(output, 'JPEG', quality=85)
            else:  # avif
                if cropped.mode in ('RGBA', 'P'):
                    cropped = cropped.convert('RGB')
                cropped.save(output, 'AVIF', quality=80)

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

    def crop_all_images(self):
        """Crop toutes les images du deck"""
        images = self.find_media_files()

        if not images:
            print("Aucune image a traiter")
            return 0

        print(f"\nCrop de {len(images)} images ({self.crop_percent}% depuis la droite)...")

        success_count = 0
        for i, img_info in enumerate(images, 1):
            print(f"  [{i}/{len(images)}] {img_info['id']}.{img_info['type']}", end="")

            if self.crop_image(img_info):
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
        Processus complet de crop

        Args:
            output_file: Nom du fichier de sortie (optionnel)

        Returns:
            Chemin vers le fichier croppe
        """
        try:
            self.extract_apkg()
            cropped_count = self.crop_all_images()

            if cropped_count > 0:
                output_path = self.create_cropped_apkg(output_file)
                return output_path
            else:
                print("Aucune image croppee, pas de fichier genere")
                return None
        finally:
            self.cleanup()


def main():
    """Fonction principale"""
    print("=" * 60)
    print("ANKI IMAGE CROPPER")
    print("Supprime la mini-carte (droite) des images")
    print("=" * 60)
    print()

    # Demander le fichier
    input_file = input("Chemin vers le fichier .apkg : ").strip().strip('"').strip("'")

    # Demander le pourcentage
    print()
    print("Pourcentage a retirer depuis la droite (defaut: 30%)")
    crop_input = input("Pourcentage [30] : ").strip()

    try:
        crop_percent = int(crop_input) if crop_input else 30
    except ValueError:
        crop_percent = 30

    if crop_percent < 1 or crop_percent > 90:
        print("Pourcentage invalide, utilisation de 30%")
        crop_percent = 30

    print()

    try:
        cropper = AnkiImageCropper(input_file, crop_percent)
        output_path = cropper.process()

        print()
        print("=" * 60)
        if output_path:
            print("CROP TERMINE AVEC SUCCES !")
            print("=" * 60)
            print(f"Fichier original : {input_file}")
            print(f"Fichier croppe   : {output_path}")
            print()
            print("Vous pouvez importer le fichier croppe dans Anki.")
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
