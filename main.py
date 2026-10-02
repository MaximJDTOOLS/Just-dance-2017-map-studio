# main.py
# -*- coding: utf-8 -*-
"""
JD2017 Tool — редактор UbiArt Framework для Just Dance 2017 (PC).

Всё в одном файле:
  * Двуязычный UI (RU / EN)
  * CKD-парсер (actor, isc, tape, texture)
  * Таймлайн с drag & drop, waveform, плейхедом
  * Плеер через ffplay / Qt Multimedia / winsound
  * Упаковка/распаковка .ipk
  * Конвертация PC → PS4
  * MenuArt / Graph
  * Редактор пиктограмм
  * Метки танца (mashup, on stage, extreme, alt, sweat)
  * Unity2UbiArt (через AssetStudioModCLI)
"""

import os
import sys
import json
import zlib
import struct
import shutil
import tempfile
import subprocess
import threading
import wave
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QStatusBar, QFileDialog, QMessageBox,
    QToolBar, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QDockWidget, QListWidget, QListWidgetItem, QGroupBox, QCheckBox,
    QSplitter, QFrame, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsItem,
    QSlider, QScrollArea, QGridLayout, QSpinBox, QColorDialog,
    QPlainTextEdit, QTabWidget, QInputDialog, QMenu,
)
from PyQt6.QtGui import (
    QAction, QKeySequence, QBrush, QColor, QPen, QFont, QPixmap,
    QPainter, QImage, QIcon, QPolygonF,
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QUrl, QTimer, QElapsedTimer, pyqtSignal

# ---------- Опциональные бэкенды ----------
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    HAVE_QT_MEDIA = True
except ImportError:
    QMediaPlayer = QAudioOutput = None
    HAVE_QT_MEDIA = False

try:
    from PIL import Image, ImageDraw, ImageQt
    HAVE_PIL = True
except ImportError:
    Image = ImageDraw = ImageQt = None
    HAVE_PIL = False

FFPLAY_PATH  = shutil.which("ffplay")
FFPROBE_PATH = shutil.which("ffprobe")
FFMPEG_PATH  = shutil.which("ffmpeg")


# ===========================================================================
#  1.  ЛОКАЛИЗАЦИЯ
# ===========================================================================
STRINGS = {
    "ru": {
        "app_title": "JD2017 Tool — редактор UbiArt",
        "open": "Открыть проект", "save": "Сохранить проект",
        "save_as": "Сохранить как…",
        "exit": "Выход",
        "ipk_pack": "Упаковать IPK", "ipk_unpack": "Распаковать IPK",
        "convert_ps4": "Конвертировать в PS4",
        "songdesc": "SongDesc (isc.ckd)", "songdata": "SongData",
        "actor": "Редактор Actor",
        "menuart": "Создать MenuArt", "graph": "Создать Graph",
        "picto": "Редактор пиктограмм",
        "u2u": "Unity2UbiArt",
        "tags": "Метки танца",
        "mashup": "Mashup", "on_stage": "On Stage", "extreme": "Extreme",
        "alt": "Alt", "sweat": "Sweat",
        "timeline": "Таймлайн",
        "preview_video": "Предпросмотр видео",
        "preview_audio": "Предпросмотр аудио",
        "play": "▶  Play", "pause": "⏸  Pause", "stop": "⏹  Stop",
        "test": "🔔  Test", "diag": "🔧  FFmpeg",
        "status": "Статус:", "backend": "бэкенд:",
        "ready": "Готов",
        "tools": "Инструменты",
        "file": "Файл", "edit": "Правка", "view": "Вид", "language": "Язык",
        "no_media_clip": "Нет медиа-клипа.",
        "file_not_found": "Файл не найден:\n{0}",
        "songdesc_saved": "SongDesc сохранён: {0}",
        "songdata_saved": "SongData сохранён: {0}",
        "actor_loaded": "Actor загружен: {0}",
        "actor_saved": "Actor сохранён: {0}",
        "menuart_done": "MenuArt создан в: {0}",
        "graph_done": "Graph создан: {0}",
        "ipk_packed": "IPK упакован: {0}",
        "ipk_unpacked": "IPK распакован в: {0}",
        "ps4_converted": "Конвертация PS4 завершена: {0}",
        "u2u_done": "Unity2UbiArt: {0}",
        "project_saved": "Проект сохранён: {0}",
        "project_loaded": "Проект загружен: {0}",
        "tags_updated": "Метки: {0}",
        "error": "Ошибка",
        "warning": "Предупреждение",
        "information": "Информация",
        "ok": "OK", "cancel": "Отмена",
        "title": "Название", "artist": "Исполнитель",
        "bpm": "BPM", "duration": "Длительность (сек)",
        "main_scene": "MainScene",
        "actor_name": "Имя Actor", "skeleton": "Skeleton",
        "pick_color": "Выбрать цвет",
        "save_png": "Сохранить PNG", "save_png_ckd": "Сохранить .png.ckd",
        "clear": "Очистить",
        "left": "← Влево", "right": "→ Вправо",
        "up": "↑ Вверх", "down": "↓ Вниз",
        "arrow_size": "Размер", "color": "Цвет",
        "event_list": "События",
        "add_picto": "＋ Picto", "add_gold": "⭐ Gold Move",
        "add_audio": "🎧  Add Audio", "add_video": "🎬  Add Video",
        "hint": "• Ctrl+ЛКМ — пиктограмма • Delete — удалить • Ctrl+колесо — зум • Drag&Drop",
        "zoom": "Zoom:",
        "time": "Время:",
        "song_dir": "Папка проекта",
        "project_dir_select": "Выберите папку проекта",
        "output_dir": "Выходная папка",
        "input_dir": "Входная папка",
    },
    "en": {
        "app_title": "JD2017 Tool — UbiArt Editor",
        "open": "Open Project", "save": "Save Project",
        "save_as": "Save As…",
        "exit": "Exit",
        "ipk_pack": "Pack IPK", "ipk_unpack": "Unpack IPK",
        "convert_ps4": "Convert to PS4",
        "songdesc": "SongDesc (isc.ckd)", "songdata": "SongData",
        "actor": "Actor Editor",
        "menuart": "Create MenuArt", "graph": "Create Graph",
        "picto": "Pictogram Editor",
        "u2u": "Unity2UbiArt",
        "tags": "Dance Tags",
        "mashup": "Mashup", "on_stage": "On Stage", "extreme": "Extreme",
        "alt": "Alt", "sweat": "Sweat",
        "timeline": "Timeline",
        "preview_video": "Video Preview",
        "preview_audio": "Audio Preview",
        "play": "▶  Play", "pause": "⏸  Pause", "stop": "⏹  Stop",
        "test": "🔔  Test", "diag": "🔧  FFmpeg",
        "status": "Status:", "backend": "backend:",
        "ready": "Ready",
        "tools": "Tools",
        "file": "File", "edit": "Edit", "view": "View", "language": "Language",
        "no_media_clip": "No media clip.",
        "file_not_found": "File not found:\n{0}",
        "songdesc_saved": "SongDesc saved: {0}",
        "songdata_saved": "SongData saved: {0}",
        "actor_loaded": "Actor loaded: {0}",
        "actor_saved": "Actor saved: {0}",
        "menuart_done": "MenuArt created in: {0}",
        "graph_done": "Graph created: {0}",
        "ipk_packed": "IPK packed: {0}",
        "ipk_unpacked": "IPK unpacked to: {0}",
        "ps4_converted": "PS4 conversion done: {0}",
        "u2u_done": "Unity2UbiArt: {0}",
        "project_saved": "Project saved: {0}",
        "project_loaded": "Project loaded: {0}",
        "tags_updated": "Tags: {0}",
        "error": "Error",
        "warning": "Warning",
        "information": "Information",
        "ok": "OK", "cancel": "Cancel",
        "title": "Title", "artist": "Artist",
        "bpm": "BPM", "duration": "Duration (sec)",
        "main_scene": "MainScene",
        "actor_name": "Actor Name", "skeleton": "Skeleton",
        "pick_color": "Pick color",
        "save_png": "Save PNG", "save_png_ckd": "Save .png.ckd",
        "clear": "Clear",
        "left": "← Left", "right": "→ Right",
        "up": "↑ Up", "down": "↓ Down",
        "arrow_size": "Size", "color": "Color",
        "event_list": "Events",
        "add_picto": "＋ Picto", "add_gold": "⭐ Gold Move",
        "add_audio": "🎧  Add Audio", "add_video": "🎬  Add Video",
        "hint": "• Ctrl+LMB — picto • Delete — remove • Ctrl+wheel — zoom • Drag&Drop",
        "zoom": "Zoom:",
        "time": "Time:",
        "song_dir": "Project folder",
        "project_dir_select": "Select project folder",
        "output_dir": "Output folder",
        "input_dir": "Input folder",
    },
}

_current_lang = "ru"


def set_lang(lang: str):
    global _current_lang
    if lang in STRINGS:
        _current_lang = lang


def tr(key: str, *args) -> str:
    txt = STRINGS.get(_current_lang, STRINGS["en"]).get(key, key)
    if args:
        try:
            return txt.format(*args)
        except Exception:
            return txt
    return txt


# ===========================================================================
#  2.  ТЕМА
# ===========================================================================
DARK_QSS = """
* { font-family: "Segoe UI","Inter","Roboto",sans-serif; font-size: 13px; }
QMainWindow, QDialog, QWidget { background-color: #1b1d21; color: #e6e6e6; }
QMenuBar { background-color: #15171a; color: #e6e6e6; padding: 2px 6px; border-bottom: 1px solid #2a2d33; }
QMenuBar::item { padding: 6px 10px; background: transparent; border-radius: 6px; }
QMenuBar::item:selected { background: #2b2f36; }
QMenu { background-color: #202329; border: 1px solid #2f333a; border-radius: 8px; padding: 6px; }
QMenu::item { padding: 6px 24px 6px 12px; border-radius: 6px; }
QMenu::item:selected { background: #3a85ff; color: white; }
QMenu::separator { height: 1px; background: #2f333a; margin: 4px 8px; }
QToolBar { background-color: #1f2228; border: none; padding: 6px; spacing: 6px; border-bottom: 1px solid #2a2d33; }
QToolBar QToolButton { background-color: #2a2e36; color: #e6e6e6; border: 1px solid #333842; border-radius: 8px; padding: 6px 12px; }
QToolBar QToolButton:hover { background-color: #343a45; border-color: #3a85ff; }
QToolBar QToolButton:pressed { background-color: #2a6cd0; }
QPushButton { background-color: #2a2e36; color: #e6e6e6; border: 1px solid #333842; border-radius: 8px; padding: 6px 14px; min-height: 22px; }
QPushButton:hover { background-color: #343a45; border-color: #3a85ff; }
QPushButton:pressed { background-color: #2a6cd0; }
QPushButton:disabled { color: #6a6f78; background-color: #202329; }
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox { background-color: #202329; color: #e6e6e6; border: 1px solid #333842; border-radius: 6px; padding: 5px 8px; selection-background-color: #3a85ff; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #3a85ff; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView { background-color: #202329; border: 1px solid #333842; selection-background-color: #3a85ff; outline: none; }
QGroupBox { border: 1px solid #2a2d33; border-radius: 10px; margin-top: 14px; padding: 12px; background-color: #1f2228; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #9aa2ad; }
QStatusBar { background-color: #15171a; color: #9aa2ad; border-top: 1px solid #2a2d33; }
QScrollBar:vertical, QScrollBar:horizontal { background: #1b1d21; border: none; width: 10px; height: 10px; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #343a45; border-radius: 5px; min-height: 20px; min-width: 20px; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: #3a85ff; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #333842; border-radius: 4px; background-color: #202329; }
QCheckBox::indicator:checked { background-color: #3a85ff; border-color: #3a85ff; }
QTabWidget::pane { border: 1px solid #2a2d33; border-radius: 8px; background: #1f2228; }
QTabBar::tab { background: #202329; color: #9aa2ad; padding: 8px 16px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #2a2e36; color: #ffffff; }
QListWidget, QTreeWidget { background-color: #1f2228; border: 1px solid #2a2d33; border-radius: 8px; }
QListWidget::item { padding: 4px 6px; border-radius: 4px; }
QListWidget::item:selected { background: #3a85ff; color: white; }
QToolTip { background: #202329; color: #e6e6e6; border: 1px solid #3a85ff; border-radius: 6px; padding: 4px 8px; }
"""


# ===========================================================================
#  3.  ЯДРО CKD — контейнер, актёр, songdesc, songdata
# ===========================================================================
class CKDContainer:
    """Универсальный контейнер .ckd: zlib / JSON / raw bytes."""

    def __init__(self, data: bytes = b""):
        self.data = data
        self.payload = b""
        self._parse()

    def _parse(self):
        data = self.data
        # zlib
        if data[:2] == b"\x78\x9c" or data[:2] == b"\x78\xda":
            try:
                self.payload = zlib.decompress(data)
                return
            except zlib.error:
                pass
        # JSON
        stripped = data.lstrip(b"\xef\xbb\xbf").lstrip()
        if stripped[:1] in (b"{", b"["):
            self.payload = stripped
            return
        # иначе — сырые данные
        self.payload = data

    @classmethod
    def from_file(cls, path: str) -> "CKDContainer":
        with open(path, "rb") as f:
            return cls(f.read())

    def to_json(self):
        p = self.payload.lstrip()
        if p[:1] in (b"{", b"["):
            try:
                return json.loads(p.decode("utf-8"))
            except Exception:
                return None
        return None

    def save_raw(self, path: str):
        with open(path, "wb") as f:
            f.write(self.data)

    @staticmethod
    def write_json_ckd(path: str, obj: dict, compress: bool = False):
        data = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
        if compress:
            data = zlib.compress(data)
        with open(path, "wb") as f:
            f.write(data)


# ---------- SongDesc ----------
@dataclass
class SongDesc:
    title: str = ""
    artist: str = ""
    bpm: int = 120
    duration: float = 0.0
    main_scene: str = ""
    tags: List[str] = field(default_factory=list)
    coach_count: int = 1
    difficulty: int = 1
    lyrics: str = ""

    def to_dict(self) -> dict:
        return {
            "__class": "SongDesc",
            "Title": self.title,
            "Artist": self.artist,
            "Bpm": self.bpm,
            "Duration": self.duration,
            "MainScene": self.main_scene,
            "Tags": list(self.tags),
            "CoachCount": self.coach_count,
            "Difficulty": self.difficulty,
            "Lyrics": self.lyrics,
        }

    def save_pc(self, path: str):
        CKDContainer.write_json_ckd(path, self.to_dict())

    @classmethod
    def load(cls, path: str) -> "SongDesc":
        c = CKDContainer.from_file(path)
        js = c.to_json() or {}
        return cls(
            title=js.get("Title", ""),
            artist=js.get("Artist", ""),
            bpm=int(js.get("Bpm", 120)),
            duration=float(js.get("Duration", 0.0)),
            main_scene=js.get("MainScene", ""),
            tags=list(js.get("Tags", [])),
            coach_count=int(js.get("CoachCount", 1)),
            difficulty=int(js.get("Difficulty", 1)),
            lyrics=js.get("Lyrics", ""),
        )


# ---------- Actor ----------
@dataclass
class ActorFile:
    name: str = ""
    skeleton: str = ""
    animations: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "__class": "Actor",
            "ActorName": self.name,
            "Skeleton": self.skeleton,
            "Animations": list(self.animations),
            "Materials": list(self.materials),
        }

    def save(self, path: str):
        CKDContainer.write_json_ckd(path, self.to_dict())

    @classmethod
    def load(cls, path: str) -> "ActorFile":
        c = CKDContainer.from_file(path)
        js = c.to_json() or {}
        return cls(
            name=js.get("ActorName", ""),
            skeleton=js.get("Skeleton", ""),
            animations=list(js.get("Animations", [])),
            materials=list(js.get("Materials", [])),
        )


# ===========================================================================
#  4.  ТАЙМЛАЙН — модель
# ===========================================================================
@dataclass
class PictoEvent:
    time: float
    duration: float
    picto_path: str
    is_gold_move: bool = False


@dataclass
class MediaClip:
    time: float
    duration: float
    path: str
    kind: str                                  # "audio" | "video"
    waveform: Optional[List[float]] = None
    thumbnail: Optional[str] = None
    volume: float = 1.0


class TimelineModel:
    def __init__(self):
        self.events: List[PictoEvent] = []
        self.media: List[MediaClip] = []
        self.bpm: float = 120.0
        self.song_name: str = ""

    # --- Пиктограммы ---
    def add_picto(self, time, duration, picto_path, gold=False) -> PictoEvent:
        ev = PictoEvent(time, duration, picto_path, gold)
        self.events.append(ev)
        return ev

    def remove_picto(self, ev: PictoEvent):
        if ev in self.events:
            self.events.remove(ev)

    # --- Медиа ---
    def add_media(self, path, kind, time=0.0, duration=0.0,
                  waveform=None, thumbnail=None, volume=1.0) -> MediaClip:
        c = MediaClip(time, duration, path, kind, waveform, thumbnail, volume)
        self.media.append(c)
        return c

    def remove_media(self, clip: MediaClip):
        if clip in self.media:
            self.media.remove(clip)

    # --- JSON / dtape ---
    def to_dict(self) -> dict:
        return {
            "bpm": self.bpm,
            "song": self.song_name,
            "events": [
                {"time": e.time, "duration": e.duration,
                 "picto": e.picto_path, "gold": e.is_gold_move}
                for e in self.events
            ],
            "media": [
                {"time": m.time, "duration": m.duration, "path": m.path,
                 "kind": m.kind, "volume": m.volume}
                for m in self.media
            ],
        }

    def export_dtape_pc(self, path: str):
        CKDContainer.write_json_ckd(path, self.to_dict())

    def export_dtape_ps3(self, path: str):
        """Big-endian бинарный dtape (совместим с реальным JD)."""
        buf = bytearray()
        buf += struct.pack(">I", 0x12D12FB9)
        buf += struct.pack(">I", len(self.events))
        for e in self.events:
            buf += struct.pack(">I", int(e.time * 1000))
            buf += struct.pack(">I", int(e.duration * 1000))
            name = e.picto_path.encode("utf-8")
            buf += struct.pack(">I", len(name))
            buf += name
            buf += struct.pack(">?", e.is_gold_move)
        with open(path, "wb") as f:
            f.write(bytes(buf))


# ===========================================================================
#  5.  МЕДИА — загрузка длительности / waveform / превью
# ===========================================================================
AUDIO_EXT = {".ogg", ".oga", ".opus", ".wav", ".mp3", ".flac", ".m4a", ".aac"}
VIDEO_EXT = {".webm", ".mp4", ".mov", ".mkv", ".avi", ".m4v"}
PICTO_EXT = {".png", ".tga"}
WMF_UNSUPPORTED = {".ogg", ".oga", ".opus", ".flac", ".webm", ".mkv", ".ogv"}


def _hidden_startupinfo():
    if os.name != "nt":
        return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    return si


def _decode_pcm(raw: bytes, sampwidth: int, nchan: int) -> List[float]:
    if sampwidth == 1:
        return [(b - 128) / 128.0 for b in raw]
    if sampwidth == 2:
        n = len(raw) // 2
        vals = struct.unpack("<" + "h" * n, raw[:n * 2])
        if nchan > 1:
            vals = [sum(vals[i:i + nchan]) / nchan
                    for i in range(0, len(vals), nchan)]
        return [v / 32768.0 for v in vals]
    if sampwidth == 4:
        n = len(raw) // 4
        vals = struct.unpack("<" + "i" * n, raw[:n * 4])
        if nchan > 1:
            vals = [sum(vals[i:i + nchan]) / nchan
                    for i in range(0, len(vals), nchan)]
        return [v / 2147483648.0 for v in vals]
    return []


def _downsample(samples: List[float], bins: int = 600) -> List[float]:
    if not samples:
        return []
    step = max(1, len(samples) // bins)
    out = []
    for i in range(0, len(samples), step):
        chunk = samples[i:i + step]
        peak = max((abs(x) for x in chunk), default=0.0)
        out.append(min(1.0, peak))
    return out[:bins]


def load_audio_info(path: str):
    """(duration, waveform, error_or_None)"""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".wav":
        try:
            with wave.open(path, "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate() or 1
                dur = frames / float(rate)
                w.setpos(0)
                raw = w.readframes(min(frames, rate * 30))
                sw, nc = w.getsampwidth(), w.getnchannels()
            return dur, _downsample(_decode_pcm(raw, sw, nc)), None
        except Exception as e:
            return 0.0, [], f"WAV: {e}"
    # остальные — через mutagen/ffprobe
    try:
        from mutagen import File as MFile
        mf = MFile(path)
        if mf and mf.info:
            return float(mf.info.length), [], None
    except Exception:
        pass
    if FFPROBE_PATH:
        try:
            out = subprocess.run(
                [FFPROBE_PATH, "-v", "error",
                 "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True, timeout=10,
                startupinfo=_hidden_startupinfo(),
            )
            return float((out.stdout or "0").strip() or 0.0), [], None
        except Exception as e:
            return 0.0, [], str(e)
    return 0.0, [], None


def load_video_info(path: str):
    """(duration, thumbnail_path, error_or_None)"""
    if not FFMPEG_PATH or not FFPROBE_PATH:
        return 0.0, None, "ffmpeg/ffprobe не найдены"
    dur = 0.0
    thumb = None
    try:
        out = subprocess.run(
            [FFPROBE_PATH, "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10,
            startupinfo=_hidden_startupinfo(),
        )
        dur = float((out.stdout or "0").strip() or 0.0)
    except Exception:
        pass
    try:
        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        subprocess.run(
            [FFMPEG_PATH, "-y", "-ss", "1", "-i", path,
             "-frames:v", "1", "-vf", "scale=320:-1", tmp],
            capture_output=True, check=True, timeout=20,
            startupinfo=_hidden_startupinfo(),
        )
        if os.path.getsize(tmp) > 0:
            thumb = tmp
    except Exception:
        thumb = None
    return dur, thumb, None


def has_audio_stream(path: str) -> bool:
    if not FFPROBE_PATH:
        return True
    try:
        out = subprocess.run(
            [FFPROBE_PATH, "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=8,
            startupinfo=_hidden_startupinfo(),
        )
        return "audio" in (out.stdout or "").lower()
    except Exception:
        return True


# ===========================================================================
#  6.  IPK — упаковка / распаковка
# ===========================================================================
class IPKArchive:
    MAGIC = b"\x50\xec\x12\xba"

    @staticmethod
    def unpack(ipk_path: str, out_dir: str) -> int:
        """Возвращает число распакованных файлов."""
        with open(ipk_path, "rb") as f:
            data = f.read()
        if not data.startswith(IPKArchive.MAGIC):
            raise ValueError("Не IPK-файл (неверная сигнатура)")

        version = struct.unpack_from(">I", data, 0x04)[0]
        base_off = struct.unpack_from(">I", data, 0x0C)[0]
        file_count = struct.unpack_from(">I", data, 0x10)[0]

        entries = []
        pos = 0x30
        for _ in range(file_count):
            type_flag = struct.unpack_from(">I", data, pos)[0]; pos += 4
            usize = struct.unpack_from(">I", data, pos)[0]; pos += 4
            csize = struct.unpack_from(">I", data, pos)[0]; pos += 4
            _ts   = struct.unpack_from(">I", data, pos)[0]; pos += 4
            offset = struct.unpack_from(">Q", data, pos)[0]; pos += 8
            if type_flag == 2:
                pos += 8
            plen = struct.unpack_from(">I", data, pos)[0]; pos += 4
            path = data[pos:pos + plen].decode("utf-8", errors="replace"); pos += plen
            nlen = struct.unpack_from(">I", data, pos)[0]; pos += 4
            name = data[pos:pos + nlen].decode("utf-8", errors="replace"); pos += nlen
            _crc = struct.unpack_from(">I", data, pos)[0]; pos += 4
            pos += 4
            entries.append((path, name, offset, usize, csize))

        os.makedirs(out_dir, exist_ok=True)
        count = 0
        for path, name, offset, usize, csize in entries:
            abs_off = base_off + offset
            if csize == 0:
                chunk = data[abs_off:abs_off + usize]
            else:
                try:
                    chunk = zlib.decompress(data[abs_off:abs_off + csize])
                except zlib.error:
                    chunk = data[abs_off:abs_off + csize]

            safe = path.replace("\\", "/").lstrip("/").replace("..", "_")
            full = Path(out_dir) / safe / name
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(chunk)
            count += 1
        return count

    @staticmethod
    def pack(in_dir: str, out_ipk: str) -> int:
        """Возвращает число упакованных файлов."""
        files = []
        for root, _, fnames in os.walk(in_dir):
            for fn in fnames:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, in_dir).replace("\\", "/")
                dirname, basename = os.path.split(rel)
                with open(full, "rb") as f:
                    content = f.read()
                files.append((dirname, basename, content))

        # Заголовок: считаем размер
        header_size = 0x30
        for dirname, basename, content in files:
            header_size += 4 * 5 + 8         # type, usize, csize, tstamp, crc, unk, offset(8)
            header_size += 4 + len(dirname.encode("utf-8"))
            header_size += 4 + len(basename.encode("utf-8"))
        base_off = header_size

        with open(out_ipk, "wb") as f:
            f.write(IPKArchive.MAGIC)
            f.write(struct.pack(">I", 5))
            f.write(struct.pack(">I", 0))
            f.write(struct.pack(">I", base_off))
            f.write(struct.pack(">I", len(files)))
            f.write(b"\x00" * (0x30 - 20))

            offset = 0
            payloads = []
            for dirname, basename, content in files:
                db = dirname.encode("utf-8")
                nb = basename.encode("utf-8")
                crc = zlib.crc32(content) & 0xFFFFFFFF
                f.write(struct.pack(">I", 1))
                f.write(struct.pack(">I", len(content)))
                f.write(struct.pack(">I", 0))          # не сжато
                f.write(struct.pack(">I", 0))
                f.write(struct.pack(">Q", offset))
                f.write(struct.pack(">I", len(db))); f.write(db)
                f.write(struct.pack(">I", len(nb))); f.write(nb)
                f.write(struct.pack(">I", crc))
                f.write(struct.pack(">I", 0))
                payloads.append(content)
                offset += len(content)

            cur = f.tell()
            if cur < base_off:
                f.write(b"\x00" * (base_off - cur))
            for p in payloads:
                f.write(p)
        return len(files)


# ===========================================================================
#  7.  КОНВЕРТЕРЫ
# ===========================================================================
class PCtoPS4Converter:
    """Best-effort конвертация: cмена endianness и упаковка."""

    def __init__(self, song_dir: str):
        self.song_dir = song_dir
        self.log: List[str] = []

    def _log(self, msg: str):
        self.log.append(msg)
        print("[ps4]", msg)

    def convert_all(self, out_dir: str) -> str:
        os.makedirs(out_dir, exist_ok=True)
        src = self.song_dir

        # dtape
        dtape_src = self._find_first(src, [".dtape.ckd", ".ktape.ckd", ".stape.ckd"])
        if dtape_src:
            try:
                tl = _load_dtape(dtape_src)
                dst = os.path.join(out_dir, os.path.basename(dtape_src)
                                   .replace(".dtape.ckd", ".dtape.ckd"))
                tl.export_dtape_ps3(dst)
                self._log(f"dtape → {dst}")
            except Exception as e:
                self._log(f"dtape error: {e}")

        # songdesc
        isc_src = self._find_first(src, [".isc.ckd"])
        if isc_src:
            try:
                sd = SongDesc.load(isc_src)
                dst = os.path.join(out_dir, os.path.basename(isc_src))
                sd.save_pc(dst)   # JSON остаётся валидным
                self._log(f"songdesc → {dst}")
            except Exception as e:
                self._log(f"isc error: {e}")

        # actor
        act_src = self._find_first(src, [".act.ckd"])
        if act_src:
            try:
                af = ActorFile.load(act_src)
                dst = os.path.join(out_dir, os.path.basename(act_src))
                af.save(dst)
                self._log(f"actor → {dst}")
            except Exception as e:
                self._log(f"actor error: {e}")

        self._log("Готово. Для полной совместимости PS4 нужны DDS→GNF и OGG→AT9 (вне рамок Python).")
        return "\n".join(self.log)

    @staticmethod
    def _find_first(root: str, suffixes: List[str]) -> Optional[str]:
        for r, _, files in os.walk(root):
            for fn in files:
                for s in suffixes:
                    if fn.endswith(s):
                        return os.path.join(r, fn)
        return None


def _load_dtape(path: str) -> TimelineModel:
    """Читает .dtape.ckd (JSON или big-endian)."""
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] in (b"\x78\x9c", b"\x78\xda"):
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            pass
    stripped = raw.lstrip()
    if stripped[:1] in (b"{", b"["):
        js = json.loads(raw.decode("utf-8"))
        tl = TimelineModel()
        tl.bpm = js.get("bpm", 120.0)
        tl.song_name = js.get("song", "")
        for ev in js.get("events", []):
            tl.add_picto(ev["time"], ev["duration"], ev["picto"],
                         ev.get("gold", False))
        return tl
    # бинарный
    if len(raw) >= 8 and struct.unpack(">I", raw[:4])[0] == 0x12D12FB9:
        tl = TimelineModel()
        pos = 4
        n = struct.unpack(">I", raw[pos:pos + 4])[0]; pos += 4
        for _ in range(n):
            t = struct.unpack(">I", raw[pos:pos + 4])[0]; pos += 4
            d = struct.unpack(">I", raw[pos:pos + 4])[0]; pos += 4
            nl = struct.unpack(">I", raw[pos:pos + 4])[0]; pos += 4
            nm = raw[pos:pos + nl].decode("utf-8", "replace"); pos += nl
            g = struct.unpack(">?", raw[pos:pos + 1])[0]; pos += 1
            tl.add_picto(t / 1000.0, d / 1000.0, nm, g)
        return tl
    raise ValueError(f"Неизвестный формат dtape: {path}")


class Unity2UbiArt:
    """Конвертер Unity .bundle → UbiArt tape через AssetStudioModCLI."""

    def __init__(self):
        self.asset_studio = self._find_asset_studio()

    @staticmethod
    def _find_asset_studio() -> Optional[str]:
        here = Path(__file__).resolve().parent
        for c in [
            here / "AssetStudioModCLI.exe",
            here / "AssetStudioModCLI" / "AssetStudioModCLI.exe",
            here / "bin" / "AssetStudioModCLI.exe",
            here / "bin" / "AssetStudioModCLI" / "AssetStudioModCLI.exe",
            here / "tools" / "AssetStudioModCLI.exe",
        ]:
            if c.is_file():
                return str(c)
        return shutil.which("AssetStudioModCLI") or shutil.which("AssetStudioModCLI.exe")

    def help_text(self) -> str:
        if self.asset_studio:
            return f"✅ AssetStudio: {self.asset_studio}"
        return (
            "❌ AssetStudioModCLI.exe не найден.\n\n"
            "Скачайте: https://github.com/aelurum/AssetStudio/releases\n"
            "Файл AssetStudioModCLI_netX.zip.\n\n"
            "Положите рядом с main.py:\n"
            "  ./AssetStudioModCLI/AssetStudioModCLI.exe\n"
            "(всё содержимое архива — exe не работает без .dll)"
        )

    def convert(self, bundle_path: str, map_name: str, out_dir: str,
                on_progress=None) -> str:
        if not self.asset_studio:
            raise RuntimeError(self.help_text())
        if not os.path.isfile(bundle_path):
            raise RuntimeError(f"Bundle не найден:\n{bundle_path}")
        os.makedirs(out_dir, exist_ok=True)
        extracted = os.path.join(out_dir, "extracted")

        if on_progress:
            on_progress(f"Извлечение: {os.path.basename(bundle_path)}")
        try:
            res = subprocess.run(
                [self.asset_studio, bundle_path, "--output", extracted,
                 "--log-level", "warning"],
                capture_output=True, text=True, timeout=600,
                startupinfo=_hidden_startupinfo(),
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Не удалось запустить AssetStudioModCLI.exe\n"
                f"Путь: {self.asset_studio}\n\n" + self.help_text()
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("AssetStudio не завершился за 10 минут.")

        if res.returncode != 0:
            raise RuntimeError(
                f"AssetStudio завершился с кодом {res.returncode}\n"
                f"STDERR:\n{(res.stderr or '')[:500]}"
            )

        # проверяем, что что-то извлеклось
        files = [p for p in Path(extracted).rglob("*") if p.is_file()]
        if not files:
            raise RuntimeError("AssetStudio не извлёк файлов из bundle.")

        if on_progress:
            on_progress(f"Извлечено файлов: {len(files)}")

        # собираем dtape-каркас
        tape_path = os.path.join(out_dir, f"{map_name}.dtape.ckd")
        TimelineModel().export_dtape_pc(tape_path)
        if on_progress:
            on_progress(f"Готово: {out_dir}")
        return tape_path


# ===========================================================================
#  8.  MENUART / GRAPH
# ===========================================================================
class MenuArtBuilder:
    def __init__(self, song_name: str):
        self.song_name = song_name or "song"

    def create_isc(self, path: str):
        data = {
            "__class": "MenuArt",
            "Song": self.song_name,
            "Icon": f"{self.song_name}_icon.tga.ckd",
            "Background": f"{self.song_name}_bg.tga.ckd",
            "CoachCount": 1,
        }
        CKDContainer.write_json_ckd(path, data)

    def create_tga(self, path: str, png_path: Optional[str] = None):
        """Конвертация PNG → TGA (используя PIL, если доступен)."""
        if HAVE_PIL and png_path and os.path.isfile(png_path):
            img = Image.open(png_path)
            img.save(path, "TGA")
        else:
            # Создаём пустую TGA 1×1 пиксель
            header = bytearray(18)
            header[2] = 2                     # uncompressed true-color
            header[12] = 1; header[14] = 1    # width=1, height=1
            header[16] = 32                   # bpp
            with open(path, "wb") as f:
                f.write(bytes(header))
                f.write(b"\x00\x00\x00\x00")

    def create_act(self, path: str):
        ActorFile(name=self.song_name + "_menu").save(path)

    def create_graph(self, path: str):
        graph = {
            "__class": "Graph",
            "Nodes": [
                {"id": "root", "type": "scene", "children": ["menuart"]},
                {"id": "menuart", "type": "menu", "children": []},
            ],
        }
        CKDContainer.write_json_ckd(path, graph)


# ===========================================================================
#  9.  ТЕГИ
# ===========================================================================
DANCE_TAGS = ["mashup", "on_stage", "extreme", "alt", "sweat"]


# ===========================================================================
#  10.  РЕДАКТОР ПИКТОГРАММ
# ===========================================================================
class PictoEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 " + tr("picto"))
        self.setMinimumSize(600, 700)

        self.img = QImage(256, 256, QImage.Format.Format_ARGB32)
        self.img.fill(Qt.GlobalColor.transparent)
        self.brush_color = QColor(255, 255, 255, 255)
        self.arrow_size = 24

        v = QVBoxLayout(self)

        # Панель инструментов
        top = QHBoxLayout()
        top.addWidget(QLabel(tr("color") + ":"))
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(40, 26)
        self._update_color_btn()
        self.btn_color.clicked.connect(self._pick_color)
        top.addWidget(self.btn_color)

        top.addWidget(QLabel(tr("arrow_size") + ":"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 120)
        self.size_spin.setValue(24)
        self.size_spin.valueChanged.connect(lambda v: setattr(self, "arrow_size", v))
        top.addWidget(self.size_spin)

        btn_clear = QPushButton(tr("clear"))
        btn_clear.clicked.connect(self._clear)
        top.addWidget(btn_clear)
        top.addStretch(1)
        v.addLayout(top)

        # Canvas
        self.canvas = QLabel()
        self.canvas.setFixedSize(256, 256)
        self.canvas.setStyleSheet(
            "background: #202329; border: 1px solid #333842; border-radius: 8px;"
        )
        v.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._refresh_canvas()

        # Стрелки
        arrows = QHBoxLayout()
        for key, lbl in [("left", tr("left")), ("right", tr("right")),
                         ("up", tr("up")), ("down", tr("down"))]:
            b = QPushButton(lbl)
            b.clicked.connect(lambda _, k=key: self._draw(k))
            arrows.addWidget(b)
        v.addLayout(arrows)

        # Сохранение
        save = QHBoxLayout()
        b1 = QPushButton(tr("save_png"))
        b1.clicked.connect(self._save_png)
        save.addWidget(b1)
        b2 = QPushButton(tr("save_png_ckd"))
        b2.clicked.connect(self._save_png_ckd)
        save.addWidget(b2)
        v.addLayout(save)

    def _update_color_btn(self):
        c = self.brush_color
        self.btn_color.setStyleSheet(
            f"background: rgba({c.red()},{c.green()},{c.blue()},{c.alpha()});"
            "border: 1px solid #333842; border-radius: 6px;"
        )

    def _pick_color(self):
        c = QColorDialog.getColor(self.brush_color, self, tr("pick_color"),
                                  QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if c.isValid():
            self.brush_color = c
            self._update_color_btn()

    def _refresh_canvas(self):
        self.canvas.setPixmap(QPixmap.fromImage(self.img))

    def _clear(self):
        self.img.fill(Qt.GlobalColor.transparent)
        self._refresh_canvas()

    def _draw(self, direction: str):
        p = QPainter(self.img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self.brush_color))
        cx, cy = 128, 128
        s = self.arrow_size
        if direction == "right":
            poly = QPolygonF([QPointF(cx, cy),
                              QPointF(cx + s, cy - s // 2),
                              QPointF(cx + s, cy + s // 2)])
        elif direction == "left":
            poly = QPolygonF([QPointF(cx, cy),
                              QPointF(cx - s, cy - s // 2),
                              QPointF(cx - s, cy + s // 2)])
        elif direction == "up":
            poly = QPolygonF([QPointF(cx, cy),
                              QPointF(cx - s // 2, cy - s),
                              QPointF(cx + s // 2, cy - s)])
        else:
            poly = QPolygonF([QPointF(cx, cy),
                              QPointF(cx - s // 2, cy + s),
                              QPointF(cx + s // 2, cy + s)])
        p.drawPolygon(poly)
        p.end()
        self._refresh_canvas()

    def _save_png(self):
        f, _ = QFileDialog.getSaveFileName(self, tr("save_png"), "", "PNG (*.png)")
        if f:
            if not f.lower().endswith(".png"):
                f += ".png"
            self.img.save(f, "PNG")

    def _save_png_ckd(self):
        f, _ = QFileDialog.getSaveFileName(self, tr("save_png_ckd"), "",
                                          "PNG CKD (*.png.ckd)")
        if not f:
            return
        if not f.lower().endswith(".png.ckd"):
            f += ".png.ckd"
        buf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        try:
            self.img.save(buf.name, "PNG")
            buf.close()
            with open(buf.name, "rb") as fh:
                png_data = fh.read()
        finally:
            try: os.unlink(buf.name)
            except Exception: pass
        compressed = zlib.compress(png_data)
        with open(f, "wb") as fh:
            fh.write(len(compressed).to_bytes(4, "little"))
            fh.write(compressed)


# ===========================================================================
#  11.  ТАЙМЛАЙН — визуальная часть и плеер
# ===========================================================================
PX_PER_SEC = 120
MAX_SECONDS = 500

RULER_H = 28
PICTO_H = 44
GOLD_H = 44
AUDIO_H = 60
VIDEO_H = 60

Y_PICTO = RULER_H
Y_GOLD = Y_PICTO + PICTO_H
Y_AUDIO = Y_GOLD + GOLD_H
Y_VIDEO = Y_AUDIO + AUDIO_H
TOTAL_H = Y_VIDEO + VIDEO_H + 24

SNAP_SEC = 0.05


def _fmt_time(s: float) -> str:
    if s < 0: s = 0.0
    m = int(s // 60)
    sec = s - m * 60
    return f"{m:02d}:{sec:06.3f}"


class PictoItem(QGraphicsRectItem):
    def __init__(self, ev: PictoEvent, editor: "TimelineView"):
        w = max(ev.duration * PX_PER_SEC, 24)
        super().__init__(0, 0, w, PICTO_H - 12)
        self.ev = ev
        self._row_y = Y_PICTO if not ev.is_gold_move else Y_GOLD
        color = QColor("#ffb400") if ev.is_gold_move else QColor("#3a85ff")
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#ffffff"), 1))
        self.setZValue(10)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setPos(ev.time * PX_PER_SEC, self._row_y + 6)
        label = QGraphicsTextItem(ev.picto_path.split("/")[-1], self)
        label.setDefaultTextColor(QColor("#ffffff"))
        label.setFont(QFont("Segoe UI", 8))
        label.setPos(4, 4)
        label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            step = PX_PER_SEC * SNAP_SEC
            return QPointF(max(0.0, round(value.x() / step) * step),
                           self._row_y + 6)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.ev.time = self.pos().x() / PX_PER_SEC
        return super().itemChange(change, value)


class MediaItem(QGraphicsRectItem):
    def __init__(self, clip: MediaClip, editor: "TimelineView"):
        self.clip = clip
        kind = clip.kind
        h = AUDIO_H if kind == "audio" else VIDEO_H
        y = Y_AUDIO if kind == "audio" else Y_VIDEO
        w = max(clip.duration * PX_PER_SEC, 80)
        super().__init__(0, 0, w, h - 8)
        self._row_y = y
        base = QColor("#2ecc71") if kind == "audio" else QColor("#9b59b6")
        self.setBrush(QBrush(base.darker(160)))
        self.setPen(QPen(base, 1))
        self.setZValue(5)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setPos(clip.time * PX_PER_SEC, y + 4)
        label = QGraphicsTextItem(os.path.basename(clip.path), self)
        label.setDefaultTextColor(QColor("#e6e6e6"))
        label.setFont(QFont("Segoe UI", 8))
        label.setPos(6, 2)
        label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        r = self.rect()
        painter.save()
        painter.setClipRect(r)
        if self.clip.kind == "audio" and self.clip.waveform:
            painter.setPen(QPen(QColor("#d5ffe8")))
            mid = r.center().y()
            n = len(self.clip.waveform)
            for i, v in enumerate(self.clip.waveform):
                x = r.left() + (i / max(1, n - 1)) * r.width()
                amp = v * (r.height() / 2 - 6)
                painter.drawLine(QPointF(x, mid - amp), QPointF(x, mid + amp))
        elif self.clip.kind == "video" and self.clip.thumbnail \
                and os.path.exists(self.clip.thumbnail):
            pm = QPixmap(self.clip.thumbnail)
            if not pm.isNull():
                scaled = pm.scaledToHeight(int(r.height() - 18),
                                           Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(int(r.left() + 4), int(r.top() + 16), scaled)
        painter.restore()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            step = PX_PER_SEC * SNAP_SEC
            return QPointF(max(0.0, round(value.x() / step) * step),
                           self._row_y + 4)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.clip.time = self.pos().x() / PX_PER_SEC
        return super().itemChange(change, value)


class TimelineView(QGraphicsView):
    def __init__(self, timeline: TimelineModel, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.zoom = 1.0
        self._playhead = None
        self.scene_ = QGraphicsScene(self)
        self.setScene(self.scene_)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#14161a")))
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAcceptDrops(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setSceneRect(0, 0, MAX_SECONDS * PX_PER_SEC, TOTAL_H + 40)
        self.refresh()

    def refresh(self):
        self.scene_.clear()
        self._playhead = None
        self._draw_ruler()
        self._draw_tracks()
        for ev in self.timeline.events:
            self.scene_.addItem(PictoItem(ev, self))
        for c in self.timeline.media:
            self.scene_.addItem(MediaItem(c, self))
        self._ensure_playhead()

    def _draw_ruler(self):
        pen = QPen(QColor("#2a2d33")); pen.setWidth(1)
        font = QFont("Segoe UI", 8)
        for s in range(MAX_SECONDS + 1):
            x = s * PX_PER_SEC
            major = (s % 5 == 0)
            self.scene_.addLine(x, 0, x, RULER_H if major else RULER_H // 2, pen)
            if major:
                t = self.scene_.addText(f"{s}s", font)
                t.setDefaultTextColor(QColor("#9aa2ad"))
                t.setPos(x + 3, 2)

    def _draw_tracks(self):
        pen = QPen(QColor("#20232a")); pen.setWidth(1)
        w = self.sceneRect().width()
        for y in (RULER_H, Y_GOLD, Y_AUDIO, Y_VIDEO, Y_VIDEO + VIDEO_H):
            self.scene_.addLine(0, y, w, y, pen)
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        for text, y in [("PICTO", Y_PICTO), ("GOLD", Y_GOLD),
                        ("AUDIO", Y_AUDIO), ("VIDEO", Y_VIDEO)]:
            t = self.scene_.addText(text, font)
            t.setDefaultTextColor(QColor("#5a616c"))
            t.setPos(4, y + 4)
        grid = QPen(QColor("#1a1c22")); grid.setWidth(1)
        for s in range(0, MAX_SECONDS + 1):
            x = s * PX_PER_SEC
            self.scene_.addLine(x, RULER_H, x, Y_VIDEO + VIDEO_H, grid)

    def _ensure_playhead(self):
        if self._playhead is None:
            self._playhead = QGraphicsLineItem(0, 0, 0, TOTAL_H)
            self._playhead.setPen(QPen(QColor("#ff3366"), 2))
            self._playhead.setZValue(1000)
            self.scene_.addItem(self._playhead)

    def set_playhead(self, seconds: float):
        self._ensure_playhead()
        seconds = max(0.0, min(float(seconds), MAX_SECONDS))
        x = seconds * PX_PER_SEC
        self._playhead.setLine(x, 0, x, TOTAL_H)
        visible = self.mapToScene(self.viewport().rect()).boundingRect()
        if x < visible.left() or x > visible.right() - 60:
            self.centerOn(x, visible.center().y())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton \
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            pos = self.mapToScene(event.pos())
            t = max(0.0, pos.x() / PX_PER_SEC)
            gold = Y_GOLD - 4 < pos.y() < Y_AUDIO
            self.timeline.add_picto(t, 0.5, "picto/default.png.ckd", gold=gold)
            self.refresh()
            return
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, 1.0)
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            for item in list(self.scene_.selectedItems()):
                if isinstance(item, PictoItem):
                    self.timeline.remove_picto(item.ev)
                elif isinstance(item, MediaItem):
                    self.timeline.remove_media(item.clip)
            self.refresh()
            event.accept()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            super().dropEvent(event)
            return
        pos = self.mapToScene(event.position().toPoint())
        drop_time = max(0.0, min(pos.x() / PX_PER_SEC, MAX_SECONDS))
        errors = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path or not os.path.isfile(path):
                continue
            err = self._import_file(path, drop_time)
            if err:
                errors.append(f"{os.path.basename(path)}: {err}")
        event.acceptProposedAction()
        self.refresh()
        if errors:
            QMessageBox.warning(self, tr("warning"), "\n".join(errors))

    def _import_file(self, path: str, t: float) -> Optional[str]:
        ext = os.path.splitext(path)[1].lower()
        if path.endswith(".png.ckd"):
            self.timeline.add_picto(t, 0.5, path); return None
        if ext in VIDEO_EXT:
            dur, thumb, err = load_video_info(path)
            self.timeline.add_media(path, "video", time=t,
                                    duration=dur or 5.0, thumbnail=thumb)
            return err
        if ext in AUDIO_EXT:
            dur, wave, err = load_audio_info(path)
            self.timeline.add_media(path, "audio", time=t,
                                    duration=dur or 5.0, waveform=wave)
            return err
        if ext in PICTO_EXT:
            self.timeline.add_picto(t, 0.5, path); return None
        return "неизвестный формат — пропущен"


class TimelineEditor(QWidget):
    """Панель: кнопки операций + плеер + сам таймлайн."""

    def __init__(self, timeline: TimelineModel, main_window=None, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.main_window = main_window

        self._playing_clip: Optional[MediaClip] = None
        self._pending_play = False
        self._external_proc: Optional[subprocess.Popen] = None
        self._ffplay_stderr: List[str] = []
        self._elapsed = QElapsedTimer()
        self._playhead_timer = QTimer(self)
        self._playhead_timer.setInterval(50)
        self._playhead_timer.timeout.connect(self._tick_playhead)

        # Qt player
        if HAVE_QT_MEDIA:
            self.player = QMediaPlayer(self)
            self.audio_out = QAudioOutput(self)
            self.audio_out.setVolume(1.0)
            self.player.setAudioOutput(self.audio_out)
            self.player.positionChanged.connect(self._on_position)
            self.player.mediaStatusChanged.connect(self._on_media_status)
            self.player.errorOccurred.connect(self._on_player_error)
        else:
            self.player = None
            self.audio_out = None

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        # ---- Ряд 1: добавление элементов ----
        h1 = QHBoxLayout()
        b = QPushButton(tr("add_picto")); b.clicked.connect(self._add_picto)
        h1.addWidget(b)
        b = QPushButton(tr("add_gold")); b.clicked.connect(self._add_gold)
        h1.addWidget(b)
        b = QPushButton(tr("add_audio")); b.clicked.connect(self._add_audio)
        h1.addWidget(b)
        b = QPushButton(tr("add_video")); b.clicked.connect(self._add_video)
        h1.addWidget(b)
        h1.addStretch(1)
        hint = QLabel(tr("hint"))
        hint.setStyleSheet("color: #6a6f78;")
        h1.addWidget(hint)
        h1.addWidget(QLabel(tr("zoom")))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 400); self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(140)
        self.zoom_slider.valueChanged.connect(self._set_zoom)
        h1.addWidget(self.zoom_slider)
        v.addLayout(h1)

        # ---- Ряд 2: плеер ----
        h2 = QHBoxLayout()
        self.btn_play = QPushButton(tr("play")); self.btn_play.clicked.connect(self._play_selected)
        h2.addWidget(self.btn_play)
        self.btn_pause = QPushButton(tr("pause")); self.btn_pause.clicked.connect(self._pause)
        h2.addWidget(self.btn_pause)
        self.btn_stop = QPushButton(tr("stop")); self.btn_stop.clicked.connect(self._stop)
        h2.addWidget(self.btn_stop)
        self.btn_test = QPushButton(tr("test")); self.btn_test.clicked.connect(self._test_sound)
        h2.addWidget(self.btn_test)
        self.btn_diag = QPushButton(tr("diag")); self.btn_diag.clicked.connect(self._diag_ffmpeg)
        h2.addWidget(self.btn_diag)
        h2.addSpacing(12)
        h2.addWidget(QLabel(tr("time")))
        self.time_label = QLabel("00:00.000")
        self.time_label.setStyleSheet("font-family: Consolas, monospace; font-size: 12px; color: #9ad1ff;")
        h2.addWidget(self.time_label)
        h2.addStretch(1)
        h2.addWidget(QLabel("🔊"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100); self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self._set_volume)
        h2.addWidget(self.volume_slider)
        v.addLayout(h2)

        # ---- Ряд 3: статус ----
        h3 = QHBoxLayout()
        h3.addWidget(QLabel(tr("status")))
        self.status_label = QLabel("—")
        self.status_label.setStyleSheet("color: #9aa2ad;")
        h3.addWidget(self.status_label)
        h3.addStretch(1)
        backend = "ffplay + Qt" if (FFPLAY_PATH and HAVE_QT_MEDIA) else (
            "ffplay" if FFPLAY_PATH else ("Qt" if HAVE_QT_MEDIA else "winsound (WAV)"))
        self.backend_label = QLabel(f"{tr('backend')} {backend}")
        self.backend_label.setStyleSheet("color: #7a828c; font-size: 11px;")
        h3.addWidget(self.backend_label)
        v.addLayout(h3)

        self.view = TimelineView(self.timeline)
        v.addWidget(self.view, 1)

    # --- добавления ---
    def _add_picto(self):
        self.timeline.add_picto(0.0, 0.5, "picto/default.png.ckd")
        self.refresh(); self._notify_events()

    def _add_gold(self):
        self.timeline.add_picto(0.0, 1.0, "picto/gold.png.ckd", gold=True)
        self.refresh(); self._notify_events()

    def _add_audio(self):
        files, _ = QFileDialog.getOpenFileNames(self, tr("add_audio"), "",
            "Audio (*.wav *.ogg *.oga *.opus *.mp3 *.flac *.m4a *.aac)")
        if not files: return
        errs = []
        for path in files:
            dur, wave, err = load_audio_info(path)
            self.timeline.add_media(path, "audio", 0.0, dur or 5.0, wave)
            if err: errs.append(f"{os.path.basename(path)}: {err}")
        self.refresh(); self._notify_events()
        if errs: QMessageBox.warning(self, tr("warning"), "\n".join(errs))

    def _add_video(self):
        files, _ = QFileDialog.getOpenFileNames(self, tr("add_video"), "",
            "Video (*.webm *.mp4 *.mov *.mkv *.avi *.m4v)")
        if not files: return
        errs = []
        for path in files:
            dur, thumb, err = load_video_info(path)
            self.timeline.add_media(path, "video", 0.0, dur or 5.0, None, thumb)
            if err: errs.append(f"{os.path.basename(path)}: {err}")
        self.refresh(); self._notify_events()
        if errs: QMessageBox.warning(self, tr("warning"), "\n".join(errs))

    def _set_zoom(self, value: int):
        target = value / 100.0
        factor = target / self.view.zoom
        self.view.scale(factor, 1.0)
        self.view.zoom = target

    def _notify_events(self):
        if self.main_window:
            self.main_window.refresh_events()

    # --- плеер ---
    def _pick_clip(self) -> Optional[MediaClip]:
        for item in self.view.scene_.selectedItems():
            if isinstance(item, MediaItem):
                return item.clip
        audio = [m for m in self.timeline.media if m.kind == "audio"]
        if audio: return audio[-1]
        if self.timeline.media: return self.timeline.media[-1]
        return None

    def _play_selected(self):
        clip = self._pick_clip()
        if not clip:
            QMessageBox.information(self, tr("information"), tr("no_media_clip"))
            return
        abs_path = os.path.abspath(clip.path)
        if not os.path.isfile(abs_path):
            QMessageBox.warning(self, tr("warning"), tr("file_not_found", abs_path))
            return
        ext = os.path.splitext(abs_path)[1].lower()

        if ext in VIDEO_EXT and not has_audio_stream(abs_path):
            QMessageBox.information(self, tr("information"),
                f"Файл «{os.path.basename(abs_path)}» не содержит аудиодорожки.")
            return

        if ext in WMF_UNSUPPORTED and FFPLAY_PATH:
            if self._play_ffplay(abs_path, clip): return
        if HAVE_QT_MEDIA and self._play_qt(abs_path, clip): return
        if ext == ".wav" and self._play_winsound(abs_path, clip): return
        if FFPLAY_PATH and self._play_ffplay(abs_path, clip): return
        QMessageBox.warning(self, tr("warning"),
            "Ни один бэкенд не смог воспроизвести файл.\n"
            f"Формат: {ext}\nУстановите ffmpeg (ffplay.exe в PATH).")

    def _play_qt(self, abs_path, clip) -> bool:
        try:
            self._kill_external()
            url = QUrl.fromLocalFile(abs_path)
            self._playing_clip = clip
            self._pending_play = True
            self.player.stop()
            self.player.setSource(url)
            self.status_label.setText(f"Qt: loading {os.path.basename(abs_path)}…")
            QTimer.singleShot(2500, self._qt_timeout)
            return True
        except Exception as e:
            print("[player] Qt failed:", e); return False

    def _qt_timeout(self):
        if not self._pending_play: return
        self._pending_play = False
        clip = self._playing_clip
        if not clip: return
        ext = os.path.splitext(clip.path)[1].lower()
        if FFPLAY_PATH and self._play_ffplay(os.path.abspath(clip.path), clip): return
        if ext == ".wav" and self._play_winsound(os.path.abspath(clip.path), clip): return
        self.status_label.setText("❌ Qt не смог загрузить файл.")

    def _play_ffplay(self, abs_path, clip) -> bool:
        if not FFPLAY_PATH: return False
        try:
            self._kill_external()
            if HAVE_QT_MEDIA and self.player:
                try: self.player.stop()
                except Exception: pass
            env = os.environ.copy()
            env.setdefault("SDL_AUDIODRIVER", "directsound")
            cmd = [FFPLAY_PATH, "-nodisp", "-autoexit", "-vn",
                   "-hide_banner", "-loglevel", "warning", abs_path]
            self._external_proc = subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, startupinfo=_hidden_startupinfo(), env=env,
            )
            self._ffplay_stderr = []
            threading.Thread(target=self._read_stderr,
                             args=(self._external_proc, self._ffplay_stderr),
                             daemon=True).start()
            self._playing_clip = clip
            self._elapsed.start()
            self._playhead_timer.start()
            self.status_label.setText(f"ffplay: {os.path.basename(abs_path)}")
            QTimer.singleShot(900, self._check_ffplay_alive)
            return True
        except Exception as e:
            print("[player] ffplay failed:", e); return False

    def _read_stderr(self, proc, buf):
        try:
            for raw in iter(proc.stderr.readline, b""):
                t = raw.decode("utf-8", "replace").rstrip()
                if t:
                    buf.append(t)
                    print("[ffplay]", t)
        except Exception:
            pass

    def _check_ffplay_alive(self):
        if self._external_proc is None: return
        rc = self._external_proc.poll()
        if rc is None: return
        tail = " | ".join(self._ffplay_stderr[-3:]) if self._ffplay_stderr else ""
        if rc == 0 and not tail:
            self.status_label.setText("Done"); return
        self.status_label.setText(f"❌ ffplay rc={rc}: {tail[:160] or 'нет вывода'}")
        clip = self._playing_clip
        if clip and os.path.splitext(clip.path)[1].lower() == ".wav":
            self._play_winsound(os.path.abspath(clip.path), clip)

    def _tick_playhead(self):
        if self._external_proc is None: return
        if self._external_proc.poll() is not None:
            self._playhead_timer.stop(); return
        if self._playing_clip is None: return
        t = self._playing_clip.time + self._elapsed.elapsed() / 1000.0
        if t >= self._playing_clip.time + self._playing_clip.duration:
            self._playhead_timer.stop(); return
        self.view.set_playhead(t)
        self.time_label.setText(_fmt_time(t))

    def _kill_external(self):
        if self._external_proc:
            try:
                if self._external_proc.poll() is None:
                    self._external_proc.terminate()
            except Exception: pass
            self._external_proc = None
        self._playhead_timer.stop()

    def _play_winsound(self, abs_path, clip) -> bool:
        if os.name != "nt": return False
        try:
            import winsound
            self._kill_external()
            if HAVE_QT_MEDIA and self.player:
                try: self.player.stop()
                except Exception: pass
            winsound.PlaySound(abs_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            self._playing_clip = clip
            self._elapsed.start(); self._playhead_timer.start()
            self.status_label.setText(f"winsound: {os.path.basename(abs_path)}")
            return True
        except Exception as e:
            print("[player] winsound failed:", e); return False

    def _pause(self):
        if HAVE_QT_MEDIA and self.player and \
                self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause(); return
        self._stop()

    def _stop(self):
        if HAVE_QT_MEDIA and self.player:
            try: self.player.stop()
            except Exception: pass
        if os.name == "nt":
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception: pass
        self._kill_external()
        self._playing_clip = None
        self._pending_play = False
        self.view.set_playhead(0.0)
        self.time_label.setText("00:00.000")
        self.status_label.setText("Stopped")

    def _set_volume(self, v: int):
        if self.audio_out: self.audio_out.setVolume(v / 100.0)

    def _test_sound(self):
        try:
            import winsound
            winsound.Beep(880, 300)
            self.status_label.setText("🔔 winsound.Beep OK")
        except Exception as e:
            QApplication.beep()
            self.status_label.setText(f"🔔 QApplication.beep() ({e})")

    def _diag_ffmpeg(self):
        lines = [
            f"ffplay : {FFPLAY_PATH or '❌ не найден'}",
            f"ffprobe: {FFPROBE_PATH or '❌ не найден'}",
            f"ffmpeg : {FFMPEG_PATH or '❌ не найден'}",
            "",
        ]
        if not FFPLAY_PATH:
            lines += ["Установите ffmpeg: https://www.gyan.dev/ffmpeg/builds/",
                      "Добавьте C:\\ffmpeg\\bin в PATH и перезапустите."]
        else:
            try:
                r = subprocess.run([FFPLAY_PATH, "-version"],
                                   capture_output=True, text=True, timeout=5,
                                   startupinfo=_hidden_startupinfo())
                src = r.stdout or r.stderr or ""
                lines.append("ffplay -version: " + (src.splitlines()[0] if src.splitlines() else "?"))
            except Exception as e:
                lines.append(f"ffplay: ошибка {e}")
        text = "\n".join(lines)
        print("=== ffmpeg diagnostics ===\n" + text)
        QMessageBox.information(self, "FFmpeg diagnostics", text)

    def _on_media_status(self, status):
        if not HAVE_QT_MEDIA: return
        if self._pending_play and status in (
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
            QMediaPlayer.MediaStatus.BufferingMedia,
        ):
            self._pending_play = False
            self.player.play()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._qt_timeout()

    def _on_position(self, ms: int):
        t = (self._playing_clip.time if self._playing_clip else 0.0) + ms / 1000.0
        self.view.set_playhead(t)
        self.time_label.setText(_fmt_time(t))

    def _on_player_error(self, error, error_string):
        print("[player] Qt error:", error, error_string)
        self._qt_timeout()

    def closeEvent(self, event):
        self._kill_external()
        if HAVE_QT_MEDIA and self.player:
            try: self.player.stop()
            except Exception: pass
        super().closeEvent(event)

    def refresh(self):
        self.view.refresh()


# ===========================================================================
#  12.  ДИАЛОГИ
# ===========================================================================
class SongDescDialog(QDialog):
    def __init__(self, sd: SongDesc, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("songdesc"))
        self.setMinimumWidth(480)
        self.sd = sd

        form = QFormLayout(self)
        self.e_title = QLineEdit(sd.title)
        self.e_artist = QLineEdit(sd.artist)
        self.e_bpm = QSpinBox(); self.e_bpm.setRange(1, 999); self.e_bpm.setValue(sd.bpm)
        self.e_dur = QLineEdit(str(sd.duration))
        self.e_scene = QLineEdit(sd.main_scene)
        self.e_coach = QSpinBox(); self.e_coach.setRange(1, 4); self.e_coach.setValue(sd.coach_count)
        self.e_diff = QSpinBox(); self.e_diff.setRange(1, 3); self.e_diff.setValue(sd.difficulty)
        self.e_lyrics = QPlainTextEdit(sd.lyrics); self.e_lyrics.setFixedHeight(80)

        # Теги
        tag_box = QGroupBox(tr("tags"))
        tg = QHBoxLayout(tag_box)
        self.tag_checks = {}
        for tag in DANCE_TAGS:
            cb = QCheckBox(tr(tag))
            cb.setChecked(tag in sd.tags)
            self.tag_checks[tag] = cb
            tg.addWidget(cb)

        form.addRow(tr("title"), self.e_title)
        form.addRow(tr("artist"), self.e_artist)
        form.addRow(tr("bpm"), self.e_bpm)
        form.addRow(tr("duration"), self.e_dur)
        form.addRow(tr("main_scene"), self.e_scene)
        form.addRow("Coaches", self.e_coach)
        form.addRow("Difficulty", self.e_diff)
        form.addRow(tag_box)
        form.addRow("Lyrics", self.e_lyrics)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _apply(self):
        self.sd.title = self.e_title.text()
        self.sd.artist = self.e_artist.text()
        self.sd.bpm = self.e_bpm.value()
        try: self.sd.duration = float(self.e_dur.text())
        except ValueError: pass
        self.sd.main_scene = self.e_scene.text()
        self.sd.coach_count = self.e_coach.value()
        self.sd.difficulty = self.e_diff.value()
        self.sd.lyrics = self.e_lyrics.toPlainText()
        self.sd.tags = [t for t, cb in self.tag_checks.items() if cb.isChecked()]
        self.accept()


class ActorDialog(QDialog):
    def __init__(self, af: ActorFile, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("actor"))
        self.setMinimumWidth(480)
        self.af = af

        form = QFormLayout(self)
        self.e_name = QLineEdit(af.name)
        self.e_skel = QLineEdit(af.skeleton)
        self.e_anims = QPlainTextEdit("\n".join(af.animations)); self.e_anims.setFixedHeight(80)
        self.e_mats = QPlainTextEdit("\n".join(af.materials)); self.e_mats.setFixedHeight(80)

        form.addRow(tr("actor_name"), self.e_name)
        form.addRow(tr("skeleton"), self.e_skel)
        form.addRow("Animations", self.e_anims)
        form.addRow("Materials", self.e_mats)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _apply(self):
        self.af.name = self.e_name.text()
        self.af.skeleton = self.e_skel.text()
        self.af.animations = [l.strip() for l in self.e_anims.toPlainText().splitlines() if l.strip()]
        self.af.materials = [l.strip() for l in self.e_mats.toPlainText().splitlines() if l.strip()]
        self.accept()


# ===========================================================================
#  13.  ГЛАВНОЕ ОКНО
# ===========================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.resize(1400, 900)

        self.timeline = TimelineModel()
        self.songdesc = SongDesc()
        self.actor = ActorFile()
        self.song_dir: Optional[str] = None

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(self._build_top_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_timeline_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 1100])
        layout.addWidget(splitter, 1)

        self.setCentralWidget(central)

        self._build_actions()
        self._build_menubar()
        self._build_toolbar()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(tr("ready"))

        self._build_events_dock()

    # ---------------- UI ----------------
    def _build_top_bar(self):
        bar = QFrame()
        bar.setStyleSheet("QFrame { background: #1f2228; border-radius: 10px; }")
        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 8, 12, 8)
        title = QLabel("🎮  JD2017 Tool")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffffff;")
        h.addWidget(title)
        h.addStretch(1)
        h.addWidget(QLabel("🌐"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ru", "en"])
        self.lang_combo.setCurrentText(_current_lang)
        self.lang_combo.currentTextChanged.connect(self._on_lang_change)
        h.addWidget(self.lang_combo)
        return bar

    def _build_left_panel(self):
        panel = QWidget()
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        # Теги
        self.tag_group = QGroupBox(tr("tags"))
        tg = QVBoxLayout(self.tag_group)
        self.tag_checks = {}
        for tag in DANCE_TAGS:
            cb = QCheckBox(tr(tag))
            cb.stateChanged.connect(lambda _, t=tag: self.toggle_tag(t))
            self.tag_checks[tag] = cb
            tg.addWidget(cb)
        v.addWidget(self.tag_group)

        # Инструменты
        self.tools_group = QGroupBox(tr("tools"))
        ag = QVBoxLayout(self.tools_group)

        for label, cb in [
            ("🖌  " + tr("picto"), self.open_picto_editor),
            ("⭐  Gold Move",      self.add_gold_move),
            ("🕺  " + tr("actor"), self.edit_actor),
            ("📝  " + tr("songdesc"), self.edit_songdesc),
            ("📦  " + tr("songdata"), self.save_songdata),
            ("🖼  " + tr("menuart"), self.create_menuart),
            ("🔗  " + tr("graph"), self.create_graph),
            ("➡️  " + tr("convert_ps4"), self.convert_ps4),
            ("🎼  " + tr("u2u"), self.run_unity2ubiart),
        ]:
            b = QPushButton(label)
            b.clicked.connect(cb)
            ag.addWidget(b)

        v.addWidget(self.tools_group)
        v.addStretch(1)
        return panel

    def _build_timeline_panel(self):
        wrapper = QWidget()
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(0, 0, 0, 0)
        self.timeline_editor = TimelineEditor(self.timeline, main_window=self)
        v.addWidget(self.timeline_editor, 1)
        return wrapper

    def _build_actions(self):
        self.act_open = QAction("📂  " + tr("open"), self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self.open_project)

        self.act_save = QAction("💾  " + tr("save"), self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.triggered.connect(self.save_project)

        self.act_save_as = QAction(tr("save_as"), self)
        self.act_save_as.triggered.connect(self.save_project_as)

        self.act_pack_ipk = QAction("📦  " + tr("ipk_pack"), self)
        self.act_pack_ipk.triggered.connect(self.pack_ipk)

        self.act_unpack_ipk = QAction("📂  " + tr("ipk_unpack"), self)
        self.act_unpack_ipk.triggered.connect(self.unpack_ipk)

        self.act_ps4 = QAction("➡️  " + tr("convert_ps4"), self)
        self.act_ps4.triggered.connect(self.convert_ps4)

        self.act_quit = QAction("🚪  " + tr("exit"), self)
        self.act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.act_quit.triggered.connect(self.close)

    def _build_menubar(self):
        mb = self.menuBar()

        fm = mb.addMenu(tr("file"))
        fm.addAction(self.act_open)
        fm.addAction(self.act_save)
        fm.addAction(self.act_save_as)
        fm.addSeparator()
        fm.addAction(self.act_pack_ipk)
        fm.addAction(self.act_unpack_ipk)
        fm.addSeparator()
        fm.addAction(self.act_ps4)
        fm.addSeparator()
        fm.addAction(self.act_quit)

        em = mb.addMenu(tr("edit"))
        em.addAction(tr("songdesc"), self.edit_songdesc)
        em.addAction(tr("songdata"), self.save_songdata)
        em.addAction(tr("actor"), self.edit_actor)

        tm = mb.addMenu("Tools")
        tm.addAction(tr("picto"), self.open_picto_editor)
        tm.addAction(tr("menuart"), self.create_menuart)
        tm.addAction(tr("graph"), self.create_graph)
        tm.addAction(tr("u2u"), self.run_unity2ubiart)

        lm = mb.addMenu(tr("language"))
        lm.addAction("Русский", lambda: self.lang_combo.setCurrentText("ru"))
        lm.addAction("English", lambda: self.lang_combo.setCurrentText("en"))

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)
        tb.addAction(self.act_open)
        tb.addAction(self.act_save)
        tb.addSeparator()
        tb.addAction(self.act_pack_ipk)
        tb.addAction(self.act_unpack_ipk)
        tb.addSeparator()
        tb.addAction(self.act_ps4)

    def _build_events_dock(self):
        dock = QDockWidget(tr("event_list"), self)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.events_list = QListWidget()
        dock.setWidget(self.events_list)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    # ---------------- Язык ----------------
    def _on_lang_change(self, lang: str):
        set_lang(lang)
        self.setWindowTitle(tr("app_title"))
        # упрощённый «live update» — просто сообщение
        self.statusBar().showMessage(
            "Язык переключён. Часть подписей обновится при следующем открытии окна."
            if lang == "ru" else
            "Language switched. Some labels will refresh on next window open."
        )

    # ---------------- Проект ----------------
    def open_project(self):
        d = QFileDialog.getExistingDirectory(self, tr("project_dir_select"))
        if not d:
            return
        self.song_dir = d
        # пытаемся подхватить songdesc
        for name in ("songdesc.isc.ckd", "songdesc.isc"):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                try:
                    self.songdesc = SongDesc.load(p)
                except Exception as e:
                    print("[open] songdesc:", e)
        # dtape
        for name in ("song.dtape.ckd",):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                try:
                    self.timeline = _load_dtape(p)
                    self.timeline_editor.timeline = self.timeline
                    self.timeline_editor.view.timeline = self.timeline
                    self.timeline_editor.refresh()
                except Exception as e:
                    print("[open] dtape:", e)
        # actor
        p = os.path.join(d, "actor.act.ckd")
        if os.path.isfile(p):
            try:
                self.actor = ActorFile.load(p)
            except Exception as e:
                print("[open] actor:", e)
        # теги
        for tag in DANCE_TAGS:
            if tag in self.tag_checks:
                self.tag_checks[tag].setChecked(tag in self.songdesc.tags)
        self.refresh_events()
        self.statusBar().showMessage(tr("project_loaded", d))

    def save_project(self):
        if not self.song_dir:
            return self.save_project_as()
        self._write_project(self.song_dir)
        self.statusBar().showMessage(tr("project_saved", self.song_dir))

    def save_project_as(self):
        d = QFileDialog.getExistingDirectory(self, tr("project_dir_select"))
        if not d:
            return
        self.song_dir = d
        self._write_project(d)
        self.statusBar().showMessage(tr("project_saved", d))

    def _write_project(self, out_dir: str):
        os.makedirs(out_dir, exist_ok=True)

        # dtape
        self.timeline.export_dtape_pc(os.path.join(out_dir, "song.dtape.ckd"))
        # songdesc
        self.songdesc.tags = [t for t, cb in self.tag_checks.items() if cb.isChecked()]
        self.songdesc.save_pc(os.path.join(out_dir, "songdesc.isc.ckd"))
        # songdata
        sd = self.songdesc.to_dict()
        sd["__class"] = "SongData"
        sd["Platform"] = "PC"
        with open(os.path.join(out_dir, "songdata.json"), "w", encoding="utf-8") as f:
            json.dump(sd, f, indent=2, ensure_ascii=False)
        # actor
        self.actor.save(os.path.join(out_dir, "actor.act.ckd"))
        # menuart
        mb = MenuArtBuilder(self.songdesc.title or "song")
        mb.create_isc(os.path.join(out_dir, "menuart.isc.ckd"))
        mb.create_act(os.path.join(out_dir, "menuart.act.ckd"))
        mb.create_graph(os.path.join(out_dir, "graph.isc.ckd"))

        # копируем медиа и пиктограммы
        media_dir = os.path.join(out_dir, "media")
        os.makedirs(media_dir, exist_ok=True)
        for i, m in enumerate(self.timeline.media):
            if os.path.isfile(m.path):
                dst = os.path.join(media_dir, f"{i:03d}_{os.path.basename(m.path)}")
                try: shutil.copy2(m.path, dst)
                except Exception: pass

    # ---------------- IPK ----------------
    def pack_ipk(self):
        d = QFileDialog.getExistingDirectory(self, tr("input_dir"))
        if not d: return
        out, _ = QFileDialog.getSaveFileName(self, tr("ipk_pack"), "", "IPK (*.ipk)")
        if not out: return
        try:
            n = IPKArchive.pack(d, out)
            QMessageBox.information(self, tr("information"), tr("ipk_packed", out))
            self.statusBar().showMessage(f"IPK: {n} files → {out}")
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    def unpack_ipk(self):
        f, _ = QFileDialog.getOpenFileName(self, tr("ipk_unpack"), "", "IPK (*.ipk)")
        if not f: return
        d = QFileDialog.getExistingDirectory(self, tr("output_dir"))
        if not d: return
        try:
            n = IPKArchive.unpack(f, d)
            QMessageBox.information(self, tr("information"), tr("ipk_unpacked", d))
            self.statusBar().showMessage(f"IPK: {n} files extracted")
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    # ---------------- PS4 ----------------
    def convert_ps4(self):
        d = QFileDialog.getExistingDirectory(self, tr("input_dir"))
        if not d: return
        out = QFileDialog.getExistingDirectory(self, tr("output_dir"))
        if not out: return
        try:
            conv = PCtoPS4Converter(d)
            log = conv.convert_all(out)
            QMessageBox.information(self, tr("information"),
                                    tr("ps4_converted", out) + "\n\n" + log)
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    # ---------------- SongDesc / SongData / Actor ----------------
    def edit_songdesc(self):
        dlg = SongDescDialog(self.songdesc, self)
        if dlg.exec():
            for tag in DANCE_TAGS:
                if tag in self.tag_checks:
                    self.tag_checks[tag].setChecked(tag in self.songdesc.tags)
            self.statusBar().showMessage("SongDesc updated")

    def save_songdata(self):
        if not self.song_dir:
            self.song_dir = QFileDialog.getExistingDirectory(self, tr("output_dir"))
            if not self.song_dir: return
        sd = self.songdesc.to_dict()
        sd["__class"] = "SongData"
        sd["Platform"] = "PC"
        p = os.path.join(self.song_dir, "songdata.json")
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(sd, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, tr("information"), tr("songdata_saved", p))
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    def edit_actor(self):
        dlg = ActorDialog(self.actor, self)
        if dlg.exec():
            self.statusBar().showMessage("Actor updated")

    # ---------------- MenuArt / Graph ----------------
    def create_menuart(self):
        d = QFileDialog.getExistingDirectory(self, tr("output_dir"))
        if not d: return
        try:
            mb = MenuArtBuilder(self.songdesc.title or "song")
            mb.create_isc(os.path.join(d, "menuart.isc.ckd"))
            mb.create_act(os.path.join(d, "menuart.act.ckd"))
            mb.create_graph(os.path.join(d, "graph.isc.ckd"))

            # опционально — TGA
            png, _ = QFileDialog.getOpenFileName(self, "Menu icon (PNG) — опционально",
                                                 "", "PNG (*.png);;All (*)")
            if png:
                mb.create_tga(os.path.join(d, "menuart.tga.ckd"), png)

            QMessageBox.information(self, tr("information"), tr("menuart_done", d))
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    def create_graph(self):
        d = QFileDialog.getExistingDirectory(self, tr("output_dir"))
        if not d: return
        try:
            mb = MenuArtBuilder(self.songdesc.title or "song")
            p = os.path.join(d, "graph.isc.ckd")
            mb.create_graph(p)
            QMessageBox.information(self, tr("information"), tr("graph_done", p))
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    # ---------------- Unity2UbiArt ----------------
    def run_unity2ubiart(self):
        u = Unity2UbiArt()
        if not u.asset_studio:
            QMessageBox.warning(self, "Unity2UbiArt", u.help_text())
            return
        bundle, _ = QFileDialog.getOpenFileName(self, "Select .bundle", "",
            "Unity Bundle (*.bundle *.unity3d *.assets);;All (*)")
        if not bundle: return
        out = QFileDialog.getExistingDirectory(self, tr("output_dir"))
        if not out: return

        map_name = os.path.splitext(os.path.basename(bundle))[0]

        def on_progress(msg):
            self.statusBar().showMessage(msg)
            print("[u2u]", msg)

        try:
            result = u.convert(bundle, map_name, out, on_progress=on_progress)
            QMessageBox.information(self, tr("information"),
                                    tr("u2u_done", result))
        except Exception as e:
            QMessageBox.critical(self, "Unity2UbiArt", str(e))

    # ---------------- Теги ----------------
    def toggle_tag(self, tag: str):
        if tag in self.songdesc.tags:
            self.songdesc.tags.remove(tag)
        else:
            self.songdesc.tags.append(tag)
        self.statusBar().showMessage(tr("tags_updated", ", ".join(self.songdesc.tags)))

    # ---------------- Пиктограммы ----------------
    def open_picto_editor(self):
        PictoEditor(self).exec()

    def add_gold_move(self):
        self.timeline.add_picto(0.0, 1.0, "picto/gold.png.ckd", gold=True)
        self.timeline_editor.refresh()
        self.refresh_events()

    # ---------------- Events ----------------
    def refresh_events(self):
        self.events_list.clear()
        for ev in self.timeline.events:
            mark = "⭐" if ev.is_gold_move else "🎵"
            self.events_list.addItem(
                QListWidgetItem(f"{mark}  {ev.time:.2f}s  —  {ev.picto_path}"))
        for m in self.timeline.media:
            mark = "🎧" if m.kind == "audio" else "🎬"
            self.events_list.addItem(
                QListWidgetItem(f"{mark}  {m.time:.2f}s  —  {os.path.basename(m.path)}"))


# ===========================================================================
#  14.  ТОЧКА ВХОДА
# ===========================================================================
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    app.setApplicationName("JD2017 Tool")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()