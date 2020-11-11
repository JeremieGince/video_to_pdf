import os
import numpy as np
import cv2
import time
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
import io
from moviepy.editor import AudioFileClip
import speech_recognition as sr
from modules import util


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

        try:
            self.audioclip.write_audiofile(r"tempdata/audio.wav", verbose=False, logger=None)
            with sr.AudioFile(r"tempdata/audio.wav") as source:
                audio_file = self._reco.record(source)
            self._text = self._reco.recognize_google(audio_file, language=self.kwargs.get("language", "fr-CA"))
        except Exception:
            self._text = ""

    def __eq__(self, other):
        return util.mse(self.image, other.image) < self.eq_threshold

    def has_image(self, image):
        return util.mse(self.image, image) < self.eq_threshold


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
        self.name = name
        self.path = f"{self.saving_folder}/{name}.pdf"
        self.canvas = Canvas(self.path, pagesize=self.page_size)
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