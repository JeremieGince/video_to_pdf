import sys
from modules.video_reader import VideoReader


if __name__ == '__main__':
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = r"C:\Users\gince\Documents\Laval_University\cours_A20\Apprentissage_par_renforcement_IFT-4201\Contenue\Semaine 5 - Les approches Bayésiennes"

    VideoReader(
        take_speech=True,
        verbose=False,
        language="fr-CA",
    ).make_pdf_from_folder(folder_path)

