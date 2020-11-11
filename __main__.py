import sys
from modules.video_reader import VideoReader


if __name__ == '__main__':
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = r"C:\Users\gince\Documents\Laval_University\cours_A20\Apprentissage_par_renforcement_IFT-4201\Contenue\Semaine 10 - Algorithmes d'apprentissage par renforcement séquentiel"

    if len(sys.argv) > 2:
        language = sys.argv[2]
    else:
        language = "fr-CA"

    VideoReader(
        take_speech=False,
        verbose=False,
        language=language,
    ).make_pdf_from_folder(folder_path)

