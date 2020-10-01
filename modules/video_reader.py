import os
import cv2
import time
from moviepy.editor import AudioFileClip
import tqdm
import glob
from PyPDF2 import PdfFileMerger, PdfFileReader
from modules.tape import TapeFrame, Tapes, PDF


class VideoReader:
    def __init__(self, dt: float = 1.0, take_speech: bool = True, verbose: bool = True, **kwargs):
        self.dt = dt
        self.take_speech = take_speech
        self.verbose = verbose
        self.saving_folder = kwargs.get("saving_folder", 'resultsdata')
        self.kwargs = kwargs

        self.pdf_paths = []

        os.makedirs("tempdata", exist_ok=True)
        os.makedirs("resultsdata", exist_ok=True)

    def make_pdf_from_mp4(self, mp4_filename: str) -> str:
        vidcap = cv2.VideoCapture(mp4_filename)
        audioclip = AudioFileClip(mp4_filename) if self.take_speech else None

        pdf = PDF(os.path.basename(mp4_filename).replace(".mp4", ''),
                  take_text=self.take_speech,
                  saving_folder=self.saving_folder,)
        tapes = Tapes()
        cv2.startWindowThread()

        t_i = time.time()
        frame_start_time = 0
        frame_end_time = 0
        time_s = 0
        print(f"Reading of the video ...") if self.verbose else None
        while True:
            vidcap.set(cv2.CAP_PROP_POS_MSEC, time_s * 1_000)
            success, image = vidcap.read()
            if not success:
                break
            image = cv2.resize(image, (min(980, image.shape[0]), min(750, image.shape[1])))
            if not tapes.has_image_at(image, -1):
                frame_end_time = time_s
                if self.take_speech and len(tapes) > 0:
                    subaudio = audioclip.subclip(frame_start_time, frame_end_time)
                    # print("duration audio cut: ", time.strftime('%H:%M:%S', time.gmtime(subaudio.duration)),
                    #       " [h:m:s] ", (frame_start_time, frame_end_time))
                    tapes[-1].audioclip = subaudio
                if len(tapes) > 0:
                    frame_start_time = frame_end_time
                    tapes[-1].times = (frame_start_time, frame_end_time)
                tapes.add_tape(TapeFrame(image, **self.kwargs))

            time_s += self.dt

        cv2.destroyAllWindows()
        t_f = time.time()

        vidcap.release()
        print(f"Reading of the video done") if self.verbose else None

        print(f"Making the pdf...") if self.verbose else None
        pdf.add_diapos(tapes)
        pdf.save()
        print(f"Making pdf done") if self.verbose else None
        print(f"elapse time: {t_f - t_i:.2f} [s]") if self.verbose else None
        self.pdf_paths.append(pdf.path)
        return pdf.path

    def get_sort_pdf_paths(self) -> list:
        sorted_paths = self.pdf_paths.copy()
        sorted_paths.sort()
        return sorted_paths

    def make_pdf_from_folder(self, dir_path: str) -> str:
        self.saving_folder = dir_path
        for mp4_file_path in tqdm.tqdm(glob.glob(os.path.join(self.saving_folder, '*.mp4')), unit="mp4_file"):
            self.make_pdf_from_mp4(mp4_file_path)

        # Call the PdfFileMerger
        merged_pdf = PdfFileMerger()

        # Loop through all of pdf and append their pages
        for pdf_path in tqdm.tqdm(self.get_sort_pdf_paths(), unit="pdf_file"):
            merged_pdf.append(PdfFileReader(pdf_path, 'rb'))

        # Write all the files into a file which is named as shown below
        merged_pdf_path = f"{self.saving_folder}/{os.path.basename(dir_path)}.pdf"
        merged_pdf.write(merged_pdf_path)
        return merged_pdf_path
