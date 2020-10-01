# Importing all necessary libraries
import os
import numpy as np
import cv2
import time
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import ImageReader
import io
from moviepy.editor import AudioFileClip
import speech_recognition as sr
import tqdm
import glob


def is_array_in_set(array_set, array: np.ndarray) -> bool:
    is_in = False
    for a in array_set:
        if np.allclose(a, array):
            is_in = True
            break
    return is_in


def is_array_in_set_at(array_set, array: np.ndarray, idx: int, threshold: float = 0.1):
    if len(array_set) == 0:
        return False
    return mse(array_set[idx], array) < threshold


def mse(a: np.ndarray, b: np.ndarray):
    return np.mean((a - b)**2)


class TapeFrame:
    def __init__(self,
                 image: np.ndarray,
                 audioclip: AudioFileClip = None,
                 init_time: float = None,
                 end_time: float = None,
                 **kwargs):
        self.image = image
        self.audioclip = audioclip
        self._text = None
        self.times = (init_time, end_time)
        self.eq_threshold = 0.1
        self._reco = sr.Recognizer()
        self.kwargs = kwargs

    @property
    def text(self) -> str:
        if self._text is None:
            self.audioclip_to_text()
        return self._text

    def audioclip_to_text(self):
        if self.audioclip is None:
            self._text = ""
            return None

        self.audioclip.write_audiofile(r"tempdata/audio.wav", verbose=False, logger=None)
        with sr.AudioFile(r"tempdata/audio.wav") as source:
            audio_file = self._reco.record(source)
        try:
            self._text = self._reco.recognize_google(audio_file, language=self.kwargs.get("language", "fr-CA"))
        except Exception:
            self._text = ""

    def __eq__(self, other):
        return mse(self.image, other.image) < self.eq_threshold

    def has_image(self, image):
        return mse(self.image, image) < self.eq_threshold


class Tapes:
    def __init__(self):
        self.tapes = []

    def add_tape(self, tape: TapeFrame) -> bool:
        has_tape = False
        if not self.has_tape(tape):
            self.tapes.append(tape)
            has_tape = True
        return has_tape

    def has_tape(self, tape: TapeFrame):
        return tape in self.tapes

    def has_image(self, image):
        return any([t.has_image(image) for t in self.tapes])

    def has_image_at(self, image, idx):
        if len(self) < abs(idx):
            return False
        return self.tapes[idx].has_image(image)

    def __getitem__(self, item):
        return self.tapes.__getitem__(item)

    def __len__(self):
        return len(self.tapes)


class PDF:
    def __init__(self, name: str, **kwargs):
        self._take_text = kwargs.get("take_text", True)
        self.img_size = (1_200, 750)
        self.page_size = (1_450, 1_200) if self._take_text else self.img_size
        self.saving_folder = kwargs.get("saving_folder", "resultsdata")
        self.canvas = Canvas(f"{self.saving_folder}/{name}.pdf", pagesize=self.page_size)
        self.font_size = 18
        self.canvas.setFont("Times-Roman", self.font_size)

    def add_diapo(self, tape_frame: TapeFrame, **kwargs):
        image = cv2.resize(tape_frame.image, self.img_size)
        self.canvas.drawImage(
            ImageReader(io.BytesIO(cv2.imencode(".jpg", image)[1])),
            0, self.page_size[1] - self.img_size[1]
        )

        if self._take_text:
            self.draw_text(tape_frame.text)

        self.canvas.drawString(self.font_size, self.font_size,
                               f"times: ({time.strftime('%H:%M:%S', time.gmtime(tape_frame.times[0]))} "
                               f"to {time.strftime('%H:%M:%S', time.gmtime(tape_frame.times[1]))}) [h:m:s]")

        self.canvas.showPage()

    def draw_text(self, text):
        text_line = ""
        line_idx = 1
        nb_c_a = self.page_size[0] - 2 * self.font_size
        words = text.split(' ')
        c_nb_c_a = nb_c_a
        for i in range(len(words)):
            text_line += words[i] + ' '
            c_nb_c_a -= (len(words[i]) + 1) * self.font_size
            # print(f"c_nb_c_a: {c_nb_c_a}, len(words[i+1]): {len(words[i+1]) if i != len(words)-1 else None}")
            if i != len(words) - 1 and len(words[i + 1]) > c_nb_c_a:
                self.canvas.drawString(self.font_size,
                                       (self.page_size[1] - self.img_size[1]) - self.font_size * line_idx,
                                       text_line)
                text_line = ""
                c_nb_c_a = nb_c_a
                line_idx += 1
        else:
            if text_line != "":
                self.canvas.drawString(self.font_size,
                                       (self.page_size[1] - self.img_size[1]) - self.font_size * line_idx,
                                       text_line)

    def add_diapos(self, tapes: Tapes):
        for tape in tapes:
            self.add_diapo(tape)

    def save(self):
        self.canvas.save()


class VideoReader:
    def __init__(self, dt: float = 1.0, take_speech: bool = True, verbose: bool = True, **kwargs):
        self.dt = dt
        self.take_speech = take_speech
        self.verbose = verbose
        self.saving_folder = kwargs.get("saving_folder", 'resultsdata')
        self.kwargs = kwargs

        os.makedirs("tempdata", exist_ok=True)
        os.makedirs("resultsdata", exist_ok=True)

    def make_pdf_from_mp4(self, mp4_filename: str):
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


if __name__ == '__main__':
    folder_path = r"C:\Users\gince\Documents\Laval_University\cours_A20\Apprentissage_par_renforcement_IFT-4201\Contenue\Semaine 5 - Les approches Bayésiennes"

    for mp4_file_path in tqdm.tqdm(glob.glob(os.path.join(folder_path, '*.mp4'))):
        VideoReader(
            take_speech=True,
            verbose=False,
            language="fr-CA",
            saving_folder=folder_path,
        ).make_pdf_from_mp4(mp4_file_path)

