# -*- coding: utf-8 -*-
"""
NOUR - برنامج مواقيت الصلاة والأذان للكمبيوتر
Python 3.10+ / PySide6 / adhanpy

التشغيل:
    pip install PySide6 adhanpy tzdata
    python nour_app.py
"""
from __future__ import annotations

import json
import math
import sys
import unicodedata
from html import escape
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QBoxLayout, QColorDialog, QDialog, QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton, QSlider,
    QScrollArea, QSizePolicy, QSpinBox, QStackedWidget, QSystemTrayIcon, QTableWidget, QTableWidgetItem, QTextBrowser,
    QVBoxLayout, QWidget,
)

NO_EDIT = QAbstractItemView.EditTriggers.NoEditTriggers
STRETCH = QHeaderView.ResizeMode.Stretch

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
    QT_MULTIMEDIA = True
except Exception:
    QT_MULTIMEDIA = False
    QMediaPlayer = None
    QAudioOutput = None

ADHANPY = True
ADHANPY_ERROR = ""
try:
    from adhanpy.PrayerTimes import PrayerTimes
    from adhanpy.calculation.CalculationMethod import CalculationMethod
    from adhanpy.calculation.CalculationParameters import CalculationParameters
    from adhanpy.calculation.Madhab import Madhab
except Exception as exc:  # pragma: no cover
    ADHANPY = False
    ADHANPY_ERROR = str(exc)

# Coordinates moved between adhanpy releases - try every known location.
Coordinates = None
if ADHANPY:
    for _module in ("adhanpy.calculation.Coordinates", "adhanpy.Coordinates",
                    "adhanpy.calculation.coordinates"):
        try:
            Coordinates = __import__(_module, fromlist=["Coordinates"]).Coordinates
            break
        except Exception:
            continue

APP_NAME = "NOUR"
APP_VERSION = "3.0"
if sys.platform == "win32":
    CONFIG_DIR = Path.home() / "AppData" / "Roaming" / "NOUR"
elif sys.platform == "darwin":
    CONFIG_DIR = Path.home() / "Library" / "Application Support" / "NOUR"
else:
    CONFIG_DIR = Path.home() / ".config" / "NOUR"
CONFIG_FILE = CONFIG_DIR / "settings.json"
MUSHAF_CONFIG_FILE = CONFIG_DIR / "mushaf.json"
MUSHAF_DEFAULTS = {
    "font_size": 20, "font_family": "Amiri Quran", "paper": "#F9F3E4",
    "ink": "#24332B", "highlight": "#DFB66C", "line_height": 130,
    "two_page": False, "last_page": 1,
}
MUSHAF_THEMES = {
    "sepia": ("#F9F3E4", "#24332B", "#DFB66C"),
    "white": ("#FFFEF9", "#1B2A24", "#E5C47D"),
    "green": ("#E8F0E6", "#183D32", "#BBD798"),
    "night": ("#172821", "#F2EBD8", "#D8B66A"),
}


def is_frozen():
    """True when running from a compiled executable built with PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def app_dir():
    """Folder that holds the .exe (or the .py). Adhan files are looked up here."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundle_dir():
    """Read-only folder with files embedded inside the executable."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


APP_DIR = app_dir()
ADHAN_CANDIDATES = [
    APP_DIR / "adhan.mp3",
    APP_DIR / "adhan.wav",
    CONFIG_DIR / "adhan.mp3",
    bundle_dir() / "adhan.mp3",
]

COLORS = {
    "bg": "#08120F", "panel": "#122720", "panel2": "#18372D", "line": "#29483B",
    "green": "#214B3B", "gold": "#D8B66A", "gold2": "#F0D99D", "text": "#F5F2E9",
    "muted": "#A9B9B0",
}

APP_THEMES = {
    "dark": {
        "bg": "#08120F", "panel": "#122720", "panel2": "#18372D", "line": "#29483B",
        "green": "#214B3B", "gold": "#D8B66A", "gold2": "#F0D99D", "text": "#F5F2E9", "muted": "#A9B9B0",
        "sidebar1": "#10241D", "sidebar2": "#0A1712", "panel_start": "#16332A", "panel_end": "#122720",
        "active": "#1D4237", "hover": "#2A5C47", "pressed": "#1B4032", "input": "#0E201A",
        "table": "#0F211B", "table_alt": "#142B22", "disabled": "#14281F",
    },
    "light": {
        "bg": "#EEF4EF", "panel": "#FFFFFF", "panel2": "#F7FBF7", "line": "#C4D8C8",
        "green": "#DCEBE0", "gold": "#A47724", "gold2": "#765719", "text": "#20362A", "muted": "#668074",
        "sidebar1": "#E1EEE4", "sidebar2": "#F7FAF5", "panel_start": "#FFFFFF", "panel_end": "#F2F8F3",
        "active": "#D8EBDD", "hover": "#C8E0CF", "pressed": "#B9D3C1", "input": "#F8FCF8",
        "table": "#FFFFFF", "table_alt": "#F1F7F2", "disabled": "#E4ECE6",
    },
    "sepia": {
        "bg": "#241D15", "panel": "#3A2D20", "panel2": "#4A3826", "line": "#705838",
        "green": "#5A4931", "gold": "#D7AD61", "gold2": "#F3D79B", "text": "#F7EBD0", "muted": "#C4AE8B",
        "sidebar1": "#3A2B1D", "sidebar2": "#211910", "panel_start": "#4A3826", "panel_end": "#35281C",
        "active": "#665033", "hover": "#765C3A", "pressed": "#4D3A25", "input": "#2D2116",
        "table": "#332619", "table_alt": "#3D2E20", "disabled": "#3A2D21",
    },
    "night": {
        "bg": "#05070D", "panel": "#0D1423", "panel2": "#121D31", "line": "#263A5A",
        "green": "#1A3150", "gold": "#8FB7E8", "gold2": "#D4E7FF", "text": "#ECF4FF", "muted": "#93A8C2",
        "sidebar1": "#0D1423", "sidebar2": "#050912", "panel_start": "#14223A", "panel_end": "#0D1729",
        "active": "#1D385B", "hover": "#284A73", "pressed": "#17314E", "input": "#0A1220",
        "table": "#0B1422", "table_alt": "#101D30", "disabled": "#172235",
    },
}

def set_app_theme(name):
    name = name if name in APP_THEMES else "dark"
    COLORS.update(APP_THEMES[name])
    return name

# ---------------------------------------------------------------- i18n
# key -> (ar, fr, en)
S = {
    "app": ("نــور", "NOUR", "NOUR"),
    "subtitle": ("مواقيت الصلاة والأذان", "Horaires de prière et adhan", "Prayer times & adhan"),
    "today": ("لوحة اليوم", "Tableau du jour", "Today"),
    "monthly": ("الجدول الشهري", "Tableau mensuel", "Monthly"),
    "education": ("التعليم الإسلامي", "Apprendre la prière", "Learning"),
    "adhkar": ("الأدعية والأذكار", "Invocations et adhkar", "Duas & adhkar"),
    "adhkar_hint": ("أذكار مختارة مع البحث والنسخ والعداد.", "Invocations sélectionnées avec recherche, copie et compteur.", "Selected supplications with search, copy and counter."),
    "adhkar_category": ("التصنيف", "Catégorie", "Category"),
    "adhkar_search": ("ابحث في الأدعية والأذكار…", "Rechercher dans les invocations…", "Search duas and adhkar…"),
    "adhkar_copy": ("نسخ الذكر", "Copier", "Copy"),
    "adhkar_copied": ("تم نسخ الذكر.", "Invocation copiée.", "Invocation copied."),
    "adhkar_counter": ("عداد التكرار", "Compteur", "Repetition counter"),
    "adhkar_reset": ("تصفير العداد", "Réinitialiser", "Reset"),
    "adhkar_times": ("التكرار المقترح", "Répétitions conseillées", "Suggested repetitions"),
    "prayer_log": ("سجل الصلاة اليومي", "Suivi quotidien des prières", "Daily prayer log"),
    "prayer_log_hint": ("ضع علامة بعد أداء كل صلاة، وسيُحفظ السجل على جهازك.", "Cochez chaque prière accomplie; le suivi est enregistré localement.", "Check each completed prayer; the log is saved locally."),
    "prayer_log_done": ("تم حفظ سجل اليوم.", "Suivi du jour enregistré.", "Today's log saved."),
    "prayer_log_progress": ("التقدم اليومي", "Progression du jour", "Today's progress"),
    "repeat_button": ("تكرار الذكر", "Répéter", "Repeat"),
    "repeat_count": ("عدد التكرار", "Nombre de répétitions", "Repetitions"),
    "education_hint": ("تعلم الصلاة والوضوء خطوة بخطوة مع عدد الركعات.", "Apprenez la prière et les ablutions étape par étape.", "Learn prayer and ablution step by step."),
    "prayer_guide": ("طريقة الصلاة وعدد الركعات", "La prière et le nombre de rakaat", "Prayer and rak'ah counts"),
    "wudu_guide": ("طريقة الوضوء", "Comment faire les ablutions", "How to perform wudu"),
    "audio_hint": ("الصوت التعليمي: شغّل الأذان من إعدادات الأذان إن كان الملف متوفرًا.", "Audio : utilisez le fichier d'adhan dans les réglages s'il est disponible.", "Audio: use the adhan file in Adhan settings if available."),
    "education_sound": ("تشغيل صوت تجريبي", "Tester le son", "Test sound"),
    "education_sound_done": ("تم تشغيل الصوت. يمكنك اختيار ملف الأذان من الإعدادات.", "Son lancé. Choisissez un fichier d'adhan dans les réglages.", "Sound played. Choose an adhan file in Settings."),
    "ramadan": ("وضع رمضان", "Mode Ramadan", "Ramadan"),
    "calendar": ("التواريخ الإسلامية", "Dates islamiques", "Islamic dates"),
    "qibla": ("القبلة", "Qibla", "Qibla"),
    "settings": ("الإعدادات", "Paramètres", "Settings"),
    "about": ("حول البرنامج", "À propos", "About"),
    "language": ("اللغة", "Langue", "Language"),
    "location": ("الموقع", "Emplacement", "Location"),
    "country": ("البلد", "Pays", "Country"),
    "city": ("المدينة", "Ville", "City"),
    "wilayas": ("58 ولاية", "58 wilayas", "58 provinces"),
    "next": ("الصلاة القادمة", "Prochaine prière", "Next prayer"),
    "remaining": ("الوقت المتبقي", "Temps restant", "Time remaining"),
    "prayers": ("مواقيت الصلاة", "Horaires de prière", "Prayer times"),
    "fajr": ("الفجر", "Fajr", "Fajr"),
    "sunrise": ("الشروق", "Lever du soleil", "Sunrise"),
    "dhuhr": ("الظهر", "Dhuhr", "Dhuhr"),
    "asr": ("العصر", "Asr", "Asr"),
    "maghrib": ("المغرب", "Maghrib", "Maghrib"),
    "isha": ("العشاء", "Isha", "Isha"),
    "method": ("طريقة الحساب", "Méthode de calcul", "Calculation method"),
    "mwl": ("رابطة العالم الإسلامي", "Ligue islamique mondiale", "Muslim World League"),
    "egypt": ("الهيئة المصرية العامة للمساحة", "Autorité égyptienne", "Egyptian General Authority"),
    "umm": ("أم القرى", "Umm al-Qura", "Umm al-Qura"),
    "karachi": ("جامعة العلوم الإسلامية - كراتشي", "Univ. islamique de Karachi", "Univ. of Islamic Sciences, Karachi"),
    "isna": ("ISNA - أمريكا الشمالية", "ISNA - Amérique du Nord", "ISNA - North America"),
    "moon": ("لجنة رؤية الهلال", "Comité d'observation lunaire", "Moonsighting Committee"),
    "dubai": ("دبي", "Dubaï", "Dubai"),
    "kuwait": ("الكويت", "Koweït", "Kuwait"),
    "qatar": ("قطر", "Qatar", "Qatar"),
    "singapore": ("سنغافورة", "Singapour", "Singapore"),
    "asr_method": ("طريقة حساب العصر", "Calcul de l'Asr", "Asr calculation"),
    "standard": ("شافعي / قياسي", "Standard / Shafi", "Standard / Shafi"),
    "hanafi": ("حنفي", "Hanafite", "Hanafi"),
    "refresh": ("إعادة الحساب", "Recalculer", "Recalculate"),
    "save": ("حفظ الإعدادات", "Enregistrer", "Save settings"),
    "save_ok": ("تم حفظ الإعدادات.", "Paramètres enregistrés.", "Settings saved."),
    "latitude": ("خط العرض", "Latitude", "Latitude"),
    "longitude": ("خط الطول", "Longitude", "Longitude"),
    "timezone": ("المنطقة الزمنية", "Fuseau horaire", "Time zone"),
    "custom_location": ("تعديل الموقع يدويًا", "Emplacement manuel", "Manual location"),
    "manual_note": ("أدخل إحداثيات صحيحة واسم منطقة زمنية IANA مثل Africa/Algiers.",
                    "Coordonnées valides + fuseau IANA, ex. Africa/Algiers.",
                    "Valid coordinates + IANA zone, e.g. Africa/Algiers."),
    "auto_location": ("تحديد موقعي تلقائيًا", "Détecter ma position", "Detect my location"),
    "locating": ("جارٍ التحديد…", "Détection…", "Detecting…"),
    "location_ok": ("تم تحديد الموقع.", "Position détectée.", "Location detected."),
    "location_error": ("تعذر تحديد الموقع.", "Détection impossible.", "Could not detect location."),
    "clock": ("الساعة الآن", "Heure actuelle", "Current time"),
    "no_next": ("لا توجد صلاة قادمة اليوم", "Aucune prière à venir", "No upcoming prayer"),
    "adhan_enable": ("تشغيل الأذان عند حلول الوقت", "Jouer l'adhan à l'heure", "Play adhan on time"),
    "adhan_file": ("ملف الأذان", "Fichier de l'adhan", "Adhan file"),
    "adhan_browse": ("اختيار ملف…", "Parcourir…", "Browse…"),
    "adhan_test": ("تجربة الصوت", "Tester", "Test"),
    "adhan_stop": ("إيقاف", "Arrêter", "Stop"),
    "adhan_volume": ("مستوى الصوت", "Volume", "Volume"),
    "adhan_missing": ("لم يُعثر على ملف الأذان. ضع adhan.mp3 بجانب البرنامج أو اختر مسارًا.",
                      "Fichier d'adhan introuvable. Placez adhan.mp3 à côté de l'app.",
                      "Adhan file not found. Put adhan.mp3 next to the app."),
    "adhan_playing": ("يُشغَّل الأذان…", "Adhan en cours…", "Playing adhan…"),
    "notify_enable": ("إشعار قبل الأذان", "Notification avant l'adhan", "Notify before adhan"),
    "notify_minutes": ("دقائق قبل الأذان", "Minutes avant", "Minutes before"),
    "notify_title": ("تذكير بالصلاة", "Rappel de prière", "Prayer reminder"),
    "notify_now": ("حان الآن وقت صلاة {prayer} يا {name}، لا تدع شيئًا يلهيك.",
                   "C'est l'heure de {prayer}, {name}.",
                   "It is time for {prayer}, {name}."),
    "notify_body": ("اقترب موعد صلاة {prayer} يا {name}، لا تدع شيئًا يلهيك.",
                    "L'heure de {prayer} approche, {name}.",
                    "Prayer time for {prayer} is near, {name}."),
    "hourly_reminder": ("تذكير كل ساعة بالدعاء والذكر", "Rappel horaire de dhikr", "Hourly prayer and dhikr reminder"),
    "hourly_interval": ("تكرار التذكير كل (ساعات)", "Répéter le rappel toutes les (heures)", "Repeat reminder every (hours)"),
    "hourly_test": ("تجربة التذكير الآن", "Tester le rappel maintenant", "Test reminder now"),
    "hourly_title": ("ذكر ودعاء", "Dhikr et invocation", "Dhikr and supplication"),
    "user_name": ("اسمك", "Votre prénom", "Your name"),
    "tune_note": ("أضف أو اطرح دقائق لكل صلاة لمطابقة توقيت المسجد.",
                  "Ajoutez ou retirez des minutes selon votre mosquée.",
                  "Add or subtract minutes to match your mosque."),
    "adjustments": ("ضبط الدقائق", "Ajustement des minutes", "Minute adjustments"),
    "reset": ("استرجاع الافتراضي", "Réinitialiser", "Reset"),
    "hijri_year": ("السنة الهجرية", "Année hégirienne", "Hijri year"),
    "gregorian_year": ("السنة الميلادية", "Année grégorienne", "Gregorian year"),
    "month": ("الشهر", "Mois", "Month"),
    "gregorian_date": ("الميلادي", "Grégorien", "Gregorian"),
    "hijri_date": ("الهجري", "Hégirien", "Hijri"),
    "suhoor": ("الإمساك", "Souhour", "Suhoor"),
    "iftar": ("الإفطار", "Iftar", "Iftar"),
    "ramadan_day": ("رمضان {day}", "Ramadan {day}", "Ramadan {day}"),
    "ramadan_now": ("نحن في شهر رمضان", "Nous sommes en Ramadan", "It is currently Ramadan"),
    "ramadan_not_now": ("لسنا في رمضان حاليًا", "Nous ne sommes pas en Ramadan", "It is not Ramadan"),
    "event": ("المناسبة", "Événement", "Occasion"),
    "islamic_new_year": ("رأس السنة الهجرية", "Nouvel an hégirien", "Islamic New Year"),
    "ashura": ("عاشوراء", "Achoura", "Ashura"),
    "isra_miraj": ("الإسراء والمعراج", "Isra et Mi'raj", "Isra and Mi'raj"),
    "ramadan_start": ("بداية رمضان", "Début du Ramadan", "Start of Ramadan"),
    "laylat_qadr": ("ليلة القدر (تقديريًا)", "Laylat al-Qadr (estimée)", "Laylat al-Qadr (est.)"),
    "eid_fitr": ("عيد الفطر", "Aïd el-Fitr", "Eid al-Fitr"),
    "arafah": ("يوم عرفة", "Jour d'Arafat", "Day of Arafah"),
    "eid_adha": ("عيد الأضحى", "Aïd al-Adha", "Eid al-Adha"),
    "qibla_from_north": ("من الشمال", "du nord", "from north"),
    "distance": ("المسافة إلى الكعبة", "Distance vers la Kaaba", "Distance to the Kaaba"),
    "km": ("كم", "km", "km"),
    "qibla_hint": ("وجّه أعلى البوصلة نحو القبلة (من الشمال الجغرافي).",
                   "Orientez le haut de la boussole vers la Qibla (nord géographique).",
                   "Point the top of the compass toward the Qibla (true north)."),
    "clock_24": ("تنسيق 24 ساعة", "Format 24 h", "24-hour format"),
    "footer": ("تُحسب الأوقات محليًا على هذا الكمبيوتر وقد تختلف قليلًا حسب طريقة الحساب.",
               "Calcul local, les résultats peuvent varier selon la méthode.",
               "Calculated locally; results may vary by calculation method."),
    "about_text": ("نور - برنامج مواقيت الصلاة للأجهزة المكتبية.\nتُحسب المواقيت محليًا باستخدام adhanpy.\nراجع طريقة الحساب مع الجهة المحلية الموثوقة.",
                   "NOUR - horaires de prière pour ordinateur.\nCalculs locaux avec adhanpy.\nVérifiez la méthode auprès d'une autorité locale.",
                   "NOUR - desktop prayer times.\nTimes are computed locally with adhanpy.\nConfirm the method with a trusted local authority."),
    "made_by": ("تمت البرمجة من طرف", "Programmé par", "Programmed by"),
    "good_luck": ("بالتوفيق للجميع", "Bonne chance à tous", "Best of luck to everyone"),
    "close": ("إغلاق", "Fermer", "Close"),
    "exit_program": ("خروج من البرنامج", "Quitter le programme", "Exit program"),
    "quran": ("القرآن الكريم", "Saint Coran", "Holy Quran"),
    "quran_hint": ("114 سورة · استماع مباشر عبر الإنترنت", "114 sourates · écoute en ligne", "114 surahs · online streaming"),
    "quran_reciter": ("القارئ", "Récitateur", "Reciter"),
    "quran_play": ("تشغيل", "Lecture", "Play"),
    "quran_pause": ("إيقاف مؤقت", "Pause", "Pause"),
    "quran_stop": ("إيقاف", "Arrêter", "Stop"),
    "quran_ready": ("اختر سورة وقارئًا واضغط تشغيل", "Choisissez une sourate et un récitateur", "Choose a surah and a reciter"),
    "quran_stream": ("جارٍ تحميل التلاوة من الإنترنت...", "Chargement de la récitation...", "Loading the recitation..."),
    "quran_error": ("تعذّر تشغيل الصوت. تحقق من الإنترنت أو اختر قارئًا آخر.",
                    "Lecture impossible. Vérifiez Internet ou choisissez un autre récitateur.",
                    "Playback failed. Check your connection or try another reciter."),
    "mushaf": ("المصحف الكريم", "Le Mushaf", "The Mushaf"),
    "mushaf_hint": ("604 صفحة · قراءة وبحث دون إنترنت", "604 pages · lecture hors ligne", "604 pages · offline reading"),
    "mushaf_surah": ("اختر السورة", "Choisir la sourate", "Choose surah"),
    "mushaf_page": ("الصفحة", "Page", "Page"),
    "mushaf_prev": ("الصفحات السابقة", "Pages précédentes", "Previous pages"),
    "mushaf_next": ("الصفحات التالية", "Pages suivantes", "Next pages"),
    "mushaf_search": ("ابحث عن كلمة أو جملة أو آية مثل 2:255", "Mot, phrase ou verset (ex. 2:255)", "Word, phrase or verse (e.g. 2:255)"),
    "mushaf_find": ("بحث في القرآن", "Chercher", "Search Quran"),
    "mushaf_results": ("النتائج", "Résultats", "Results"),
    "mushaf_back": ("العودة إلى المصحف", "Retour au Mushaf", "Back to Mushaf"),
    "mushaf_count": ("{count} آية مطابقة", "{count} versets trouvés", "{count} matching verses"),
    "mushaf_no_results": ("لم تُعثر على نتائج. جرّب كلمة أخرى.", "Aucun résultat.", "No results. Try another word."),
    "mushaf_missing": ("ملف المصحف quran-uthmani.json غير موجود. ضعه بجانب nour_app.py أو أعد البناء من الحزمة الكاملة.",
                       "Le fichier quran-uthmani.json manque. Placez-le à côté de nour_app.py.",
                       "Missing quran-uthmani.json. Put it beside nour_app.py or rebuild from the full kit."),
    "mushaf_invalid": ("وُجد ملف quran-uthmani.json لكن تعذرت قراءته. تأكد من أنه JSON كامل وليس صفحة HTML.",
                       "Le fichier quran-uthmani.json est présent mais illisible. Vérifiez son contenu.",
                       "quran-uthmani.json exists but could not be read. Check that it is complete JSON, not HTML."),
    "mushaf_settings": ("إعدادات المصحف", "Réglages du Mushaf", "Mushaf settings"),
    "mushaf_font": ("نوع الخط", "Police", "Font"),
    "mushaf_size": ("حجم الخط", "Taille du texte", "Text size"),
    "mushaf_spacing": ("المسافة بين السطور", "Espacement des lignes", "Line spacing"),
    "mushaf_paper": ("لون الصفحة", "Couleur de la page", "Page color"),
    "mushaf_ink": ("لون الكتابة", "Couleur du texte", "Text color"),
    "mushaf_highlight": ("لون تمييز البحث", "Couleur de surbrillance", "Highlight color"),
    "mushaf_spread": ("عرض صفحتين على الشاشات الواسعة", "Afficher deux pages sur grand écran", "Two pages on wide screens"),
    "mushaf_reset": ("استعادة المظهر الافتراضي", "Restaurer l'apparence", "Restore default appearance"),
    "mushaf_save": ("حفظ وتطبيق", "Enregistrer et appliquer", "Save and apply"),
    "mushaf_theme": ("مظهر الصفحة", "Thème de lecture", "Reading theme"),
    "mushaf_theme_custom": ("ألوان مخصصة", "Couleurs personnalisées", "Custom colors"),
    "mushaf_theme_sepia": ("ورقي دافئ", "Papier chaud", "Warm paper"),
    "mushaf_theme_white": ("أبيض هادئ", "Blanc doux", "Soft white"),
    "mushaf_theme_green": ("أخضر مريح", "Vert doux", "Soft green"),
    "mushaf_theme_night": ("قراءة ليلية", "Lecture nocturne", "Night reading"),
    "install_missing": ("مكتبة الحساب غير مثبتة. أغلق البرنامج ثم:\npip install adhanpy tzdata",
                        "Bibliothèque absente. Fermez puis:\npip install adhanpy tzdata",
                        "Calculation library missing. Close then:\npip install adhanpy tzdata"),
    "tray_msg": ("نور يعمل في الخلفية - الأذان والإشعارات مستمرة.",
                 "NOUR continue en arrière-plan.",
                 "NOUR keeps running in the background."),
    "quit": ("خروج", "Quitter", "Quit"),
    "open_nour": ("فتح نور", "Ouvrir NOUR", "Open NOUR"),
    "calc_error": ("تعذر حساب المواقيت", "Calcul impossible", "Could not calculate"),
    "tz_invalid": ("المنطقة الزمنية غير صالحة. مثال: Africa/Algiers",
                   "Fuseau horaire invalide. Exemple : Africa/Algiers",
                   "Invalid time zone. Example: Africa/Algiers"),
    "apply": ("تطبيق", "Appliquer", "Apply"),
    "hijri_adjust": ("تعديل التاريخ الهجري (بالأيام)", "Ajustement hégirien (jours)", "Hijri date adjustment (days)"),
    "hijri_note": ("التاريخ الهجري محسوب حسابيًا وقد يختلف بيوم عن إعلان الجهة الرسمية. استعمل خيار تعديل التاريخ الهجري في الإعدادات.",
                   "La date hégirienne est calculée arithmétiquement et peut différer d'un jour de l'annonce officielle. Utilisez l'ajustement dans les paramètres.",
                   "The Hijri date is calculated arithmetically and may differ by one day from the official announcement. Use the adjustment in Settings."),
    "sec_calc": ("الحساب والعرض", "Calcul et affichage", "Calculation & display"),
    "theme": ("مظهر التطبيق", "Thème de l'application", "App theme"),
    "theme_dark": ("زمردي داكن", "Émeraude sombre", "Dark emerald"),
    "theme_light": ("فاتح هادئ", "Clair doux", "Soft light"),
    "theme_sepia": ("بني دافئ", "Sépia chaleureux", "Warm sepia"),
    "theme_night": ("ليلي عميق", "Nuit profonde", "Deep night"),
    "sec_adhan": ("الأذان", "Adhan", "Adhan"),
    "sec_notify": ("الإشعارات", "Notifications", "Notifications"),
    "mushaf_limited": ("يُعرض أول {shown} نتيجة فقط. ضيّق البحث لنتائج أدق.",
                       "Seuls les {shown} premiers résultats sont affichés. Affinez la recherche.",
                       "Showing only the first {shown} results. Narrow your search."),
}

HOURLY_REMINDERS = {
    "ar": [
        "سبحان الله وبحمده، سبحان الله العظيم.",
        "اللهم اغفر لي وارحمني واهدني وعافني وارزقني.",
        "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد.",
        "أستغفر الله العظيم وأتوب إليه.",
        "اللهم صل وسلم وبارك على نبينا محمد ﷺ.",
        "اللهم أعنّي على ذكرك وشكرك وحسن عبادتك.",
    ],
    "fr": [
        "Gloire et louange à Allah, Gloire à Allah l'Immense.",
        "Ô Allah, pardonne-moi, fais-moi miséricorde et guide-moi.",
        "Il n'y a de dieu qu'Allah, seul et sans associé.",
        "Je demande pardon à Allah et je me repens à Lui.",
        "Ô Allah, prie et bénis notre Prophète Muhammad ﷺ.",
        "Ô Allah, aide-moi à T'évoquer, Te remercier et bien T'adorer.",
    ],
    "en": [
        "Glory and praise be to Allah, the Most Great.",
        "O Allah, forgive me, have mercy on me, and guide me.",
        "There is no god but Allah, alone, without partner.",
        "I seek Allah's forgiveness and repent to Him.",
        "O Allah, send blessings upon our Prophet Muhammad ﷺ.",
        "O Allah, help me remember You, thank You, and worship You well.",
    ],
}

ADHKAR_DATA = [
    ("أذكار الصباح والمساء", "سُبْحَانَ اللهِ وَبِحَمْدِهِ", "من قالها مئة مرة حُطّت خطاياه وإن كانت مثل زبد البحر.", 100),
    ("أذكار الصباح والمساء", "أَسْتَغْفِرُ اللهَ وَأَتُوبُ إِلَيْهِ", "ذكر للاستغفار والتوبة إلى الله تعالى.", 100),
    ("أذكار الصباح والمساء", "لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ", "من أعظم الأذكار، ويقال صباحًا ومساءً.", 10),
    ("بعد الصلاة", "أَسْتَغْفِرُ اللهَ، أَسْتَغْفِرُ اللهَ، أَسْتَغْفِرُ اللهَ، اللَّهُمَّ أَنْتَ السَّلَامُ وَمِنْكَ السَّلَامُ تَبَارَكْتَ يَا ذَا الْجَلَالِ وَالْإِكْرَامِ", "ذكر يقال بعد السلام من الصلاة.", 1),
    ("بعد الصلاة", "سُبْحَانَ اللهِ 33، وَالْحَمْدُ لِلَّهِ 33، وَاللهُ أَكْبَرُ 33، وَتُتَمُّ الْمِائَةَ بِقَوْلِ: لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ", "التسبيح والتحميد والتكبير بعد الصلاة.", 1),
    ("النوم والاستيقاظ", "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا", "يقال عند النوم.", 1),
    ("النوم والاستيقاظ", "الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ", "يقال عند الاستيقاظ.", 1),
    ("أدعية عامة", "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ", "دعاء جامع من القرآن الكريم.", 1),
    ("أدعية عامة", "اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ", "دعاء للاستعانة على العبادة.", 1),
    ("المسجد", "اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ", "يقال عند دخول المسجد.", 1),
    ("المسجد", "اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ", "يقال عند الخروج من المسجد.", 1),
]

TRAY = None

def tr(lang, key, **vars):
    table = S.get(key)
    raw = table[0] if table else key
    if lang == "fr" and table:
        raw = table[1]
    elif lang == "en" and table:
        raw = table[2]
    for name, value in vars.items():
        raw = raw.replace("{" + name + "}", str(value))
    return raw

# ---------------------------------------------------------------- cities
# key -> (ar, fr, lat, lon)  /  Africa/Algiers
DZ = [
    ("adrar", "أدرار", "Adrar", 27.8742, -0.2939),
    ("chlef", "الشلف", "Chlef", 36.1655, 1.3345),
    ("laghouat", "الأغواط", "Laghouat", 33.8, 2.865),
    ("oum_el_bouaghi", "أم البواقي", "Oum El Bouaghi", 35.875, 7.114),
    ("batna", "باتنة", "Batna", 35.555, 6.174),
    ("bejaia", "بجاية", "Béjaïa", 36.751, 5.084),
    ("biskra", "بسكرة", "Biskra", 34.85, 5.73),
    ("bechar", "بشار", "Béchar", 31.6167, -2.2167),
    ("blida", "البليدة", "Blida", 36.47, 2.83),
    ("bouira", "البويرة", "Bouira", 36.375, 3.9),
    ("tamanrasset", "تمنراست", "Tamanrasset", 22.785, 5.5228),
    ("tebessa", "تبسة", "Tébessa", 35.4, 8.12),
    ("tlemcen", "تلمسان", "Tlemcen", 34.888, -1.315),
    ("tiaret", "تيارت", "Tiaret", 35.37, 1.32),
    ("tizi_ouzou", "تيزي وزو", "Tizi Ouzou", 36.7117, 4.0458),
    ("algiers", "الجزائر العاصمة", "Alger", 36.7538, 3.0588),
    ("djelfa", "الجلفة", "Djelfa", 34.67, 3.25),
    ("jijel", "جيجل", "Jijel", 36.82, 5.77),
    ("setif", "سطيف", "Sétif", 36.19, 5.41),
    ("saida", "سعيدة", "Saïda", 34.83, 0.15),
    ("skikda", "سكيكدة", "Skikda", 36.8667, 6.9),
    ("sidi_bel_abbes", "سيدي بلعباس", "Sidi Bel Abbès", 35.2, -0.63),
    ("annaba", "عنابة", "Annaba", 36.9, 7.77),
    ("guelma", "قالمة", "Guelma", 36.46, 7.43),
    ("constantine", "قسنطينة", "Constantine", 36.365, 6.6147),
    ("medea", "المدية", "Médéa", 36.2675, 2.75),
    ("mostaganem", "مستغانم", "Mostaganem", 35.94, 0.09),
    ("msila", "المسيلة", "M'Sila", 35.7, 4.54),
    ("mascara", "معسكر", "Mascara", 35.4, 0.14),
    ("ouargla", "ورقلة", "Ouargla", 31.95, 5.33),
    ("oran", "وهران", "Oran", 35.6971, -0.6308),
    ("el_bayadh", "البيض", "El Bayadh", 33.68, 1.02),
    ("illizi", "إليزي", "Illizi", 26.5, 8.48),
    ("bordj", "برج بوعريريج", "Bordj Bou Arréridj", 36.07, 4.76),
    ("boumerdes", "بومرداس", "Boumerdès", 36.76, 3.47),
    ("el_tarf", "الطارف", "El Tarf", 36.77, 8.31),
    ("tindouf", "تندوف", "Tindouf", 27.67, -8.14),
    ("tissemsilt", "تيسمسيلت", "Tissemsilt", 35.61, 1.81),
    ("el_oued", "الوادي", "El Oued", 33.37, 6.87),
    ("khenchela", "خنشلة", "Khenchela", 35.43, 7.14),
    ("souk_ahras", "سوق أهراس", "Souk Ahras", 36.29, 7.95),
    ("tipaza", "تيبازة", "Tipaza", 36.59, 2.45),
    ("mila", "ميلة", "Mila", 36.45, 6.26),
    ("ain_defla", "عين الدفلى", "Aïn Defla", 36.26, 1.97),
    ("naama", "النعامة", "Naâma", 33.27, -0.31),
    ("ain_temouchent", "عين تموشنت", "Aïn Témouchent", 35.3, -1.14),
    ("ghardaia", "غرداية", "Ghardaïa", 32.49, 3.67),
    ("relizane", "غليزان", "Relizane", 35.74, 0.56),
    ("timimoun", "تيميمون", "Timimoun", 29.26, 0.23),
    ("bjmokhtar", "برج باجي مختار", "Bordj Badji Mokhtar", 21.33, 0.95),
    ("ouled_djellal", "أولاد جلال", "Ouled Djellal", 34.43, 5.07),
    ("beni_abbes", "بني عباس", "Béni Abbès", 30.13, -2.17),
    ("in_salah", "عين صالح", "In Salah", 27.19, 2.47),
    ("in_guezzam", "عين قزام", "In Guezzam", 19.57, 5.77),
    ("touggourt", "تقرت", "Touggourt", 33.1, 6.06),
    ("djanet", "جانت", "Djanet", 24.55, 9.48),
    ("el_mghair", "المغير", "El M'Ghair", 33.95, 5.92),
    ("el_menia", "المنيعة", "El Meniaa", 30.58, 2.88),
]

COUNTRIES = {
    "algeria": ("الجزائر", "Algérie", "Algeria", "Africa/Algiers", DZ),
    "france": ("فرنسا", "France", "France", "Europe/Paris", [
        ("paris", "باريس", "Paris", 48.8566, 2.3522),
        ("marseille", "مرسيليا", "Marseille", 43.2965, 5.3698),
        ("lyon", "ليون", "Lyon", 45.764, 4.8357),
        ("strasbourg", "ستراسبورغ", "Strasbourg", 48.5734, 7.7521),
    ]),
    "uk": ("المملكة المتحدة", "Royaume-Uni", "United Kingdom", "Europe/London", [
        ("london", "لندن", "London", 51.5072, -0.1276),
        ("birmingham", "برمنغهام", "Birmingham", 52.4862, -1.8904),
        ("manchester", "مانشستر", "Manchester", 53.4808, -2.2426),
    ]),
    "saudi": ("السعودية", "Arabie saoudite", "Saudi Arabia", "Asia/Riyadh", [
        ("mecca", "مكة المكرمة", "La Mecque", 21.3891, 39.8579),
        ("medina", "المدينة المنورة", "Médine", 24.5247, 39.5692),
        ("riyadh", "الرياض", "Riyad", 24.7136, 46.6753),
        ("jeddah", "جدة", "Djeddah", 21.4858, 39.1925),
    ]),
    "other": ("دول أخرى", "Autres pays", "Other countries", "UTC", [
        ("cairo", "القاهرة", "Le Caire", 30.0444, 31.2357),
        ("tunis", "تونس", "Tunis", 36.8065, 10.1815),
        ("rabat", "الرباط", "Rabat", 34.0209, -6.8416),
        ("dubai", "دبي", "Dubaï", 25.2048, 55.2708),
        ("istanbul", "إسطنبول", "Istanbul", 41.0082, 28.9784),
        ("new_york", "نيويورك", "New York", 40.7128, -74.006),
    ]),
}

# Time zone per city when it differs from the country default.
CITY_TZ = {
    "cairo": "Africa/Cairo", "tunis": "Africa/Tunis", "rabat": "Africa/Casablanca",
    "dubai": "Asia/Dubai", "istanbul": "Europe/Istanbul", "new_york": "America/New_York",
}

METHODS = [
    ("MUSLIM_WORLD_LEAGUE", "mwl"),
    ("EGYPTIAN", "egypt"),
    ("UMM_AL_QURA", "umm"),
    ("KARACHI", "karachi"),
    ("NORTH_AMERICA", "isna"),
    ("MOON_SIGHTING_COMMITTEE", "moon"),
    ("DUBAI", "dubai"),
    ("KUWAIT", "kuwait"),
    ("QATAR", "qatar"),
    ("SINGAPORE", "singapore"),
]

PRAYER_KEYS = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]
ADHAN_KEYS = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

# All three editions below have 114 full-surah files at 128 kbps on the CDN.
QURAN_RECITERS = [
    ("مشاري راشد العفاسي", "ar.alafasy"),
    ("عبد الباسط عبد الصمد", "ar.abdulbasitmurattal"),
    ("محمد صديق المنشاوي", "ar.muhammadsiddiqalminshawimujawwad"),
]
# Bundled chapter names keep the list usable without a network connection.
QURAN_SURAHS = ['ٱلْفَاتِحَةِ', 'البَقَرَةِ', 'آلِ عِمۡرَانَ', 'النِّسَاءِ', 'المَائـِدَةِ', 'الأَنۡعَامِ', 'الأَعۡرَافِ', 'الأَنفَالِ', 'التَّوۡبَةِ', 'يُونُسَ', 'هُودٍ', 'يُوسُفَ', 'الرَّعۡدِ', 'إِبۡرَاهِيمَ', 'الحِجۡرِ', 'النَّحۡلِ', 'الإِسۡرَاءِ', 'الكَهۡفِ', 'مَرۡيَمَ', 'طه', 'الأَنبِيَاءِ', 'الحَجِّ', 'المُؤۡمِنُونَ', 'النُّورِ', 'الفُرۡقَانِ', 'الشُّعَرَاءِ', 'النَّمۡلِ', 'القَصَصِ', 'العَنكَبُوتِ', 'الرُّومِ', 'لُقۡمَانَ', 'السَّجۡدَةِ', 'الأَحۡزَابِ', 'سَبَإٍ', 'فَاطِرٍ', 'يسٓ', 'الصَّافَّاتِ', 'صٓ', 'الزُّمَرِ', 'غَافِرٍ', 'فُصِّلَتۡ', 'الشُّورَىٰ', 'الزُّخۡرُفِ', 'الدُّخَانِ', 'الجَاثِيَةِ', 'الأَحۡقَافِ', 'مُحَمَّدٍ', 'الفَتۡحِ', 'الحُجُرَاتِ', 'قٓ', 'الذَّارِيَاتِ', 'الطُّورِ', 'النَّجۡمِ', 'القَمَرِ', 'الرَّحۡمَٰن', 'الوَاقِعَةِ', 'الحَدِيدِ', 'المُجَادلَةِ', 'الحَشۡرِ', 'المُمۡتَحنَةِ', 'الصَّفِّ', 'الجُمُعَةِ', 'المُنَافِقُونَ', 'التَّغَابُنِ', 'الطَّلَاقِ', 'التَّحۡرِيمِ', 'المُلۡكِ', 'القَلَمِ', 'الحَاقَّةِ', 'المَعَارِجِ', 'نُوحٍ', 'الجِنِّ', 'المُزَّمِّلِ', 'المُدَّثِّرِ', 'القِيَامَةِ', 'الإِنسَانِ', 'المُرۡسَلَاتِ', 'النَّبَإِ', 'النَّازِعَاتِ', 'عَبَسَ', 'التَّكۡوِيرِ', 'الانفِطَارِ', 'المُطَفِّفِينَ', 'الانشِقَاقِ', 'البُرُوجِ', 'الطَّارِقِ', 'الأَعۡلَىٰ', 'الغَاشِيَةِ', 'الفَجۡرِ', 'البَلَدِ', 'الشَّمۡسِ', 'اللَّيۡلِ', 'الضُّحَىٰ', 'الشَّرۡحِ', 'التِّينِ', 'العَلَقِ', 'القَدۡرِ', 'البَيِّنَةِ', 'الزَّلۡزَلَةِ', 'العَادِيَاتِ', 'القَارِعَةِ', 'التَّكَاثُرِ', 'العَصۡرِ', 'الهُمَزَةِ', 'الفِيلِ', 'قُرَيۡشٍ', 'المَاعُونِ', 'الكَوۡثَرِ', 'الكَافِرُونَ', 'النَّصۡرِ', 'المَسَدِ', 'الإِخۡلَاصِ', 'الفَلَقِ', 'النَّاسِ']

EVENTS = [(1, 1, "islamic_new_year"), (10, 1, "ashura"), (27, 7, "isra_miraj"),
          (1, 9, "ramadan_start"), (27, 9, "laylat_qadr"), (1, 10, "eid_fitr"),
          (9, 12, "arafah"), (10, 12, "eid_adha")]

HIJRI_MONTHS = {
    "ar": ["محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"],
    "fr": ["Mouharram", "Safar", "Rabi al-awwal", "Rabi al-thani", "Joumada al-oula", "Joumada al-thania", "Rajab", "Chaabane", "Ramadan", "Chawwal", "Dhou al-Qida", "Dhou al-Hijja"],
    "en": ["Muharram", "Safar", "Rabi I", "Rabi II", "Jumada I", "Jumada II", "Rajab", "Shaban", "Ramadan", "Shawwal", "Dhu al-Qidah", "Dhu al-Hijjah"],
}

KAABA = (21.422487, 39.826206)
MUSHAF_MAX_RESULTS = 300


def quran_normalize_with_positions(text):
    """Remove Quranic diacritics while retaining offsets into the original text."""
    letters, positions = [], []
    equivalents = str.maketrans({"ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})
    for offset, char in enumerate(text):
        if unicodedata.combining(char) or char in ("ـ", "\ufeff"):
            continue
        letters.append(char.translate(equivalents))
        positions.append(offset)
    return "".join(letters), positions


def quran_highlight(text, query, whole=False, highlight="#DFB66C"):
    """Highlight every matching word/phrase without changing the verse text."""
    if whole:
        return "<span style='background-color:%s;color:#183327'>%s</span>" % (highlight, escape(text))
    needle, _ = quran_normalize_with_positions(query.strip())
    haystack, positions = quran_normalize_with_positions(text)
    if not needle:
        return escape(text)
    result, start, cursor = [], 0, 0
    while True:
        match = haystack.find(needle, cursor)
        if match < 0:
            break
        first = positions[match]
        last = positions[match + len(needle) - 1] + 1
        result.append(escape(text[start:first]))
        result.append("<span style='background-color:%s;color:#203428'>%s</span>" % (highlight, escape(text[first:last])))
        start = last
        cursor = match + len(needle)
    result.append(escape(text[start:]))
    return "".join(result)

# English spellings that differ from the French ones stored in the tables.
EN_CITY = {
    "algiers": "Algiers", "mecca": "Makkah", "medina": "Madinah", "cairo": "Cairo",
    "london": "London", "riyadh": "Riyadh", "jeddah": "Jeddah", "bejaia": "Bejaia",
    "setif": "Setif", "constantine": "Constantine", "tlemcen": "Tlemcen",
    "batna": "Batna", "annaba": "Annaba", "oran": "Oran", "blida": "Blida",
}


# ---------------------------------------------------------------- helpers
def gregorian_to_hijri(y, m, d):
    if m < 3:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524
    l = jd - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    hm = (24 * l) // 709
    hd = l - (709 * hm) // 24
    return 30 * n + j - 30, hm, hd


def hijri_to_gregorian(hy, hm, hd):
    jd = ((11 * hy + 3) // 30) + 354 * hy + 30 * hm - ((hm - 1) // 2) + hd + 1948440 - 385
    l = jd + 68569
    n = (4 * l) // 146097
    l = l - (146097 * n + 3) // 4
    y = (4000 * (l + 1)) // 1461001
    l = l - (1461 * y) // 4 + 31
    m = (80 * l) // 2447
    d = l - (2447 * m) // 80
    l = m // 11
    m = m + 2 - 12 * l
    return date(100 * (n - 49) + y + l, m, d)


def format_hijri(hy, hm, hd, lang):
    months = HIJRI_MONTHS.get(lang, HIJRI_MONTHS["en"])
    return "%d %s %d" % (hd, months[max(0, min(11, hm - 1))], hy)


def qibla_bearing(lat, lon):
    lat1, lon1 = math.radians(lat), math.radians(lon)
    lat2, lon2 = math.radians(KAABA[0]), math.radians(KAABA[1])
    dlon = lon2 - lon1
    x = math.sin(dlon)
    y = math.cos(lat1) * math.tan(lat2) - math.sin(lat1) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def distance_km(lat, lon):
    rlat1, rlat2 = math.radians(lat), math.radians(KAABA[0])
    dlat = rlat2 - rlat1
    dlon = math.radians(KAABA[1] - lon)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return int(6371 * 2 * math.asin(math.sqrt(a)))


def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(data):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        temp = CONFIG_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(CONFIG_FILE)
    except (OSError, TypeError, ValueError) as exc:
        print("config save failed:", exc)


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_ms(milliseconds):
    seconds = max(0, int(milliseconds // 1000))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return "%d:%02d:%02d" % (hours, minutes, secs)
    return "%d:%02d" % (minutes, secs)


def valid_zone(name):
    name = (name or "").strip()
    if not name:
        return False
    try:
        ZoneInfo(name)
        return True
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return False


def load_mushaf_settings():
    settings = dict(MUSHAF_DEFAULTS)
    try:
        saved = json.loads(MUSHAF_CONFIG_FILE.read_text(encoding="utf-8-sig"))
        for key in settings:
            if key in saved:
                settings[key] = saved[key]
    except (OSError, ValueError, TypeError):
        pass
    for key, low, high in (("font_size", 12, 38), ("line_height", 100, 220), ("last_page", 1, 604)):
        try:
            settings[key] = max(low, min(high, int(settings[key])))
        except (ValueError, TypeError):
            settings[key] = MUSHAF_DEFAULTS[key]
    settings["two_page"] = bool(settings["two_page"])
    if settings["font_family"] not in ("Amiri Quran", "Traditional Arabic", "Noto Naskh Arabic"):
        settings["font_family"] = "Amiri Quran"
    for name in ("paper", "ink", "highlight"):
        color = QColor(str(settings[name]))
        settings[name] = color.name() if color.isValid() else MUSHAF_DEFAULTS[name]
    return settings


def save_mushaf_settings(settings):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        MUSHAF_CONFIG_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        print("mushaf settings save failed:", exc)


def tray_info_icon():
    """QSystemTrayIcon.MessageIcon.Information (old builds expose the short name)."""
    icon = getattr(QSystemTrayIcon, "Information", None)
    if icon is None:
        icon = QSystemTrayIcon.MessageIcon.Information
    return icon


def tray_click_reasons():
    trigger = getattr(QSystemTrayIcon, "Trigger", None)
    double = getattr(QSystemTrayIcon, "DoubleClick", None)
    if trigger is None:
        trigger = QSystemTrayIcon.ActivationReason.Trigger
    if double is None:
        double = QSystemTrayIcon.ActivationReason.DoubleClick
    return (trigger, double)


# ---------------------------------------------------------------- widgets
class Compass(QWidget):
    """Qibla compass drawn in a 300x300 design space and scaled to the widget."""

    def __init__(self, size=None):
        super().__init__()
        self.bearing = 0.0
        if size:
            self.setFixedSize(size, size)
        else:
            self.setMinimumSize(220, 220)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_bearing(self, value):
        self.bearing = value % 360.0
        self.update()

    def paintEvent(self, event):
        side = min(self.width(), self.height())
        if side <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.width() / 2.0, self.height() / 2.0)
        factor = side / 300.0
        p.scale(factor, factor)
        r = 142.0
        centre = QPointF(0.0, 0.0)
        no_pen = Qt.PenStyle.NoPen

        # Soft golden halo around the dial
        for radius, alpha in ((r, 22), (r - 5, 44)):
            glow = QColor(COLORS["gold"])
            glow.setAlpha(alpha)
            p.setPen(no_pen)
            p.setBrush(glow)
            p.drawEllipse(centre, radius, radius)

        # Layered dial
        p.setPen(QColor("#3E6B58"))
        p.setBrush(QColor("#0D1D17"))
        p.drawEllipse(centre, r - 7, r - 7)
        p.setPen(no_pen)
        p.setBrush(QColor("#122720"))
        p.drawEllipse(centre, r - 12, r - 12)
        p.setPen(QColor("#22453A"))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(centre, r - 21, r - 21)

        # Tick marks
        for deg in range(0, 360, 5):
            major = deg % 45 == 0
            mid = deg % 15 == 0
            length = 11 if major else (6 if mid else 3)
            rad = math.radians(deg - 90)
            outer = r - 9
            pen = QPen(QColor(COLORS["gold"]) if major else QColor("#5C7A6D"))
            pen.setWidthF(2.0 if major else 1.0)
            p.setPen(pen)
            p.drawLine(QLineF(outer * math.cos(rad), outer * math.sin(rad),
                              (outer - length) * math.cos(rad), (outer - length) * math.sin(rad)))

        # Cardinal letters
        font = QFont("Segoe UI")
        font.setPixelSize(18)
        font.setBold(True)
        p.setFont(font)
        for label, deg in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
            rad = math.radians(deg - 90)
            x = (r - 36) * math.cos(rad)
            y = (r - 36) * math.sin(rad)
            p.setPen(QColor(COLORS["gold2"]) if label == "N" else QColor(COLORS["muted"]))
            p.drawText(QRectF(x - 14, y - 14, 28, 28), Qt.AlignmentFlag.AlignCenter, label)

        # Qibla needle (golden kite) + Kaaba glyph at the tip
        p.save()
        p.rotate(self.bearing)
        tip = r - 26
        p.setPen(QColor("#8A6A2E"))
        p.setBrush(QColor(COLORS["gold"]))
        p.drawPolygon(QPolygonF([QPointF(0, -tip), QPointF(-10, 6), QPointF(0, -2), QPointF(10, 6)]))
        p.setPen(no_pen)
        p.setBrush(QColor("#356052"))
        p.drawPolygon(QPolygonF([QPointF(0, tip - 30), QPointF(-7, -4), QPointF(0, 0), QPointF(7, -4)]))
        ky = -tip + 16
        p.setPen(QColor(COLORS["gold"]))
        p.setBrush(QColor("#0B1714"))
        p.drawRect(QRectF(-13, ky, 26, 20))
        p.setPen(no_pen)
        p.setBrush(QColor(COLORS["gold"]))
        p.drawRect(QRectF(-13, ky + 7, 26, 4))
        p.restore()

        # Center jewel
        p.setPen(QColor("#8A6A2E"))
        p.setBrush(QColor(COLORS["gold2"]))
        p.drawEllipse(centre, 6, 6)
        p.setPen(no_pen)
        p.setBrush(QColor("#0B1714"))
        p.drawEllipse(centre, 2, 2)
        p.end()


class LocationWorker(QThread):
    """Looks up the approximate position by IP without freezing the window."""
    result_ready = Signal(object, str)

    def run(self):
        try:
            import urllib.request
            request = urllib.request.Request(
                "https://ipwho.is/",
                headers={"User-Agent": "Mozilla/5.0 (NOUR)", "Accept": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=7) as response:
                data = json.loads(response.read().decode("utf-8"))
            if data.get("success") is False:
                raise ValueError(str(data.get("message", "lookup failed")))
            float(data["latitude"])
            float(data["longitude"])
            self.result_ready.emit(data, "")
        except Exception as exc:
            self.result_ready.emit(None, str(exc))


def style_sheet(rtl=True):
    c = COLORS
    return """
    QMainWindow, QWidget { background: %(bg)s; color: %(text)s; font-family: 'Segoe UI', 'Noto Sans Arabic', 'Tahoma'; font-size: 14px; }
    QLabel { background: transparent; }
    QCheckBox, QSlider { background: transparent; }
    QScrollArea { background: transparent; border: none; }
    QScrollArea > QWidget > QWidget { background: transparent; }
    QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
    QScrollBar::handle:vertical { background: %(line)s; border-radius: 4px; min-height: 28px; }
    QScrollBar::handle:vertical:hover { background: %(gold)s; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
    QStatusBar { background: transparent; color: %(muted)s; font-size: 12px; }
    QStatusBar::item { border: none; }
    QFrame#Sidebar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 %(sidebar1)s, stop:1 %(sidebar2)s);
                     border: 1px solid %(line)s; border-radius: 20px; }
    QFrame#Panel { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 %(panel_start)s, stop:1 %(panel_end)s);
                   border: 1px solid %(line)s; border-radius: 20px; }
    QFrame#Card { background: %(panel2)s; border: 1px solid %(line)s; border-radius: 14px; }
    QFrame#Card[active="true"] { background: %(active)s; border: 2px solid %(gold)s; }
    QLabel#CardValue { color: %(text)s; font-size: 22px; font-weight: 700; }
    QLabel#CardValue[active="true"] { color: %(gold2)s; }
    QLabel#Brand { color: %(gold2)s; font-size: 28px; font-weight: 800; }
    QLabel#Sub { color: %(muted)s; font-size: 11px; }
    QLabel#Title { color: %(gold2)s; font-size: 20px; font-weight: 700; }
    QLabel#Section { color: %(gold)s; font-size: 15px; font-weight: 700; padding-top: 10px; padding-bottom: 4px;
                     border-bottom: 1px solid %(line)s; }
    QLabel#Muted { color: %(muted)s; font-size: 12px; }
    QLabel#Big { color: %(gold2)s; font-size: 34px; font-weight: 800; }
    QLabel#Count { color: %(gold)s; font-size: 28px; font-weight: 700; }
    QLabel#CreditName { color: %(gold2)s; font-size: 27px; font-weight: 800; }
    QLabel#CreditLine { color: %(text)s; font-size: 15px; }
    QLabel#CreditLink { color: %(gold)s; font-size: 14px; font-weight: 600; }
    QPushButton { background: %(green)s; color: %(text)s; border: 1px solid %(line)s;
                  border-radius: 11px; padding: 10px 16px; text-align: %(align)s; font-size: 14px; }
    QPushButton#Nav { padding: 8px 14px; }
    QPushButton:hover { background: %(hover)s; border-color: %(gold)s; }
    QPushButton:pressed { background: %(pressed)s; }
    QPushButton:disabled { color: %(muted)s; background: %(disabled)s; }
    QPushButton:checked { background: %(gold)s; color: #14231C; font-weight: 700; border-color: %(gold2)s; }
    QPushButton#Primary { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 %(gold2)s, stop:1 %(gold)s);
                          color: #14231C; font-weight: 700; font-size: 15px; border: none; }
    QPushButton#Primary:hover { background: %(gold2)s; }
    QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit {
        background: %(input)s; border: 1px solid %(line)s; border-radius: 9px; padding: 7px; color: %(text)s;
        selection-background-color: %(gold)s; selection-color: #14231C; }
    QComboBox:hover, QDoubleSpinBox:hover, QSpinBox:hover, QLineEdit:hover { border-color: %(gold)s; }
    QComboBox:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled, QLineEdit:disabled { color: #6F8277; background: #0B1814; }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView { background: %(panel)s; border: 1px solid %(line)s; selection-background-color: %(green)s; }
    QTableWidget { background: %(table)s; alternate-background-color: %(table_alt)s; border: 1px solid %(line)s;
                   border-radius: 14px; gridline-color: #23453A; }
    QTableWidget::item { padding: 5px; }
    QHeaderView::section { background: %(panel2)s; color: %(gold2)s; border: none; border-bottom: 1px solid %(line)s;
                           padding: 8px; font-weight: 700; }
    QCheckBox { spacing: 9px; }
    QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 1px solid %(line)s; background: %(input)s; }
    QCheckBox::indicator:hover { border-color: %(gold)s; }
    QCheckBox::indicator:checked { background: %(gold)s; border-color: %(gold)s; }
    QSlider::groove:horizontal { height: 7px; background: %(line)s; border-radius: 4px; }
    QSlider::sub-page:horizontal { background: %(gold)s; border-radius: 4px; }
    QSlider::handle:horizontal { background: %(gold2)s; width: 18px; margin: -7px 0; border-radius: 9px; }
    QDialog { background: %(bg)s; }
    """ % {"bg": c["bg"], "panel": c["panel"], "panel2": c["panel2"], "line": c["line"],
           "green": c["green"], "gold": c["gold"], "gold2": c["gold2"], "text": c["text"],
           "muted": c["muted"], "sidebar1": c["sidebar1"], "sidebar2": c["sidebar2"],
           "panel_start": c["panel_start"], "panel_end": c["panel_end"], "active": c["active"],
           "hover": c["hover"], "pressed": c["pressed"], "input": c["input"],
           "table": c["table"], "table_alt": c["table_alt"], "disabled": c["disabled"],
           "align": "right" if rtl else "left"}


# ---------------------------------------------------------------- main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.app_theme = set_app_theme(self.cfg.get("theme", "dark"))
        self.lang = self.cfg.get("language", "ar")
        if self.lang not in ("ar", "fr", "en"):
            self.lang = "ar"
        self.country = self.cfg.get("country", "algeria")
        if self.country not in COUNTRIES:
            self.country = "algeria"
        self.city = self.cfg.get("city", "constantine")
        self.manual = bool(self.cfg.get("manual", False))
        self.lat = _as_float(self.cfg.get("lat", 36.365), 36.365)
        self.lon = _as_float(self.cfg.get("lon", 6.6147), 6.6147)
        self.tz_name = self.cfg.get("tz", "Africa/Algiers")
        self.method = self.cfg.get("method", "MUSLIM_WORLD_LEAGUE")
        self.madhab_hanafi = bool(self.cfg.get("hanafi", False))
        self.adhan_enabled = bool(self.cfg.get("adhan_enabled", True))
        self.adhan_path = self.cfg.get("adhan_path", "")
        self.volume = max(0, min(100, _as_int(self.cfg.get("volume", 100), 100)))
        self.notify_enabled = bool(self.cfg.get("notify_enabled", True))
        self.notify_minutes = max(1, min(60, _as_int(self.cfg.get("notify_minutes", 10), 10)))
        self.hourly_enabled = bool(self.cfg.get("hourly_enabled", True))
        self.hourly_interval = max(1, min(12, _as_int(self.cfg.get("hourly_interval", 1), 1)))
        self.last_hourly = None
        self.user_name = self.cfg.get("user_name", "")
        self.prayer_log = self.cfg.get("prayer_log", {})
        if not isinstance(self.prayer_log, dict):
            self.prayer_log = {}
        self.hour12 = bool(self.cfg.get("hour12", False))
        saved_tune = self.cfg.get("tune", {})
        if not isinstance(saved_tune, dict):
            saved_tune = {}
        self.tune = {key: _as_int(saved_tune.get(key, 0), 0) for key in PRAYER_KEYS}
        self.hijri_adjust = max(-2, min(2, _as_int(self.cfg.get("hijri_adjust", 0), 0)))
        self.quran_surah_idx = max(0, min(113, _as_int(self.cfg.get("quran_surah", 0), 0)))
        self.quran_reciter_idx = max(0, min(len(QURAN_RECITERS) - 1, _as_int(self.cfg.get("quran_reciter", 0), 0)))
        self.calc_date = None
        self._calc_failed = False
        self.row_labels = {}
        self.section_labels = {}
        self._mushaf_norm = None
        self.loc_worker = None
        self._quran_duration = 0
        self._quran_position = 0
        self.card_cols = 3
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(350)
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.mushaf_settings = load_mushaf_settings()
        self.mushaf_surahs = []
        self.mushaf_verses = []
        self.mushaf_pages = {}
        self.mushaf_by_reference = {}
        self.mushaf_error = "mushaf_missing"
        self.load_mushaf_data()

        self.times = {}
        self.target = None
        self.target_key = None
        self.last_adhan = None
        self.last_notify = None
        self.tz = self.zone()

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(self.make_icon())
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        self.resize(min(1180, available.width() - 30) if available else 1180,
                    min(820, available.height() - 30) if available else 820)
        self.setMinimumSize(750, 560)
        self.setStyleSheet(style_sheet(rtl=self.lang == "ar"))
        self.player = None
        self.audio_out = None
        if QT_MULTIMEDIA:
            try:
                self.player = QMediaPlayer(self)
                self.audio_out = QAudioOutput(self)
                self.player.setAudioOutput(self.audio_out)
                self.audio_out.setVolume(max(0.0, min(1.0, self.volume / 100.0)))
            except Exception as exc:
                print("audio init failed:", exc)
                self.player = None

        self.quran_player = None
        self.quran_audio = None
        if QT_MULTIMEDIA:
            try:
                self.quran_player = QMediaPlayer(self)
                self.quran_audio = QAudioOutput(self)
                self.quran_player.setAudioOutput(self.quran_audio)
                self.quran_audio.setVolume(0.85)
            except Exception as exc:
                print("quran audio init failed:", exc)
                self.quran_player = None

        self.build_ui()
        self.relayout_cards()
        self.apply_language()
        self.recalculate()
        self.init_tray()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    # ---------------- ui
    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(232)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 18, 16, 16)
        side.setSpacing(8)
        self.brand = QLabel("☾  " + tr(self.lang, "app"))
        self.brand.setObjectName("Brand")
        self.subtitle = QLabel()
        self.subtitle.setObjectName("Sub")
        self.subtitle.setWordWrap(True)
        side.addWidget(self.brand)
        side.addWidget(self.subtitle)

        # Navigation lives in a scroll area so small windows never squash the buttons together.
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_body = QWidget()
        nav_layout = QVBoxLayout(nav_body)
        nav_layout.setContentsMargins(0, 8, 0, 0)
        nav_layout.setSpacing(6)
        self.nav_buttons = {}
        for key in ("today", "monthly", "ramadan", "calendar", "qibla", "education", "adhkar", "prayer_log", "quran", "mushaf", "settings", "about"):
            button = QPushButton()
            button.setObjectName("Nav")
            button.setCheckable(True)
            button.clicked.connect(lambda _=False, k=key: self.show_page(k))
            self.nav_buttons[key] = button
            nav_layout.addWidget(button)
        nav_layout.addStretch(1)
        nav_scroll.setWidget(nav_body)
        side.addWidget(nav_scroll, 1)

        self.lang_combo = QComboBox()
        for label, code in (("العربية", "ar"), ("Français", "fr"), ("English", "en")):
            self.lang_combo.addItem(label, code)
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(self.lang)))
        self.lang_combo.currentIndexChanged.connect(self.language_changed)
        side.addWidget(self.lang_combo)
        self.clock_label = QLabel("--:--:--")
        self.clock_label.setObjectName("Count")
        self.clock_label.setAlignment(Qt.AlignCenter)
        side.addWidget(self.clock_label)
        self.statusBar().setSizeGripEnabled(False)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.page_today())      # 0
        self.pages.addWidget(self.page_monthly())    # 1
        self.pages.addWidget(self.page_ramadan())    # 2
        self.pages.addWidget(self.page_calendar())   # 3
        self.pages.addWidget(self.page_qibla())      # 4
        self.pages.addWidget(self.page_education()) # 5
        self.pages.addWidget(self.page_adhkar())    # 6
        self.pages.addWidget(self.page_prayer_log()) # 7
        self.pages.addWidget(self.page_settings())   # 8
        self.pages.addWidget(self.page_about())      # 9
        self.pages.addWidget(self.page_quran())      # 10
        self.pages.addWidget(self.page_mushaf())     # 11

        outer.addWidget(sidebar)
        outer.addWidget(self.pages, 1)

    def say(self, text, timeout=12000):
        """Short status message shown under the pages (never resizes the sidebar)."""
        self.statusBar().showMessage(str(text).replace("\n", " "), timeout)

    def card(self, key):
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setProperty("active", False)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        name = QLabel()
        name.setObjectName("Muted")
        value = QLabel("--:--")
        value.setObjectName("CardValue")
        value.setProperty("active", False)
        layout.addWidget(name)
        layout.addStretch(1)
        layout.addWidget(value)
        self.cards[key] = (frame, name, value)
        return frame

    def highlight_cards(self, active_key=None):
        for key in PRAYER_KEYS:
            frame, _name, value_label = self.cards[key]
            active = key == active_key
            for widget in (frame, value_label):
                if bool(widget.property("active")) != active:
                    widget.setProperty("active", active)
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)

    def relayout_cards(self):
        """Three prayer cards per row on wide windows, two on narrow ones."""
        if not hasattr(self, "cards_grid"):
            return
        cols = 3 if self.width() >= 860 else 2
        if cols == self.card_cols:
            return
        self.card_cols = cols
        for index, key in enumerate(PRAYER_KEYS):
            frame = self.cards[key][0]
            self.cards_grid.removeWidget(frame)
            self.cards_grid.addWidget(frame, index // cols, index % cols)
        for column in range(3):
            self.cards_grid.setColumnStretch(column, 1 if column < cols else 0)

    def page_today(self):
        self.cards = {}
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        head = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setObjectName("Title")
        head.addWidget(self.title_label)
        head.addStretch(1)
        self.date_label = QLabel()
        self.date_label.setObjectName("Muted")
        head.addWidget(self.date_label)
        layout.addLayout(head)

        panel = QFrame()
        panel.setObjectName("Panel")
        inner = QHBoxLayout(panel)
        inner.setContentsMargins(22, 18, 22, 18)
        left = QVBoxLayout()
        self.next_label = QLabel()
        self.next_label.setObjectName("Muted")
        self.next_value = QLabel("—")
        self.next_value.setObjectName("Big")
        self.remaining_label = QLabel()
        self.remaining_label.setObjectName("Muted")
        self.countdown = QLabel("--:--:--")
        self.countdown.setObjectName("Count")
        left.addWidget(self.next_label)
        left.addWidget(self.next_value)
        left.addWidget(self.remaining_label)
        left.addWidget(self.countdown)
        inner.addLayout(left, 1)

        qibla_box = QVBoxLayout()
        self.qibla_small = Compass(120)
        self.qibla_deg = QLabel("—")
        self.qibla_deg.setAlignment(Qt.AlignCenter)
        self.qibla_deg.setStyleSheet("color: %s; font-weight: 700;" % COLORS["gold2"])
        qibla_box.addWidget(self.qibla_small)
        qibla_box.addWidget(self.qibla_deg)
        inner.addLayout(qibla_box)
        layout.addWidget(panel)

        grid = QGridLayout()
        grid.setSpacing(12)
        for index, key in enumerate(PRAYER_KEYS):
            grid.addWidget(self.card(key), index // 3, index % 3)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        self.cards_grid = grid
        layout.addLayout(grid)
        layout.addStretch(1)
        return page

    def page_education(self):
        """Educational guide presented as clear written instructions only."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.education_title = QLabel()
        self.education_title.setObjectName("Title")
        layout.addWidget(self.education_title)
        self.education_hint = QLabel()
        self.education_hint.setObjectName("Muted")
        self.education_hint.setWordWrap(True)
        layout.addWidget(self.education_hint)

        prayer_panel = QFrame()
        prayer_panel.setObjectName("Panel")
        prayer_layout = QVBoxLayout(prayer_panel)
        self.prayer_guide_label = QLabel()
        self.prayer_guide_label.setObjectName("Section")
        prayer_layout.addWidget(self.prayer_guide_label)
        self.prayer_guide = QTextBrowser()
        self.prayer_guide.setOpenExternalLinks(False)
        self.prayer_guide.setMinimumHeight(300)
        prayer_layout.addWidget(self.prayer_guide)
        layout.addWidget(prayer_panel)

        wudu_panel = QFrame()
        wudu_panel.setObjectName("Panel")
        wudu_layout = QVBoxLayout(wudu_panel)
        self.wudu_guide_label = QLabel()
        self.wudu_guide_label.setObjectName("Section")
        wudu_layout.addWidget(self.wudu_guide_label)
        self.wudu_guide = QTextBrowser()
        self.wudu_guide.setOpenExternalLinks(False)
        self.wudu_guide.setMinimumHeight(330)
        wudu_layout.addWidget(self.wudu_guide)
        layout.addWidget(wudu_panel)
        layout.addStretch(1)
        return page

    def education_html(self):
        if self.lang == "fr":
            prayer = """<h3>Les cinq prières obligatoires</h3><table width='100%' cellspacing='0' cellpadding='8'><tr><th>Prayer</th><th>Rakaat obligatoires</th><th>Lecture</th></tr><tr><td>Fajr</td><td><b>2</b></td><td>Audible</td></tr><tr><td>Dhuhr</td><td><b>4</b></td><td>Silencieuse</td></tr><tr><td>Asr</td><td><b>4</b></td><td>Silencieuse</td></tr><tr><td>Maghrib</td><td><b>3</b></td><td>Les 2 premières audibles</td></tr><tr><td>Isha</td><td><b>4</b></td><td>Les 2 premières audibles</td></tr></table><h3>Déroulement d’une rakaah</h3><ol><li>Faire l’intention dans le cœur, se tenir debout face à la qibla et dire « Allahou Akbar ».</li><li>Réciter Al-Fatiha, puis une sourate ou quelques versets dans les deux premières rakaat.</li><li>Faire le roukou’ en disant « Allahou Akbar », garder le dos droit, puis se relever.</li><li>Faire deux prosternations séparées par une position assise. Cela constitue une rakaah.</li><li>Après deux rakaat, s’asseoir pour le tachahhoud. Dans la dernière rakaah, réciter le tachahhoud puis terminer par le salam à droite et à gauche.</li></ol><p><b>Important :</b> les détails des actes recommandés peuvent varier selon l’école juridique. Pour un apprentissage pratique, demander à un enseignant de confiance.</p>"""
            wudu = """<h3>Les ablutions, étape par étape</h3><ol><li><b>Intention et invocation :</b> avoir l’intention de se purifier et dire « Bismillah ».</li><li><b>Mains :</b> laver les deux mains jusqu’aux poignets trois fois, en faisant passer l’eau entre les doigts.</li><li><b>Bouche et nez :</b> rincer la bouche, puis aspirer doucement de l’eau par le nez et la rejeter, trois fois.</li><li><b>Visage :</b> laver tout le visage, du front au menton et d’une oreille à l’autre, trois fois.</li><li><b>Bras :</b> laver le bras droit puis le gauche, des doigts jusqu’aux coudes inclus, trois fois.</li><li><b>Tête et oreilles :</b> passer les mains mouillées sur la tête, puis essuyer l’intérieur et l’extérieur des oreilles.</li><li><b>Pieds :</b> laver le pied droit puis le gauche jusqu’aux chevilles incluses, en frottant entre les orteils.</li></ol><p>Après les ablutions, il est recommandé de dire l’attestation connue de la purification.</p>"""
        elif self.lang == "en":
            prayer = """<h3>The five obligatory prayers</h3><table width='100%' cellspacing='0' cellpadding='8'><tr><th>Prayer</th><th>Obligatory rakaat</th><th>Recitation</th></tr><tr><td>Fajr</td><td><b>2</b></td><td>Audible</td></tr><tr><td>Dhuhr</td><td><b>4</b></td><td>Quiet</td></tr><tr><td>Asr</td><td><b>4</b></td><td>Quiet</td></tr><tr><td>Maghrib</td><td><b>3</b></td><td>First 2 audible</td></tr><tr><td>Isha</td><td><b>4</b></td><td>First 2 audible</td></tr></table><h3>One rakaah</h3><ol><li>Make the intention, face the qibla and say “Allahu Akbar”.</li><li>Recite Al-Fatiha and, in the first two rakaat, another surah or verses.</li><li>Bow, stand up, then perform two prostrations with a sitting between them.</li><li>After two rakaat, sit for tashahhud. In the final rakaah, complete tashahhud and finish with salam to both sides.</li></ol>"""
            wudu = """<h3>Wudu step by step</h3><ol><li>Make the intention and say “Bismillah”.</li><li>Wash both hands to the wrists three times, including between the fingers.</li><li>Rinse the mouth and nose three times.</li><li>Wash the entire face three times.</li><li>Wash the right then left arm to and including the elbows, three times.</li><li>Wipe the head with wet hands and wipe the ears.</li><li>Wash the right then left foot to and including the ankles, between the toes.</li></ol>"""
        else:
            prayer = """<h3>الصلوات الخمس وعدد الركعات المفروضة</h3><table width='100%' cellspacing='0' cellpadding='8'><tr><th>الصلاة</th><th>عدد الركعات</th><th>القراءة</th></tr><tr><td>الفجر</td><td><b>ركعتان</b></td><td>جهرية</td></tr><tr><td>الظهر</td><td><b>أربع ركعات</b></td><td>سرية</td></tr><tr><td>العصر</td><td><b>أربع ركعات</b></td><td>سرية</td></tr><tr><td>المغرب</td><td><b>ثلاث ركعات</b></td><td>الجهر في الأوليين</td></tr><tr><td>العشاء</td><td><b>أربع ركعات</b></td><td>الجهر في الأوليين</td></tr></table><h3>طريقة أداء الركعة بالتفصيل</h3><ol><li><b>النية والقيام:</b> تستحضر نية الصلاة في القلب، وتقف مستقبل القبلة مستويًا خاشعًا.</li><li><b>تكبيرة الإحرام:</b> ترفع يديك وتقول «الله أكبر»، ثم تضع اليمنى على اليسرى وتقرأ دعاء الاستفتاح إن كنت تعرفه.</li><li><b>القراءة:</b> تقرأ سورة الفاتحة، ثم سورة أو آيات من القرآن في الركعتين الأوليين.</li><li><b>الركوع:</b> تقول «الله أكبر»، وتنحني مع استقامة الظهر، وتقول «سبحان ربي العظيم»، ثم ترفع قائلًا «سمع الله لمن حمده» و«ربنا ولك الحمد».</li><li><b>السجود:</b> تهوي قائلًا «الله أكبر»، وتسجد على الجبهة والأنف والكفين والركبتين وأطراف القدمين، وتقول «سبحان ربي الأعلى». ترفع للجلوس ثم تسجد السجدة الثانية.</li><li><b>التشهد والسلام:</b> بعد الركعة الثانية تجلس للتشهد، وفي الركعة الأخيرة تكمل التشهد والصلاة الإبراهيمية، ثم تسلّم عن اليمين وعن اليسار.</li></ol><p><b>تنبيه:</b> هذا شرح تعليمي مختصر للفرائض الأساسية، وقد تختلف بعض السنن والتفاصيل بين المذاهب؛ يُستحسن التعلم عمليًا من معلّم موثوق.</p>"""
            wudu = """<h3>طريقة الوضوء بالتفصيل</h3><ol><li><b>النية والتسمية:</b> تنوي رفع الحدث والتطهر للصلاة، وتقول «بسم الله».</li><li><b>غسل الكفين:</b> تغسل الكفين إلى الرسغين ثلاث مرات، وتدخل الماء بين الأصابع.</li><li><b>المضمضة والاستنشاق:</b> تتمضمض بإدارة الماء في الفم، ثم تستنشق الماء بلطف وتستنثره، ثلاث مرات.</li><li><b>غسل الوجه:</b> تغسل الوجه كاملًا من منابت الشعر إلى أسفل الذقن، ومن الأذن إلى الأذن، ثلاث مرات.</li><li><b>غسل الذراعين:</b> تغسل الذراع اليمنى ثم اليسرى من أطراف الأصابع إلى المرفقين، مع إدخال المرفقين، ثلاث مرات.</li><li><b>مسح الرأس والأذنين:</b> تمسح الرأس بيدين مبللتين، ثم تمسح الأذنين من الداخل والخارج.</li><li><b>غسل الرجلين:</b> تغسل الرجل اليمنى ثم اليسرى إلى الكعبين، مع تخليل أصابع القدمين والتأكد من وصول الماء.</li></ol><p>بعد الفراغ من الوضوء يُستحب قول الشهادة الواردة في أحاديث الطهارة. احرص على عدم الإسراف في الماء.</p>"""
        return prayer, wudu

    def update_education_content(self):
        prayer, wudu = self.education_html()
        self.prayer_guide.setHtml(prayer)
        self.wudu_guide.setHtml(wudu)

    def page_adhkar(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.adhkar_title = QLabel()
        self.adhkar_title.setObjectName("Title")
        layout.addWidget(self.adhkar_title)
        self.adhkar_hint = QLabel()
        self.adhkar_hint.setObjectName("Muted")
        self.adhkar_hint.setWordWrap(True)
        layout.addWidget(self.adhkar_hint)
        controls = QHBoxLayout()
        self.adhkar_category_label = QLabel()
        self.adhkar_category_combo = QComboBox()
        self.adhkar_category_combo.addItem("الكل", "all")
        for category in sorted({row[0] for row in ADHKAR_DATA}):
            self.adhkar_category_combo.addItem(category, category)
        self.adhkar_category_combo.currentIndexChanged.connect(self.fill_adhkar_list)
        self.adhkar_search = QLineEdit()
        self.adhkar_search.textChanged.connect(self.fill_adhkar_list)
        controls.addWidget(self.adhkar_category_label)
        controls.addWidget(self.adhkar_category_combo, 1)
        controls.addWidget(self.adhkar_search, 2)
        layout.addLayout(controls)
        body = QHBoxLayout()
        self.adhkar_list = QListWidget()
        self.adhkar_list.currentRowChanged.connect(self.adhkar_selected)
        body.addWidget(self.adhkar_list, 1)
        panel = QFrame()
        panel.setObjectName("Panel")
        detail = QVBoxLayout(panel)
        self.adhkar_text = QLabel()
        self.adhkar_text.setWordWrap(True)
        self.adhkar_text.setTextFormat(Qt.TextFormat.RichText)
        self.adhkar_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.adhkar_text.setMinimumHeight(220)
        detail.addWidget(self.adhkar_text, 1)
        self.adhkar_repeat_label = QLabel()
        self.adhkar_repeat_label.setObjectName("Muted")
        detail.addWidget(self.adhkar_repeat_label)
        row = QHBoxLayout()
        self.adhkar_copy_button = QPushButton()
        self.adhkar_copy_button.clicked.connect(self.copy_adhkar)
        self.adhkar_repeat_button = QPushButton()
        self.adhkar_repeat_button.setObjectName("Primary")
        self.adhkar_repeat_button.clicked.connect(self.repeat_adhkar)
        self.adhkar_reset_button = QPushButton()
        self.adhkar_reset_button.clicked.connect(self.reset_adhkar_counter)
        row.addWidget(self.adhkar_copy_button)
        row.addWidget(self.adhkar_repeat_button)
        row.addWidget(self.adhkar_reset_button)
        detail.addLayout(row)
        body.addWidget(panel, 2)
        layout.addLayout(body, 1)
        self.adhkar_status = QLabel()
        self.adhkar_status.setObjectName("Muted")
        layout.addWidget(self.adhkar_status)
        self.fill_adhkar_list()
        return page

    def fill_adhkar_list(self):
        if not hasattr(self, "adhkar_list"):
            return
        category = self.adhkar_category_combo.currentData()
        query = self.adhkar_search.text().strip()
        self.adhkar_list.blockSignals(True)
        self.adhkar_list.clear()
        for index, (cat, title, text, repeat) in enumerate(ADHKAR_DATA):
            if category != "all" and cat != category:
                continue
            if query and query not in (cat + title + text):
                continue
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, index)
            self.adhkar_list.addItem(item)
        self.adhkar_list.blockSignals(False)
        if self.adhkar_list.count():
            self.adhkar_list.setCurrentRow(0)
        else:
            self.adhkar_text.setText("<p>لا توجد نتائج مطابقة.</p>")

    def adhkar_selected(self, row):
        if row < 0:
            return
        index = self.adhkar_list.item(row).data(Qt.ItemDataRole.UserRole)
        _category, title, text, repeat = ADHKAR_DATA[index]
        self.adhkar_text.setText("<h2>%s</h2><p style='font-size:22px; line-height:1.8'>%s</p><p>%s</p>" % (title, text, "التكرار المقترح: %d مرة" % repeat))
        self.adhkar_repeat_label.setText(tr(self.lang, "adhkar_times") + ": " + str(repeat))
        self.adhkar_counter = 0
        self.adhkar_status.clear()

    def copy_adhkar(self):
        row = self.adhkar_list.currentRow()
        if row < 0:
            return
        index = self.adhkar_list.item(row).data(Qt.ItemDataRole.UserRole)
        QApplication.clipboard().setText(ADHKAR_DATA[index][1])
        self.adhkar_status.setText(tr(self.lang, "adhkar_copied"))

    def repeat_adhkar(self):
        if self.adhkar_list.currentRow() < 0:
            return
        self.adhkar_counter = getattr(self, "adhkar_counter", 0) + 1
        self.adhkar_status.setText(tr(self.lang, "repeat_count") + ": " + str(self.adhkar_counter))
        self.adhkar_repeat_button.setText(tr(self.lang, "repeat_button") + "  (" + str(self.adhkar_counter) + ")")

    def reset_adhkar_counter(self):
        self.adhkar_counter = 0
        self.adhkar_status.clear()
        self.adhkar_repeat_button.setText(tr(self.lang, "repeat_button"))

    def page_prayer_log(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.prayer_log_title = QLabel()
        self.prayer_log_title.setObjectName("Title")
        layout.addWidget(self.prayer_log_title)
        self.prayer_log_hint = QLabel()
        self.prayer_log_hint.setObjectName("Muted")
        self.prayer_log_hint.setWordWrap(True)
        layout.addWidget(self.prayer_log_hint)
        panel = QFrame(); panel.setObjectName("Panel")
        inner = QVBoxLayout(panel)
        self.prayer_log_date = QLabel()
        self.prayer_log_date.setObjectName("Section")
        inner.addWidget(self.prayer_log_date)
        self.prayer_checks = {}
        for key in PRAYER_KEYS:
            check = QCheckBox()
            check.stateChanged.connect(self.save_prayer_log)
            self.prayer_checks[key] = check
            inner.addWidget(check)
        self.prayer_log_progress_label = QLabel()
        self.prayer_log_progress_label.setObjectName("Big")
        inner.addWidget(self.prayer_log_progress_label)
        self.prayer_log_status = QLabel(); self.prayer_log_status.setObjectName("Muted")
        inner.addWidget(self.prayer_log_status)
        layout.addWidget(panel)
        layout.addStretch(1)
        self.load_prayer_log()
        return page

    def prayer_log_key(self):
        return datetime.now(self.tz).date().isoformat()

    def load_prayer_log(self):
        if not hasattr(self, "prayer_checks"):
            return
        saved = self.prayer_log.get(self.prayer_log_key(), {})
        for key, check in self.prayer_checks.items():
            check.blockSignals(True)
            check.setChecked(bool(saved.get(key, False)))
            check.blockSignals(False)
        self.update_prayer_log_progress()

    def save_prayer_log(self):
        key = self.prayer_log_key()
        self.prayer_log[key] = {name: check.isChecked() for name, check in self.prayer_checks.items()}
        self.write_config()
        self.prayer_log_status.setText(tr(self.lang, "prayer_log_done"))
        self.update_prayer_log_progress()

    def update_prayer_log_progress(self):
        if not hasattr(self, "prayer_checks"):
            return
        done = sum(check.isChecked() for check in self.prayer_checks.values())
        total = len(self.prayer_checks)
        self.prayer_log_progress_label.setText(tr(self.lang, "prayer_log_progress") + ":  " + str(done) + " / " + str(total))

    def page_monthly(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.monthly_title = QLabel()
        self.monthly_title.setObjectName("Title")
        layout.addWidget(self.monthly_title)
        controls = QHBoxLayout()
        self.m_year_label = QLabel()
        self.m_year = QSpinBox()
        self.m_year.setRange(1900, 2200)
        self.m_year.setValue(date.today().year)
        self.m_year.valueChanged.connect(self.fill_monthly)
        self.m_month_label = QLabel()
        self.m_month = QSpinBox()
        self.m_month.setRange(1, 12)
        self.m_month.setValue(date.today().month)
        self.m_month.valueChanged.connect(self.fill_monthly)
        self.export_pdf_btn = QPushButton()
        self.export_pdf_btn.setObjectName("Primary")
        self.export_pdf_btn.clicked.connect(self.export_monthly)
        controls.addWidget(self.m_year_label)
        controls.addWidget(self.m_year)
        controls.addSpacing(20)
        controls.addWidget(self.m_month_label)
        controls.addWidget(self.m_month)
        controls.addStretch(1)
        controls.addWidget(self.export_pdf_btn)
        layout.addLayout(controls)
        self.monthly_table = QTableWidget(0, 8)
        self.monthly_table.setEditTriggers(NO_EDIT)
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.horizontalHeader().setSectionResizeMode(STRETCH)
        self.monthly_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.monthly_table.verticalHeader().setVisible(False)
        layout.addWidget(self.monthly_table, 1)
        return page

    def page_ramadan(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.ramadan_title = QLabel()
        self.ramadan_title.setObjectName("Title")
        layout.addWidget(self.ramadan_title)
        self.ramadan_status = QLabel()
        self.ramadan_status.setObjectName("Big")
        layout.addWidget(self.ramadan_status)
        controls = QHBoxLayout()
        self.r_year_label = QLabel()
        self.r_year = QSpinBox()
        self.r_year.setRange(1300, 1600)
        self.r_year.setValue(self.to_hijri(date.today())[0])
        self.r_year.valueChanged.connect(self.fill_ramadan)
        self.export_ramadan_btn = QPushButton()
        self.export_ramadan_btn.setObjectName("Primary")
        self.export_ramadan_btn.clicked.connect(self.export_ramadan)
        controls.addWidget(self.r_year_label)
        controls.addWidget(self.r_year)
        controls.addStretch(1)
        controls.addWidget(self.export_ramadan_btn)
        layout.addLayout(controls)
        self.ramadan_note = QLabel()
        self.ramadan_note.setObjectName("Muted")
        self.ramadan_note.setWordWrap(True)
        layout.addWidget(self.ramadan_note)
        self.ramadan_table = QTableWidget(0, 4)
        self.ramadan_table.setEditTriggers(NO_EDIT)
        self.ramadan_table.setAlternatingRowColors(True)
        self.ramadan_table.horizontalHeader().setSectionResizeMode(STRETCH)
        self.ramadan_table.verticalHeader().setVisible(False)
        layout.addWidget(self.ramadan_table, 1)
        return page

    def page_calendar(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.calendar_title = QLabel()
        self.calendar_title.setObjectName("Title")
        layout.addWidget(self.calendar_title)
        controls = QHBoxLayout()
        self.c_year_label = QLabel()
        self.c_year = QSpinBox()
        self.c_year.setRange(1900, 2200)
        self.c_year.setValue(date.today().year)
        self.c_year.valueChanged.connect(self.fill_calendar)
        controls.addWidget(self.c_year_label)
        controls.addWidget(self.c_year)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.calendar_note = QLabel()
        self.calendar_note.setObjectName("Muted")
        self.calendar_note.setWordWrap(True)
        layout.addWidget(self.calendar_note)
        self.calendar_table = QTableWidget(0, 3)
        self.calendar_table.setEditTriggers(NO_EDIT)
        self.calendar_table.setAlternatingRowColors(True)
        self.calendar_table.horizontalHeader().setSectionResizeMode(STRETCH)
        self.calendar_table.verticalHeader().setVisible(False)
        layout.addWidget(self.calendar_table, 1)
        return page

    def page_qibla(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)
        self.qibla_title = QLabel()
        self.qibla_title.setObjectName("Title")
        self.qibla_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qibla_title)
        self.qibla_big = Compass()
        layout.addWidget(self.qibla_big, 1)
        self.qibla_big_deg = QLabel("—")
        self.qibla_big_deg.setObjectName("Big")
        self.qibla_big_deg.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qibla_big_deg)
        self.distance_label = QLabel()
        self.distance_label.setObjectName("Muted")
        self.distance_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.distance_label)
        self.qibla_hint = QLabel()
        self.qibla_hint.setObjectName("Muted")
        self.qibla_hint.setWordWrap(True)
        self.qibla_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qibla_hint)
        return page

    def page_quran(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.quran_title = QLabel()
        self.quran_title.setObjectName("Title")
        self.quran_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.quran_title)
        self.quran_hint = QLabel()
        self.quran_hint.setObjectName("Muted")
        self.quran_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.quran_hint)

        controls = QHBoxLayout()
        self.quran_reciter_label = QLabel()
        self.quran_reciter = QComboBox()
        for name, edition in QURAN_RECITERS:
            self.quran_reciter.addItem(name, edition)
        self.quran_reciter.setCurrentIndex(self.quran_reciter_idx)
        controls.addWidget(self.quran_reciter_label)
        controls.addWidget(self.quran_reciter, 1)
        layout.addLayout(controls)

        self.quran_list = QListWidget()
        self.quran_list.setStyleSheet(
            "QListWidget{background:#18372D;border:1px solid #33584A;border-radius:14px;"
            "font-size:17px;padding:8px;}"
            "QListWidget::item{padding:9px;border-bottom:1px solid #29483B;}"
            "QListWidget::item:selected{background:#214B3B;color:#F0D99D;}"
        )
        for number, name in enumerate(QURAN_SURAHS, 1):
            self.quran_list.addItem("%03d   %s" % (number, name))
        self.quran_list.setCurrentRow(self.quran_surah_idx)
        self.quran_list.itemDoubleClicked.connect(lambda _item: self.play_quran())
        layout.addWidget(self.quran_list, 1)

        actions = QHBoxLayout()
        self.quran_play_button = QPushButton()
        self.quran_play_button.setObjectName("Primary")
        self.quran_pause_button = QPushButton()
        self.quran_stop_button = QPushButton()
        self.quran_play_button.clicked.connect(self.play_quran)
        self.quran_pause_button.clicked.connect(self.pause_quran)
        self.quran_stop_button.clicked.connect(self.stop_quran)
        actions.addWidget(self.quran_play_button)
        actions.addWidget(self.quran_pause_button)
        actions.addWidget(self.quran_stop_button)
        layout.addLayout(actions)

        slider_row = QHBoxLayout()
        self.quran_progress = QSlider(Qt.Orientation.Horizontal)
        self.quran_progress.setRange(0, 0)
        # A timeline always runs left to right, even in the Arabic interface.
        self.quran_progress.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.quran_progress.sliderReleased.connect(self.seek_quran)
        self.quran_time = QLabel("0:00 / 0:00")
        self.quran_time.setObjectName("Muted")
        self.quran_time.setMinimumWidth(120)
        self.quran_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quran_time.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        slider_row.addWidget(self.quran_progress, 1)
        slider_row.addWidget(self.quran_time)
        layout.addLayout(slider_row)
        self.quran_status = QLabel()
        self.quran_status.setObjectName("Muted")
        self.quran_status.setWordWrap(True)
        self.quran_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.quran_status)
        if self.quran_player:
            self.quran_player.positionChanged.connect(self.quran_position_changed)
            self.quran_player.durationChanged.connect(self.quran_duration_changed)
            self.quran_player.errorOccurred.connect(self.quran_error)
        return page

    def update_quran_time(self):
        self.quran_time.setText("%s / %s" % (fmt_ms(self._quran_position), fmt_ms(self._quran_duration)))

    def play_quran(self):
        if not self.quran_player:
            self.quran_status.setText(tr(self.lang, "quran_error"))
            return
        number = self.quran_list.currentRow() + 1
        if number < 1 or number > 114:
            return
        edition = self.quran_reciter.currentData()
        url = "https://cdn.islamic.network/quran/audio-surah/128/%s/%d.mp3" % (edition, number)
        self.quran_player.stop()
        self.quran_player.setSource(QUrl(url))
        self.quran_player.play()
        self.quran_status.setText("%s · %s" % (QURAN_SURAHS[number - 1], tr(self.lang, "quran_stream")))
        self.write_config()  # remembers the last surah and reciter

    def pause_quran(self):
        if self.quran_player:
            if self.quran_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.quran_player.pause()
            else:
                self.quran_player.play()

    def stop_quran(self):
        if self.quran_player:
            self.quran_player.stop()
        self.quran_progress.setValue(0)
        self._quran_position = 0
        self.update_quran_time()
        self.quran_status.setText(tr(self.lang, "quran_ready"))

    def seek_quran(self):
        if self.quran_player:
            self.quran_player.setPosition(self.quran_progress.value())

    def quran_duration_changed(self, duration):
        self._quran_duration = max(0, duration)
        self.quran_progress.setRange(0, self._quran_duration)
        self.update_quran_time()

    def quran_position_changed(self, position):
        self._quran_position = max(0, position)
        if not self.quran_progress.isSliderDown():
            self.quran_progress.setValue(position)
        self.update_quran_time()

    def quran_error(self, _error, _message=""):
        self.quran_status.setText(tr(self.lang, "quran_error"))

    def load_mushaf_data(self):
        """Accept both the bundled format and the original Al Quran Cloud response."""
        candidates = (APP_DIR / "quran-uthmani.json", bundle_dir() / "quran-uthmani.json",
                      CONFIG_DIR / "quran-uthmani.json")
        for path in candidates:
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                if "data" in data and isinstance(data["data"], dict):
                    data = data["data"]
                surahs = data["surahs"]
                verses = []
                pages = {}
                references = {}
                for surah in surahs:
                    for ayah in surah["ayahs"]:
                        entry = dict(ayah, surah_number=surah["number"], surah_name=surah["name"])
                        verses.append(entry)
                        pages.setdefault(ayah["page"], []).append(entry)
                        references[(surah["number"], ayah["numberInSurah"])] = entry
                if len(surahs) != 114 or len(verses) != 6236 or len(pages) != 604:
                    raise ValueError("Incomplete Uthmani Quran data")
                self.mushaf_surahs = surahs
                self.mushaf_verses = verses
                self.mushaf_pages = pages
                self.mushaf_by_reference = references
                self.mushaf_error = ""
                return
            except (OSError, KeyError, TypeError, ValueError) as exc:
                self.mushaf_error = "mushaf_invalid"
                print("mushaf data:", path, exc)

    def page_mushaf(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        self.mushaf_title = QLabel()
        self.mushaf_title.setObjectName("Title")
        self.mushaf_title.setAlignment(Qt.AlignCenter)
        self.mushaf_hint = QLabel()
        self.mushaf_hint.setObjectName("Muted")
        self.mushaf_hint.setAlignment(Qt.AlignCenter)
        head = QHBoxLayout()
        head.addWidget(self.mushaf_title)
        head.addStretch(1)
        head.addWidget(self.mushaf_hint)
        layout.addLayout(head)

        controls = QHBoxLayout()
        self.mushaf_surah_label = QLabel()
        self.mushaf_surah_combo = QComboBox()
        for number, name in enumerate(QURAN_SURAHS, 1):
            self.mushaf_surah_combo.addItem("%d. %s" % (number, name), number)
        self.mushaf_surah_combo.currentIndexChanged.connect(self.mushaf_choose_surah)
        self.mushaf_page_label = QLabel()
        self.mushaf_page_spin = QSpinBox()
        self.mushaf_page_spin.setRange(1, 604)
        self.mushaf_page_spin.valueChanged.connect(self.show_mushaf_page)
        controls.addWidget(self.mushaf_surah_label)
        controls.addWidget(self.mushaf_surah_combo, 1)
        controls.addWidget(self.mushaf_page_label)
        controls.addWidget(self.mushaf_page_spin)
        layout.addLayout(controls)

        search_row = QHBoxLayout()
        self.mushaf_search_edit = QLineEdit()
        self.mushaf_search_edit.returnPressed.connect(self.search_mushaf)
        self.mushaf_search_button = QPushButton()
        self.mushaf_search_button.clicked.connect(self.search_mushaf)
        self.mushaf_settings_button = QPushButton()
        self.mushaf_settings_button.clicked.connect(self.open_mushaf_settings)
        search_row.addWidget(self.mushaf_search_edit, 1)
        search_row.addWidget(self.mushaf_search_button)
        search_row.addWidget(self.mushaf_settings_button)
        layout.addLayout(search_row)

        book = QWidget()
        book_layout = QHBoxLayout(book)
        book_layout.setContentsMargins(0, 0, 0, 0)
        book_layout.setSpacing(0)
        book_layout.setDirection(QBoxLayout.Direction.RightToLeft)
        self.mushaf_right_page = QTextBrowser()
        self.mushaf_left_page = QTextBrowser()
        paper_style = (
            "QTextBrowser { background: #F9F3E4; color: #24332B; border: 9px solid #665336; "
            "border-radius: 13px; font-family: 'Amiri Quran'; font-size: 15pt; "
            "selection-background-color: #D8B66A; }"
            "QScrollBar:vertical { background: #f3ead5; width: 8px; }"
            "QScrollBar::handle:vertical { background: #bea77a; border-radius: 4px; min-height: 24px; }"
        )
        for browser in (self.mushaf_right_page, self.mushaf_left_page):
            browser.setStyleSheet(paper_style)
            browser.setReadOnly(True)
        book_layout.addWidget(self.mushaf_right_page, 1)
        book_layout.addWidget(self.mushaf_left_page, 1)
        layout.addWidget(book, 1)

        self.mushaf_results_dialog = QDialog(self)
        self.mushaf_results_dialog.resize(800, 620)
        self.mushaf_results_dialog.setMinimumSize(520, 400)
        results_layout = QVBoxLayout(self.mushaf_results_dialog)
        results_layout.setContentsMargins(20, 18, 20, 18)
        results_layout.setSpacing(12)
        self.mushaf_results_label = QLabel()
        self.mushaf_results_label.setObjectName("Title")
        results_layout.addWidget(self.mushaf_results_label)
        self.mushaf_results_browser = QTextBrowser()
        self.mushaf_results_browser.setOpenLinks(False)
        self.mushaf_results_browser.anchorClicked.connect(self.open_mushaf_result)
        self.mushaf_results_browser.setStyleSheet(
            "QTextBrowser { background: #18372D; border: 1px solid #33584A; "
            "border-radius: 12px; color: #F5F2E9; padding: 12px; }"
        )
        results_layout.addWidget(self.mushaf_results_browser, 1)
        self.mushaf_return_button = QPushButton()
        self.mushaf_return_button.clicked.connect(self.mushaf_results_dialog.hide)
        results_layout.addWidget(self.mushaf_return_button)

        navigation = QHBoxLayout()
        self.mushaf_previous_button = QPushButton()
        self.mushaf_next_button = QPushButton()
        self.mushaf_previous_button.clicked.connect(lambda: self.turn_mushaf(-1))
        self.mushaf_next_button.clicked.connect(lambda: self.turn_mushaf(1))
        navigation.addWidget(self.mushaf_previous_button)
        navigation.addStretch(1)
        navigation.addWidget(self.mushaf_next_button)
        layout.addLayout(navigation)
        self.mushaf_current_page = self.mushaf_settings["last_page"]
        self.mushaf_active_query = ""
        self.mushaf_selected_ayah = None
        self.mushaf_two_page = bool(self.mushaf_settings["two_page"]) and self.width() >= 1080
        self.build_mushaf_settings_dialog()
        self.render_mushaf()
        return page

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.relayout_cards()
        if hasattr(self, "mushaf_left_page") and hasattr(self, "mushaf_current_page"):
            two_page = bool(self.mushaf_settings["two_page"]) and self.width() >= 1080
            if two_page != self.mushaf_two_page:
                self.mushaf_two_page = two_page
                self.render_mushaf()

    def build_mushaf_settings_dialog(self):
        self.mushaf_settings_dialog = QDialog(self)
        self.mushaf_settings_dialog.setMinimumSize(485, 450)
        self.mushaf_settings_dialog.resize(545, 560)
        layout = QVBoxLayout(self.mushaf_settings_dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        self.mushaf_settings_title = QLabel()
        self.mushaf_settings_title.setObjectName("Title")
        layout.addWidget(self.mushaf_settings_title)
        form = QFormLayout()
        form.setSpacing(12)
        self.mushaf_setting_labels = {}

        def add_row(key, widget):
            label = QLabel()
            label.setObjectName("Muted")
            self.mushaf_setting_labels[key] = label
            form.addRow(label, widget)

        self.mushaf_font_combo = QComboBox()
        self.mushaf_font_combo.addItems(["Amiri Quran", "Traditional Arabic", "Noto Naskh Arabic"])
        add_row("mushaf_font", self.mushaf_font_combo)
        self.mushaf_size_spin = QSpinBox()
        self.mushaf_size_spin.setRange(12, 38)
        self.mushaf_size_spin.setSuffix(" pt")
        add_row("mushaf_size", self.mushaf_size_spin)
        self.mushaf_spacing_spin = QSpinBox()
        self.mushaf_spacing_spin.setRange(100, 220)
        self.mushaf_spacing_spin.setSingleStep(5)
        self.mushaf_spacing_spin.setSuffix(" %")
        add_row("mushaf_spacing", self.mushaf_spacing_spin)

        self.mushaf_theme_combo = QComboBox()
        self.mushaf_theme_combo.addItem("", "custom")
        for key in MUSHAF_THEMES:
            self.mushaf_theme_combo.addItem("", key)
        self.mushaf_theme_combo.currentIndexChanged.connect(self.choose_mushaf_theme)
        add_row("mushaf_theme", self.mushaf_theme_combo)

        self.mushaf_color_buttons = {}
        for key, label_key in (("paper", "mushaf_paper"), ("ink", "mushaf_ink"),
                               ("highlight", "mushaf_highlight")):
            button = QPushButton()
            button.clicked.connect(lambda _=False, name=key: self.choose_mushaf_color(name))
            self.mushaf_color_buttons[key] = button
            add_row(label_key, button)
        layout.addLayout(form)
        self.mushaf_spread_check = QCheckBox()
        layout.addWidget(self.mushaf_spread_check)
        layout.addStretch(1)
        actions = QHBoxLayout()
        self.mushaf_reset_button = QPushButton()
        self.mushaf_reset_button.clicked.connect(self.reset_mushaf_prefs)
        self.mushaf_cancel_button = QPushButton()
        self.mushaf_cancel_button.clicked.connect(self.mushaf_settings_dialog.reject)
        self.mushaf_save_button = QPushButton()
        self.mushaf_save_button.setObjectName("Primary")
        self.mushaf_save_button.clicked.connect(self.save_mushaf_prefs)
        actions.addWidget(self.mushaf_reset_button)
        actions.addStretch(1)
        actions.addWidget(self.mushaf_cancel_button)
        actions.addWidget(self.mushaf_save_button)
        layout.addLayout(actions)
        self.mushaf_pending_colors = {}

    def update_mushaf_color_buttons(self):
        for name, button in self.mushaf_color_buttons.items():
            color = self.mushaf_pending_colors[name]
            contrast = "#122720" if QColor(color).lightness() > 140 else "#F5F2E9"
            button.setText(color.upper())
            button.setStyleSheet(
                "QPushButton{background:%s;color:%s;border:1px solid #D8B66A;"
                "border-radius:9px;text-align:center;}" % (color, contrast)
            )

    def choose_mushaf_theme(self, _index):
        theme = self.mushaf_theme_combo.currentData()
        if theme in MUSHAF_THEMES:
            self.mushaf_pending_colors = dict(zip(("paper", "ink", "highlight"), MUSHAF_THEMES[theme]))
            self.update_mushaf_color_buttons()

    def choose_mushaf_color(self, name):
        color = QColorDialog.getColor(
            QColor(self.mushaf_pending_colors[name]), self.mushaf_settings_dialog,
            tr(self.lang, "mushaf_" + name),
        )
        if color.isValid():
            self.mushaf_pending_colors[name] = color.name()
            self.mushaf_theme_combo.blockSignals(True)
            self.mushaf_theme_combo.setCurrentIndex(0)
            self.mushaf_theme_combo.blockSignals(False)
            self.update_mushaf_color_buttons()

    def reset_mushaf_prefs(self):
        self.mushaf_font_combo.setCurrentText(MUSHAF_DEFAULTS["font_family"])
        self.mushaf_size_spin.setValue(MUSHAF_DEFAULTS["font_size"])
        self.mushaf_spacing_spin.setValue(MUSHAF_DEFAULTS["line_height"])
        self.mushaf_spread_check.setChecked(False)
        self.mushaf_theme_combo.blockSignals(True)
        self.mushaf_theme_combo.setCurrentIndex(1)
        self.mushaf_theme_combo.blockSignals(False)
        self.mushaf_pending_colors = {
            key: MUSHAF_DEFAULTS[key] for key in ("paper", "ink", "highlight")
        }
        self.update_mushaf_color_buttons()

    def open_mushaf_settings(self):
        current = self.mushaf_settings
        self.mushaf_font_combo.setCurrentText(current["font_family"])
        self.mushaf_size_spin.setValue(current["font_size"])
        self.mushaf_spacing_spin.setValue(current["line_height"])
        self.mushaf_spread_check.setChecked(current["two_page"])
        self.mushaf_pending_colors = {key: current[key] for key in ("paper", "ink", "highlight")}
        self.mushaf_theme_combo.blockSignals(True)
        self.mushaf_theme_combo.setCurrentIndex(0)
        self.mushaf_theme_combo.blockSignals(False)
        self.update_mushaf_color_buttons()
        self.mushaf_settings_dialog.exec()

    def save_mushaf_prefs(self):
        self.mushaf_settings.update({
            "font_family": self.mushaf_font_combo.currentText(),
            "font_size": self.mushaf_size_spin.value(),
            "line_height": self.mushaf_spacing_spin.value(),
            "two_page": self.mushaf_spread_check.isChecked(),
            **self.mushaf_pending_colors,
        })
        save_mushaf_settings(self.mushaf_settings)
        self.mushaf_two_page = bool(self.mushaf_settings["two_page"]) and self.width() >= 1080
        self.render_mushaf()
        self.mushaf_settings_dialog.accept()

    def mushaf_choose_surah(self, _index):
        number = self.mushaf_surah_combo.currentData()
        if self.mushaf_surahs and number and 1 <= number <= 114:
            first_page = self.mushaf_surahs[number - 1]["ayahs"][0]["page"]
            self.show_mushaf_page(first_page)

    def show_mushaf_page(self, number):
        self.mushaf_current_page = max(1, min(604, number))
        self.mushaf_settings["last_page"] = self.mushaf_current_page
        save_mushaf_settings(self.mushaf_settings)
        self.mushaf_selected_ayah = None
        self.mushaf_page_spin.blockSignals(True)
        self.mushaf_page_spin.setValue(self.mushaf_current_page)
        self.mushaf_page_spin.blockSignals(False)
        self.render_mushaf()

    def turn_mushaf(self, direction):
        two = self.mushaf_two_page
        base = ((self.mushaf_current_page - 1) // 2) * 2 + 1 if two else self.mushaf_current_page
        number = base + direction * (2 if two else 1)
        if 1 <= number <= 604:
            self.show_mushaf_page(number)

    def mushaf_page_html(self, number):
        ayahs = self.mushaf_pages.get(number, [])
        if not ayahs:
            return "<p align='center'>%s</p>" % escape(tr(self.lang, self.mushaf_error or "mushaf_missing"))
        prefs = self.mushaf_settings
        accent = "#e5c88b" if QColor(prefs["paper"]).lightness() < 100 else "#796847"
        title_color = "#f0d99d" if QColor(prefs["paper"]).lightness() < 100 else "#526a51"
        size = prefs["font_size"]
        parts = [
            "<html><body dir='rtl' bgcolor='%s' style='color:%s;font-family:%s;'>"
            % (prefs["paper"], prefs["ink"], prefs["font_family"]),
            "<p align='center' style='font-size:10pt;color:%s;margin:2px;'>%s &nbsp; ۞ &nbsp; الجزء %s</p>"
            % (accent, escape(ayahs[0]["surah_name"]), ayahs[0]["juz"]),
        ]
        paragraph_open = False
        for ayah in ayahs:
            if ayah["numberInSurah"] == 1:
                if paragraph_open:
                    parts.append("</p>")
                    paragraph_open = False
                parts.append("<p align='center' style='font-size:%spt;color:%s;margin:6px;'>"
                             "۞ &nbsp; %s &nbsp; ۞</p>" % (max(14, size - 1), title_color, escape(ayah["surah_name"])))
            if not paragraph_open:
                parts.append("<p align='justify' style='font-family:%s;font-size:%spt;line-height:%s%%;margin:0;'>"
                             % (prefs["font_family"], size, prefs["line_height"]))
                paragraph_open = True
            selected = self.mushaf_selected_ayah == ayah["number"]
            content = quran_highlight(ayah["text"], self.mushaf_active_query, whole=selected,
                                      highlight=prefs["highlight"])
            parts.append("<a name='ayah-%s'></a>%s " % (ayah["number"], content))
            parts.append("<font color='%s'> ۞ %s </font> " % (accent, ayah["numberInSurah"]))
        if paragraph_open:
            parts.append("</p>")
        parts.append("<p align='center' style='font-size:10pt;color:%s;margin:3px;'>❈ %s ❈</p></body></html>"
                     % (accent, number))
        return "".join(parts)

    def render_mushaf(self):
        if not hasattr(self, "mushaf_right_page"):
            return
        prefs = self.mushaf_settings
        paper_style = (
            "QTextBrowser { background:%s;color:%s;border:8px solid #665336;border-radius:13px;"
            "font-family:'%s';font-size:%spt;selection-background-color:%s; }"
            "QScrollBar:vertical{background:%s;width:8px;}"
            "QScrollBar::handle:vertical{background:#bea77a;border-radius:4px;min-height:24px;}"
            % (prefs["paper"], prefs["ink"], prefs["font_family"], prefs["font_size"],
               prefs["highlight"], prefs["paper"])
        )
        for browser in (self.mushaf_right_page, self.mushaf_left_page):
            browser.setStyleSheet(paper_style)
        self.mushaf_left_page.setVisible(self.mushaf_two_page)
        self.mushaf_page_spin.blockSignals(True)
        self.mushaf_page_spin.setValue(self.mushaf_current_page)
        self.mushaf_page_spin.blockSignals(False)
        right_number = ((self.mushaf_current_page - 1) // 2) * 2 + 1 if self.mushaf_two_page else self.mushaf_current_page
        self.mushaf_right_page.setHtml(self.mushaf_page_html(right_number))
        if self.mushaf_two_page:
            self.mushaf_left_page.setHtml(self.mushaf_page_html(right_number + 1))
        if self.mushaf_selected_ayah is not None:
            for browser in (self.mushaf_right_page, self.mushaf_left_page):
                browser.scrollToAnchor("ayah-%s" % self.mushaf_selected_ayah)
        step = 2 if self.mushaf_two_page else 1
        self.mushaf_previous_button.setEnabled(right_number > 1)
        self.mushaf_next_button.setEnabled(right_number + step <= 604)
        if self.mushaf_pages.get(self.mushaf_current_page):
            verses = self.mushaf_pages[self.mushaf_current_page]
            number = next((v["surah_number"] for v in verses if v["numberInSurah"] == 1), verses[0]["surah_number"])
            self.mushaf_surah_combo.blockSignals(True)
            self.mushaf_surah_combo.setCurrentIndex(number - 1)
            self.mushaf_surah_combo.blockSignals(False)

    def mushaf_normalized(self):
        """Diacritic-free text of every verse, computed once and reused by every search."""
        if self._mushaf_norm is None or len(self._mushaf_norm) != len(self.mushaf_verses):
            self._mushaf_norm = [quran_normalize_with_positions(v["text"])[0] for v in self.mushaf_verses]
        return self._mushaf_norm

    def search_mushaf(self):
        query = self.mushaf_search_edit.text().strip()
        if not query:
            self.mushaf_active_query = ""
            self.render_mushaf()
            return
        if not self.mushaf_verses:
            self.mushaf_results_browser.setHtml("<p>%s</p>" % escape(tr(self.lang, self.mushaf_error or "mushaf_missing")))
            self.mushaf_results_dialog.show()
            return
        reference = query.split(":")
        if len(reference) == 2 and all(part.strip().isdigit() for part in reference):
            verse = self.mushaf_by_reference.get((int(reference[0]), int(reference[1])))
            matches = [verse] if verse else []
            self.mushaf_active_query = ""
        else:
            needle, _ = quran_normalize_with_positions(query)
            normalized = self.mushaf_normalized()
            matches = [v for v, text in zip(self.mushaf_verses, normalized) if needle and needle in text]
            self.mushaf_active_query = query
        self.mushaf_results_label.setText(tr(self.lang, "mushaf_count", count=len(matches)))
        shown = matches[:MUSHAF_MAX_RESULTS]
        blocks = ["<html><body dir='rtl' style='color:#f5f2e9;'>"]
        if len(matches) > len(shown):
            blocks.append("<p style='color:#d8b66a;'>%s</p>" % escape(tr(self.lang, "mushaf_limited", shown=len(shown))))
        for verse in shown:
            link = "mushaf://open/%s/%s" % (verse["page"], verse["number"])
            header = "%s · %s:%s · %s %s" % (
                verse["surah_name"], verse["surah_number"], verse["numberInSurah"],
                tr(self.lang, "mushaf_page"), verse["page"])
            blocks.append("<p style='margin-bottom:12px;'><a href='%s' style='color:#f0d99d;'>%s</a><br>"
                          "<a href='%s' style='color:#f5f2e9;font-family:Amiri Quran;font-size:15pt;'>%s</a></p>"
                          % (link, escape(header), link, quran_highlight(
                              verse["text"], self.mushaf_active_query,
                              highlight=self.mushaf_settings["highlight"])))
        if not matches:
            blocks.append("<p>%s</p>" % escape(tr(self.lang, "mushaf_no_results")))
        blocks.append("</body></html>")
        self.mushaf_results_browser.setHtml("".join(blocks))
        self.mushaf_results_dialog.show()
        self.mushaf_results_dialog.raise_()
        self.mushaf_results_dialog.activateWindow()

    def open_mushaf_result(self, url):
        try:
            _empty, page, number = url.path().split("/")
            target = int(page)
            self.show_mushaf_page(target)
            self.mushaf_selected_ayah = int(number)
            self.render_mushaf()
            self.mushaf_results_dialog.hide()
            self.showNormal()
            self.raise_()
            self.activateWindow()
        except (ValueError, IndexError):
            return

    def section(self, form, key):
        label = QLabel(tr(self.lang, key))
        label.setObjectName("Section")
        self.section_labels[key] = label
        form.addRow(label)

    def page_settings(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        panel = QFrame()
        panel.setObjectName("Panel")
        outer.addWidget(panel)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(26, 22, 26, 20)
        panel_layout.setSpacing(12)
        self.settings_title = QLabel()
        self.settings_title.setObjectName("Title")
        panel_layout.addWidget(self.settings_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        form = QFormLayout(body)
        form.setContentsMargins(0, 0, 12, 0)
        form.setSpacing(12)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        scroll.setWidget(body)
        panel_layout.addWidget(scroll, 1)

        # ---- location
        self.section(form, "location")
        self.country_combo = QComboBox()
        for key, value in COUNTRIES.items():
            self.country_combo.addItem(value[2 if self.lang == "en" else (1 if self.lang == "fr" else 0)], key)
        self.country_combo.setCurrentIndex(max(0, self.country_combo.findData(self.country)))
        self.country_combo.currentIndexChanged.connect(self.country_changed)
        form.addRow(self.row_label("country"), self.country_combo)

        self.city_combo = QComboBox()
        self.city_combo.currentIndexChanged.connect(self.city_changed)
        form.addRow(self.row_label("city"), self.city_combo)
        self.rebuild_cities()

        self.manual_check = QCheckBox()
        self.manual_check.setChecked(self.manual)
        self.manual_check.stateChanged.connect(self.manual_toggled)
        form.addRow(self.manual_check)

        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(5)
        self.lat_spin.setValue(self.lat)
        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setDecimals(5)
        self.lon_spin.setValue(self.lon)
        self.tz_edit = QLineEdit(self.tz_name)
        form.addRow(self.row_label("latitude"), self.lat_spin)
        form.addRow(self.row_label("longitude"), self.lon_spin)
        form.addRow(self.row_label("timezone"), self.tz_edit)

        self.auto_btn = QPushButton()
        self.auto_btn.clicked.connect(self.detect_location)
        form.addRow(self.auto_btn)

        # ---- calculation and display
        self.section(form, "sec_calc")
        self.method_combo = QComboBox()
        for method, label_key in METHODS:
            self.method_combo.addItem(tr(self.lang, label_key), method)
        self.method_combo.setCurrentIndex(max(0, self.method_combo.findData(self.method)))
        form.addRow(self.row_label("method"), self.method_combo)

        self.asr_combo = QComboBox()
        self.asr_combo.addItem(tr(self.lang, "standard"), "shafi")
        self.asr_combo.addItem(tr(self.lang, "hanafi"), "hanafi")
        self.asr_combo.setCurrentIndex(1 if self.madhab_hanafi else 0)
        form.addRow(self.row_label("asr_method"), self.asr_combo)

        self.hijri_spin = QSpinBox()
        self.hijri_spin.setRange(-2, 2)
        self.hijri_spin.setValue(self.hijri_adjust)
        form.addRow(self.row_label("hijri_adjust"), self.hijri_spin)

        self.theme_combo = QComboBox()
        for theme in ("dark", "light", "sepia", "night"):
            self.theme_combo.addItem("", theme)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self.app_theme)))
        self.theme_combo.currentIndexChanged.connect(self.theme_changed)
        form.addRow(self.row_label("theme"), self.theme_combo)

        self.hour12_check = QCheckBox()
        self.hour12_check.setChecked(not self.hour12)
        form.addRow(self.hour12_check)

        self.tune_button = QPushButton("⏱  " + tr(self.lang, "adjustments"))
        self.tune_button.clicked.connect(self.open_tune_dialog)
        form.addRow(self.row_label("adjustments"), self.tune_button)
        self.build_tune_dialog()

        # ---- adhan
        self.section(form, "sec_adhan")
        self.adhan_check = QCheckBox()
        self.adhan_check.setChecked(self.adhan_enabled)
        form.addRow(self.adhan_check)
        adhan_row = QHBoxLayout()
        self.adhan_edit = QLineEdit(self.adhan_path)
        self.adhan_browse = QPushButton()
        self.adhan_browse.clicked.connect(self.browse_adhan)
        self.adhan_test = QPushButton()
        self.adhan_test.clicked.connect(self.test_adhan)
        self.adhan_stop = QPushButton()
        self.adhan_stop.clicked.connect(self.stop_adhan)
        adhan_row.addWidget(self.adhan_edit, 1)
        adhan_row.addWidget(self.adhan_browse)
        adhan_row.addWidget(self.adhan_test)
        adhan_row.addWidget(self.adhan_stop)
        form.addRow(self.row_label("adhan_file"), adhan_row)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume)
        self.volume_slider.valueChanged.connect(self.volume_changed)
        form.addRow(self.row_label("adhan_volume"), self.volume_slider)

        # ---- notifications
        self.section(form, "sec_notify")
        self.notify_check = QCheckBox()
        self.notify_check.setChecked(self.notify_enabled)
        form.addRow(self.notify_check)
        self.hourly_check = QCheckBox()
        self.hourly_check.setChecked(self.hourly_enabled)
        form.addRow(self.hourly_check)
        self.hourly_interval_spin = QSpinBox()
        self.hourly_interval_spin.setRange(1, 12)
        self.hourly_interval_spin.setValue(self.hourly_interval)
        self.hourly_interval_spin.setSuffix(" h")
        form.addRow(self.row_label("hourly_interval"), self.hourly_interval_spin)
        self.hourly_test_btn = QPushButton()
        self.hourly_test_btn.clicked.connect(self.test_hourly_reminder)
        form.addRow(self.hourly_test_btn)
        self.notify_spin = QSpinBox()
        self.notify_spin.setRange(1, 60)
        self.notify_spin.setValue(self.notify_minutes)
        self.notify_spin.setSuffix(" min")
        form.addRow(self.row_label("notify_minutes"), self.notify_spin)
        self.name_edit = QLineEdit(self.user_name)
        form.addRow(self.row_label("user_name"), self.name_edit)

        self.save_button = QPushButton()
        self.save_button.setObjectName("Primary")
        self.save_button.clicked.connect(self.save)
        panel_layout.addWidget(self.save_button)

        # Live preview: results follow the widgets, "Save" only persists them.
        self.lat_spin.valueChanged.connect(self.schedule_refresh)
        self.lon_spin.valueChanged.connect(self.schedule_refresh)
        self.tz_edit.editingFinished.connect(self.schedule_refresh)
        self.method_combo.currentIndexChanged.connect(self.schedule_refresh)
        self.asr_combo.currentIndexChanged.connect(self.schedule_refresh)
        self.hijri_spin.valueChanged.connect(self.hijri_changed)
        self.hour12_check.toggled.connect(self.hour12_changed)
        self.apply_manual_state()
        return page

    def theme_changed(self, _index):
        self.app_theme = set_app_theme(self.theme_combo.currentData() or "dark")
        self.setStyleSheet(style_sheet(rtl=self.lang == "ar"))
        self.update()
        for compass in (getattr(self, "qibla_small", None), getattr(self, "qibla_big", None)):
            if compass is not None:
                compass.update()

    def schedule_refresh(self, *_args):
        self.refresh_timer.start()

    def refresh_all(self):
        self.recalculate()
        self.fill_monthly()
        self.fill_ramadan()
        self.fill_calendar()
        self.update_date_label()

    def hijri_changed(self, value):
        self.hijri_adjust = int(value)
        self.schedule_refresh()

    def hour12_changed(self, checked):
        self.hour12 = not checked
        self.schedule_refresh()

    def volume_changed(self, value):
        if self.audio_out is not None:
            self.audio_out.setVolume(max(0.0, min(1.0, value / 100.0)))

    def build_tune_dialog(self):
        """Minute adjustments live in their own window."""
        self.tune_dialog = QDialog(self)
        self.tune_dialog.setMinimumSize(560, 420)
        self.tune_dialog.resize(600, 440)
        layout = QVBoxLayout(self.tune_dialog)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)
        self.tune_title_label = QLabel("⏱  " + tr(self.lang, "adjustments"))
        self.tune_title_label.setObjectName("Title")
        layout.addWidget(self.tune_title_label)
        self.tune_note_label = QLabel(tr(self.lang, "tune_note"))
        self.tune_note_label.setObjectName("Muted")
        self.tune_note_label.setWordWrap(True)
        layout.addWidget(self.tune_note_label)
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(16)
        self.tune_spins = {}
        self.tune_labels = {}
        for index, key in enumerate(PRAYER_KEYS):
            label = QLabel(tr(self.lang, key))
            label.setObjectName("Muted")
            spin = QSpinBox()
            spin.setRange(-30, 30)
            spin.setValue(self.tune.get(key, 0))
            spin.setSuffix(" min")
            spin.setMinimumWidth(140)
            self.tune_labels[key] = label
            self.tune_spins[key] = spin
            grid.addWidget(label, index // 2, (index % 2) * 2)
            grid.addWidget(spin, index // 2, (index % 2) * 2 + 1)
        layout.addLayout(grid)
        layout.addStretch(1)
        buttons = QHBoxLayout()
        self.tune_reset_btn = QPushButton("↺  " + tr(self.lang, "reset"))
        self.tune_reset_btn.clicked.connect(self.reset_tune)
        self.tune_close_btn = QPushButton(tr(self.lang, "apply"))
        self.tune_close_btn.setObjectName("Primary")
        self.tune_close_btn.clicked.connect(self.tune_dialog.accept)
        buttons.addWidget(self.tune_reset_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.tune_close_btn)
        layout.addLayout(buttons)

    def reset_tune(self):
        for spin in self.tune_spins.values():
            spin.setValue(0)

    def open_tune_dialog(self):
        """Adjustments are applied only when the dialog is confirmed; closing it discards edits."""
        self.tune_dialog.setWindowTitle(tr(self.lang, "adjustments"))
        for key, spin in self.tune_spins.items():
            spin.setValue(self.tune.get(key, 0))
        if self.tune_dialog.exec():  # non-zero means Accepted
            self.tune = {key: spin.value() for key, spin in self.tune_spins.items()}
            self.write_config()
            self.refresh_all()

    def page_about(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = QFrame()
        panel.setObjectName("Panel")
        layout.addWidget(panel)
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(30, 34, 30, 30)
        inner.setSpacing(9)

        def centered(label, object_name):
            label.setObjectName(object_name)
            label.setAlignment(Qt.AlignCenter)
            return label

        self.about_brand = centered(QLabel("☾  " + tr(self.lang, "app")), "Brand")
        self.about_brand.setStyleSheet("font-size: 42px;")
        self.about_sub = centered(QLabel(tr(self.lang, "subtitle") + "   ·   v" + APP_VERSION), "Sub")
        stars = centered(QLabel("✦     ✦     ✦"), "Muted")
        stars.setStyleSheet("font-size: 16px; color: %s;" % COLORS["gold"])
        inner.addWidget(self.about_brand)
        inner.addWidget(self.about_sub)
        inner.addSpacing(14)
        inner.addWidget(stars)
        inner.addSpacing(12)
        self.about_made = centered(QLabel(tr(self.lang, "made_by")), "CreditLine")
        self.about_name = centered(QLabel("أنور   ·   Anouar"), "CreditName")
        self.about_handle = centered(QLabel("TikTok      ·      @Ianouar3G"), "CreditLine")
        self.about_youtube = centered(QLabel("▶   youtube.com/@YounesTaoutaou-g2n"), "CreditLink")
        self.about_tiktok = centered(QLabel("♪   tiktok.com/@Ianouar3G"), "CreditLink")
        inner.addWidget(self.about_made)
        inner.addWidget(self.about_name)
        inner.addWidget(self.about_handle)
        inner.addSpacing(8)
        inner.addWidget(self.about_youtube)
        inner.addWidget(self.about_tiktok)
        inner.addSpacing(18)
        self.about_luck = centered(QLabel("♡   " + tr(self.lang, "good_luck") + "   ♡"), "CreditLine")
        self.about_luck.setStyleSheet("font-size: 18px; color: %s;" % COLORS["gold2"])
        inner.addWidget(self.about_luck)
        inner.addStretch(1)
        self.about_footer = centered(QLabel(tr(self.lang, "footer")), "Muted")
        self.about_footer.setWordWrap(True)
        inner.addWidget(self.about_footer)
        inner.addSpacing(14)
        self.exit_program_button = QPushButton()
        self.exit_program_button.setObjectName("Primary")
        self.exit_program_button.clicked.connect(self.really_quit)
        inner.addWidget(self.exit_program_button)
        return page

    def row_label(self, key):
        label = QLabel(tr(self.lang, key))
        label.setObjectName("Muted")
        self.row_labels[key] = label
        return label

    def show_page(self, key):
        mapping = {"today": 0, "monthly": 1, "ramadan": 2, "calendar": 3, "qibla": 4, "education": 5, "adhkar": 6, "prayer_log": 7, "settings": 8, "about": 9, "quran": 10, "mushaf": 11}
        self.pages.setCurrentIndex(mapping[key])
        for name, button in self.nav_buttons.items():
            button.setChecked(name == key)

    # ---------------- language
    def apply_language(self):
        for key, value in COUNTRIES.items():
            index = self.country_combo.findData(key)
            if index >= 0:
                self.country_combo.setItemText(index, value[0 if self.lang == "ar" else (1 if self.lang == "fr" else 2)])
        self.rebuild_cities()
        # Signals are blocked so rebuilding the lists does not trigger a recalculation.
        index = self.method_combo.currentIndex()
        self.method_combo.blockSignals(True)
        self.method_combo.clear()
        for method, label_key in METHODS:
            self.method_combo.addItem(tr(self.lang, label_key), method)
        self.method_combo.setCurrentIndex(max(0, index))
        self.method_combo.blockSignals(False)
        current = self.asr_combo.currentData() or "shafi"
        self.asr_combo.blockSignals(True)
        self.asr_combo.clear()
        self.asr_combo.addItem(tr(self.lang, "standard"), "shafi")
        self.asr_combo.addItem(tr(self.lang, "hanafi"), "hanafi")
        self.asr_combo.setCurrentIndex(0 if current == "shafi" else 1)
        self.asr_combo.blockSignals(False)

        self.brand.setText("☾  " + tr(self.lang, "app"))
        self.subtitle.setText(tr(self.lang, "subtitle"))
        icons = {"today": "⌂  ", "monthly": "▦  ", "ramadan": "☾  ", "calendar": "✦  ",
                 "qibla": "◈  ", "education": "📚  ", "adhkar": "☷  ", "prayer_log": "✓  ", "quran": "♫  ", "mushaf": "▤  ", "settings": "⚙  ", "about": "ⓘ  "}
        for key, button in self.nav_buttons.items():
            button.setText(icons.get(key, "") + tr(self.lang, key))
        self.lang_combo.setToolTip(tr(self.lang, "language"))
        self.title_label.setText(tr(self.lang, "today"))
        self.next_label.setText(tr(self.lang, "next"))
        self.remaining_label.setText(tr(self.lang, "remaining"))
        self.monthly_title.setText(tr(self.lang, "monthly"))
        self.m_year_label.setText(tr(self.lang, "gregorian_year"))
        self.m_month_label.setText(tr(self.lang, "month"))
        self.export_pdf_btn.setText("🖨 " + tr(self.lang, "monthly") + " PDF")
        self.ramadan_title.setText(tr(self.lang, "ramadan"))
        self.r_year_label.setText(tr(self.lang, "hijri_year"))
        self.export_ramadan_btn.setText("🖨 PDF")
        self.calendar_title.setText(tr(self.lang, "calendar"))
        self.c_year_label.setText(tr(self.lang, "gregorian_year"))
        self.qibla_title.setText(tr(self.lang, "qibla"))
        self.education_title.setText(tr(self.lang, "education"))
        self.education_hint.setText(tr(self.lang, "education_hint"))
        self.adhkar_title.setText(tr(self.lang, "adhkar"))
        self.adhkar_hint.setText(tr(self.lang, "adhkar_hint"))
        self.adhkar_category_label.setText(tr(self.lang, "adhkar_category"))
        self.adhkar_search.setPlaceholderText(tr(self.lang, "adhkar_search"))
        self.adhkar_copy_button.setText(tr(self.lang, "adhkar_copy"))
        self.adhkar_reset_button.setText(tr(self.lang, "adhkar_reset"))
        self.adhkar_repeat_button.setText(tr(self.lang, "repeat_button") + ("  (" + str(getattr(self, "adhkar_counter", 0)) + ")" if getattr(self, "adhkar_counter", 0) else ""))
        self.prayer_log_title.setText(tr(self.lang, "prayer_log"))
        self.prayer_log_hint.setText(tr(self.lang, "prayer_log_hint"))
        self.prayer_log_date.setText(datetime.now(self.tz).strftime("%Y-%m-%d"))
        for key, check in self.prayer_checks.items():
            check.setText(tr(self.lang, key))
        self.update_prayer_log_progress()
        self.prayer_guide_label.setText(tr(self.lang, "prayer_guide"))
        self.wudu_guide_label.setText(tr(self.lang, "wudu_guide"))
        self.update_education_content()
        self.qibla_hint.setText(tr(self.lang, "qibla_hint"))
        self.quran_title.setText("☾  " + tr(self.lang, "quran"))
        self.quran_hint.setText(tr(self.lang, "quran_hint"))
        self.quran_reciter_label.setText(tr(self.lang, "quran_reciter"))
        self.quran_play_button.setText("▶  " + tr(self.lang, "quran_play"))
        self.quran_pause_button.setText("Ⅱ  " + tr(self.lang, "quran_pause"))
        self.quran_stop_button.setText("■  " + tr(self.lang, "quran_stop"))
        if not self.quran_player or self.quran_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.quran_status.setText(tr(self.lang, "quran_ready"))
        self.mushaf_title.setText("۞  " + tr(self.lang, "mushaf"))
        self.mushaf_hint.setText(tr(self.lang, "mushaf_hint"))
        self.mushaf_surah_label.setText(tr(self.lang, "mushaf_surah"))
        self.mushaf_page_label.setText(tr(self.lang, "mushaf_page"))
        self.mushaf_previous_button.setText(tr(self.lang, "mushaf_prev"))
        self.mushaf_next_button.setText(tr(self.lang, "mushaf_next"))
        self.mushaf_search_edit.setPlaceholderText(tr(self.lang, "mushaf_search"))
        self.mushaf_search_button.setText(tr(self.lang, "mushaf_find"))
        self.mushaf_settings_button.setText("⚙  " + tr(self.lang, "mushaf_settings"))
        self.mushaf_settings_dialog.setWindowTitle(tr(self.lang, "mushaf_settings"))
        self.mushaf_settings_title.setText(tr(self.lang, "mushaf_settings"))
        self.mushaf_results_dialog.setWindowTitle(tr(self.lang, "mushaf_results"))
        self.mushaf_spread_check.setText(tr(self.lang, "mushaf_spread"))
        self.mushaf_reset_button.setText(tr(self.lang, "mushaf_reset"))
        self.mushaf_cancel_button.setText(tr(self.lang, "close"))
        self.mushaf_save_button.setText(tr(self.lang, "mushaf_save"))
        for key, label in self.mushaf_setting_labels.items():
            label.setText(tr(self.lang, key))
        for index in range(self.mushaf_theme_combo.count()):
            key = "mushaf_theme_" + self.mushaf_theme_combo.itemData(index)
            self.mushaf_theme_combo.setItemText(index, tr(self.lang, key))
        self.mushaf_return_button.setText(tr(self.lang, "mushaf_back"))
        self.mushaf_results_label.setText(tr(self.lang, "mushaf_results"))
        self.render_mushaf()
        self.settings_title.setText(tr(self.lang, "settings"))
        self.manual_check.setText(tr(self.lang, "custom_location"))
        self.auto_btn.setText("📍 " + tr(self.lang, "auto_location"))
        self.adhan_check.setText(tr(self.lang, "adhan_enable"))
        self.adhan_browse.setText(tr(self.lang, "adhan_browse"))
        self.adhan_test.setText(tr(self.lang, "adhan_test"))
        self.adhan_stop.setText(tr(self.lang, "adhan_stop"))
        self.notify_check.setText(tr(self.lang, "notify_enable"))
        self.hourly_check.setText(tr(self.lang, "hourly_reminder"))
        self.hourly_test_btn.setText("▶  " + tr(self.lang, "hourly_test"))
        self.save_button.setText(tr(self.lang, "save"))
        self.tune_button.setText("⏱  " + tr(self.lang, "adjustments"))
        self.tune_dialog.setWindowTitle(tr(self.lang, "adjustments"))
        self.tune_title_label.setText("⏱  " + tr(self.lang, "adjustments"))
        self.tune_note_label.setText(tr(self.lang, "tune_note"))
        self.tune_reset_btn.setText("↺  " + tr(self.lang, "reset"))
        self.tune_close_btn.setText(tr(self.lang, "apply"))
        for key, label in self.tune_labels.items():
            label.setText(tr(self.lang, key))
        self.about_brand.setText("☾  " + tr(self.lang, "app"))
        self.about_sub.setText(tr(self.lang, "subtitle"))
        self.about_made.setText(tr(self.lang, "made_by"))
        self.about_luck.setText("♡   " + tr(self.lang, "good_luck") + "   ♡")
        self.about_footer.setText(tr(self.lang, "footer"))
        self.exit_program_button.setText("⏻  " + tr(self.lang, "exit_program"))
        for key in PRAYER_KEYS:
            if key in self.cards:
                self.cards[key][1].setText(tr(self.lang, key))
        for key, spin in self.tune_spins.items():
            spin.setToolTip(tr(self.lang, "tune_note"))
        for key, label in self.row_labels.items():
            label.setText(tr(self.lang, key))
        theme_labels = {"dark": "theme_dark", "light": "theme_light", "sepia": "theme_sepia", "night": "theme_night"}
        for index in range(self.theme_combo.count()):
            self.theme_combo.setItemText(index, tr(self.lang, theme_labels[self.theme_combo.itemData(index)]))
        for key, label in self.section_labels.items():
            label.setText(tr(self.lang, key))
        self.hour12_check.setText(tr(self.lang, "clock_24"))
        self.ramadan_note.setText(tr(self.lang, "hijri_note"))
        self.calendar_note.setText(tr(self.lang, "hijri_note"))
        if hasattr(self, "tray_show_action"):
            self.tray_show_action.setText(tr(self.lang, "open_nour"))
            self.tray_quit_action.setText(tr(self.lang, "quit"))
        self.setWindowTitle(APP_NAME + " v" + APP_VERSION + " - " + tr(self.lang, "subtitle"))
        # Set on the application so dialogs and message boxes follow the language too
        # (a widget-level setLayoutDirection does not reach top-level dialogs).
        try:
            QApplication.instance().setLayoutDirection(
                Qt.LayoutDirection.RightToLeft if self.lang == "ar" else Qt.LayoutDirection.LeftToRight)
        except Exception as exc:
            print("layout direction failed:", exc)
        self.setStyleSheet(style_sheet(rtl=self.lang == "ar"))
        self.update_date_label()
        self.fill_monthly()
        self.fill_ramadan()
        self.fill_calendar()

    def language_changed(self):
        self.lang = self.lang_combo.currentData() or "ar"
        self.apply_language()
        self.recalculate()
        self.write_config()

    # ---------------- location
    def rebuild_cities(self):
        self.city_combo.blockSignals(True)
        self.city_combo.clear()
        index = 0 if self.lang == "ar" else (1 if self.lang == "fr" else 2)
        for code, ar, fr, _lat, _lon in COUNTRIES[self.country][4]:
            if index == 0:
                label = ar
            elif index == 1:
                label = fr
            else:
                label = EN_CITY.get(code, fr)
            self.city_combo.addItem(label, code)
        found = self.city_combo.findData(self.city)
        self.city_combo.setCurrentIndex(max(0, found))
        self.city = self.city_combo.currentData() or self.city
        self.city_combo.blockSignals(False)

    def country_changed(self):
        self.country = self.country_combo.currentData() or "algeria"
        self.city = COUNTRIES[self.country][4][0][0]
        self.rebuild_cities()
        self.manual_check.setChecked(False)
        self.manual_toggled()

    def city_changed(self):
        if self.manual_check.isChecked():
            return
        self.city = self.city_combo.currentData()
        entry = self.city_entry()
        if entry:
            self.lat_spin.setValue(entry[1])
            self.lon_spin.setValue(entry[2])
            self.tz_edit.setText(CITY_TZ.get(entry[0], COUNTRIES[self.country][3]))
            self.recalculate()

    def city_entry(self):
        for code, _ar, _fr, lat, lon in COUNTRIES[self.country][4]:
            if code == self.city:
                return (code, lat, lon)
        return None

    def apply_manual_state(self):
        """Manual mode edits coordinates by hand; otherwise the city list drives them."""
        manual = self.manual_check.isChecked()
        for widget in (self.lat_spin, self.lon_spin, self.tz_edit):
            widget.setEnabled(manual)
        self.city_combo.setEnabled(not manual)

    def manual_toggled(self, *_args):
        self.apply_manual_state()
        if not self.manual_check.isChecked():
            self.city_changed()
        else:
            self.recalculate()

    def zone(self):
        name = self.tz_edit.text().strip() if hasattr(self, "tz_edit") else self.tz_name
        for candidate in (name, self.tz_name, "UTC"):
            try:
                return ZoneInfo(candidate or "UTC")
            except (ZoneInfoNotFoundError, ValueError, OSError):
                continue
        return timezone.utc

    def detect_location(self):
        if self.loc_worker is not None and self.loc_worker.isRunning():
            return
        self.auto_btn.setEnabled(False)
        self.auto_btn.setText(tr(self.lang, "locating"))
        self.loc_worker = LocationWorker(self)
        self.loc_worker.result_ready.connect(self.location_done)
        self.loc_worker.start()

    def location_done(self, data, error):
        self.auto_btn.setEnabled(True)
        self.auto_btn.setText("📍 " + tr(self.lang, "auto_location"))
        if not data:
            print("detect failed:", error)
            self.say(tr(self.lang, "location_error"))
            return
        try:
            self.manual_check.setChecked(True)
            self.lat_spin.setValue(float(data["latitude"]))
            self.lon_spin.setValue(float(data["longitude"]))
            zone = data.get("timezone")
            if isinstance(zone, dict):
                zone = zone.get("id")
            if valid_zone(str(zone or "")):
                self.tz_edit.setText(str(zone))
            self.recalculate()
            self.say(tr(self.lang, "location_ok"))
        except (KeyError, TypeError, ValueError) as exc:
            print("detect failed:", exc)
            self.say(tr(self.lang, "location_error"))

    # ---------------- calculation
    def current_coords(self):
        lat = self.lat_spin.value() if hasattr(self, "lat_spin") else self.lat
        lon = self.lon_spin.value() if hasattr(self, "lon_spin") else self.lon
        if Coordinates is not None:
            try:
                return Coordinates(lat, lon)
            except Exception:
                pass
        return (lat, lon)

    def params(self):
        name = self.method_combo.currentData() if hasattr(self, "method_combo") else self.method
        member = getattr(CalculationMethod, name or "MUSLIM_WORLD_LEAGUE", None)
        if member is None:
            member = CalculationMethod.MUSLIM_WORLD_LEAGUE
        # CalculationMethod is an enum, not a parameters factory. PrayerTimes
        # needs CalculationParameters for night_portions() and the twilight angles.
        parameters = CalculationParameters(method=member)
        hanafi = hasattr(self, "asr_combo") and self.asr_combo.currentData() == "hanafi"
        hanafi_value = getattr(Madhab, "HANAFI", None)
        if hanafi_value is None:
            hanafi_value = getattr(Madhab, "Hanafi", None)
        shafi_value = getattr(Madhab, "SHAFI", None)
        if shafi_value is None:
            shafi_value = getattr(Madhab, "Shafi", None)
        if hanafi_value is not None and shafi_value is not None:
            parameters.madhab = hanafi_value if hanafi else shafi_value
        return parameters

    def compute_day(self, day):
        if not ADHANPY:
            return {}
        tz = self.zone()
        coordinates = self.current_coords()
        parameters = self.params()
        try:
            try:
                prayers = PrayerTimes(coordinates, day, calculation_parameters=parameters, time_zone=tz)
            except TypeError:
                # older adhanpy builds without the time_zone keyword
                prayers = PrayerTimes(coordinates, day, calculation_parameters=parameters)
        except Exception as exc:
            print("calc error:", exc)
            return {}
        result = {}
        for key in PRAYER_KEYS:
            value = getattr(prayers, key, None)
            if value is None:
                continue
            if value.tzinfo is None:
                value = value.replace(tzinfo=tz)
            offset = self.tune.get(key, 0)
            if offset:
                value = value + timedelta(minutes=offset)
            result[key] = value
        return result

    def to_hijri(self, day):
        """Hijri date of a datetime.date, shifted by the user's adjustment."""
        day = day + timedelta(days=self.hijri_adjust)
        return gregorian_to_hijri(day.year, day.month, day.day)

    def from_hijri(self, hy, hm, hd):
        return hijri_to_gregorian(hy, hm, hd) - timedelta(days=self.hijri_adjust)

    def recalculate(self):
        self.calc_date = datetime.now(self.zone()).date()
        if not ADHANPY:
            self.say(tr(self.lang, "install_missing"), 0)
            return
        try:
            self.tz = self.zone()
            self.lat = self.lat_spin.value() if hasattr(self, "lat_spin") else self.lat
            self.lon = self.lon_spin.value() if hasattr(self, "lon_spin") else self.lon
            today = datetime.now(self.tz).date()
            self.times = {(today + timedelta(days=offset)).isoformat(): self.compute_day(today + timedelta(days=offset))
                          for offset in (0, 1)}
            if not self.times.get(today.isoformat()):
                self._calc_failed = True
                self.say(tr(self.lang, "calc_error"), 0)
            elif self._calc_failed:
                self._calc_failed = False
                self.statusBar().clearMessage()
            bearing = qibla_bearing(self.lat, self.lon)
            self.qibla_small.set_bearing(bearing)
            self.qibla_big.set_bearing(bearing)
            self.qibla_deg.setText("%.1f° %s" % (bearing, tr(self.lang, "qibla_from_north")))
            self.qibla_big_deg.setText("%.1f°" % bearing)
            self.distance_label.setText("%s: %s %s" % (tr(self.lang, "distance"),
                                                       format(distance_km(self.lat, self.lon), ","),
                                                       tr(self.lang, "km")))
            self.update_date_label()
            self.update_cards()
            self.update_next()
        except Exception as exc:
            self.say(tr(self.lang, "calc_error") + ": " + str(exc), 0)

    def update_date_label(self):
        now = datetime.now(self.tz)
        hy, hm, hd = self.to_hijri(now.date())
        self.date_label.setText("%s  |  %s" % (now.strftime("%Y-%m-%d"), format_hijri(hy, hm, hd, self.lang)))

    def fmt(self, value):
        if not value:
            return "--:--"
        if self.hour12 and self.lang != "fr":
            text = value.strftime("%I:%M %p").lstrip("0")
            if self.lang == "ar":
                text = text.replace("AM", "ص").replace("PM", "م")
            return text
        return value.strftime("%H:%M")

    def update_cards(self):
        today = datetime.now(self.tz).date().isoformat()
        for key in PRAYER_KEYS:
            value = self.times.get(today, {}).get(key)
            self.cards[key][2].setText(self.fmt(value))

    def update_next(self):
        now = datetime.now(self.tz)
        today = now.date().isoformat()
        candidates = []
        for key in ADHAN_KEYS:
            value = self.times.get(today, {}).get(key)
            if value and value > now:
                candidates.append((value, key))
        if not candidates:
            tomorrow = (now.date() + timedelta(days=1)).isoformat()
            value = self.times.get(tomorrow, {}).get("fajr")
            if value:
                candidates.append((value, "fajr"))
        if not candidates:
            self.next_value.setText(tr(self.lang, "no_next"))
            self.target = None
            self.highlight_cards(None)
            return
        self.target, self.target_key = min(candidates, key=lambda item: item[0])
        self.next_value.setText(tr(self.lang, self.target_key) + "  ·  " + self.fmt(self.target))
        self.highlight_cards(self.target_key)

    def fmt_clock(self, now):
        if self.hour12 and self.lang != "fr":
            text = now.strftime("%I:%M:%S %p").lstrip("0")
            if self.lang == "ar":
                text = text.replace("AM", "ص").replace("PM", "م")
            return text
        return now.strftime("%H:%M:%S")

    def test_hourly_reminder(self):
        now = datetime.now(self.tz)
        self.notify_text(tr(self.lang, "hourly_title"), self.hourly_reminder_text(now.hour))

    def hourly_reminder_text(self, hour):
        messages = HOURLY_REMINDERS.get(self.lang, HOURLY_REMINDERS["en"])
        return messages[hour % len(messages)]

    def notify_text(self, title, message):
        self.say(message, 10000)
        if TRAY is not None and TRAY.isVisible():
            TRAY.showMessage(title, message, tray_info_icon(), 10000)
        else:
            print("[NOUR]", title, message)

    def tick(self):
        now = datetime.now(self.tz)
        self.clock_label.setText(self.fmt_clock(now))
        hourly_stamp = (now.date().isoformat(), now.hour)
        interval = self.hourly_interval_spin.value() if hasattr(self, "hourly_interval_spin") else self.hourly_interval
        if (self.hourly_check.isChecked() and now.minute == 0 and now.second < 2
                and now.hour % max(1, interval) == 0 and hourly_stamp != self.last_hourly):
            self.last_hourly = hourly_stamp
            self.notify_text(tr(self.lang, "hourly_title"), self.hourly_reminder_text(now.hour))
        if self.calc_date != now.date():
            self.recalculate()  # a new day started: compute today and tomorrow again
        if not self.target:
            if now.second == 0:
                self.update_next()
            return
        seconds = int((self.target - now).total_seconds())
        hours, rest = divmod(max(0, seconds), 3600)
        minutes, secs = divmod(rest, 60)
        self.countdown.setText("%02d:%02d:%02d" % (hours, minutes, secs))
        stamp = (self.target.date().isoformat(), self.target_key)
        if 0 < seconds <= self.notify_spin.value() * 60 and self.notify_check.isChecked() and stamp != self.last_notify:
            self.last_notify = stamp
            self.notify(tr(self.lang, "notify_body"), False)
        if seconds <= 0:
            if stamp != self.last_adhan:
                self.last_adhan = stamp
                if seconds > -120:  # do not play a stale adhan after the computer woke from sleep
                    self.notify(tr(self.lang, "notify_now"), True)
            self.recalculate()

    def notify(self, template, play):
        name = self.name_edit.text().strip()
        if not name:
            for fragment in (" يا {name}", ", {name}", "{name}"):
                template = template.replace(fragment, "")
        message = template.replace("{name}", name).replace("{prayer}", tr(self.lang, self.target_key))
        self.say(message, 15000)
        if TRAY is not None and TRAY.isVisible():
            TRAY.showMessage(tr(self.lang, "notify_title"), message, tray_info_icon(), 10000)
        else:
            print("[NOUR]", message)
        if play and self.adhan_check.isChecked():
            self.play_adhan()
        elif play:
            QApplication.beep()

    # ---------------- adhan
    def resolve_adhan(self):
        custom = self.adhan_edit.text().strip() if hasattr(self, "adhan_edit") else self.adhan_path
        for path in ([Path(custom)] if custom else []) + ADHAN_CANDIDATES:
            try:
                if path.is_file():
                    return path
            except Exception:
                continue
        return None

    def play_adhan(self):
        path = self.resolve_adhan()
        if path is None:
            self.say(tr(self.lang, "adhan_missing"))
            return
        if self.player is None:
            QApplication.beep()
            return
        try:
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
            self.player.play()
            self.say(tr(self.lang, "adhan_playing") + " (" + path.name + ")")
        except Exception as exc:
            print("play failed:", exc)

    def stop_adhan(self):
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass
        self.statusBar().clearMessage()

    def test_adhan(self):
        self.play_adhan()

    def browse_adhan(self):
        path, _ = QFileDialog.getOpenFileName(self, tr(self.lang, "adhan_file"), str(APP_DIR),
                                              "Audio (*.mp3 *.wav *.ogg *.m4a)")
        if path:
            self.adhan_edit.setText(path)

    # ---------------- tables
    def make_item(self, text, today=False):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if today:
            item.setBackground(QColor(COLORS["green"]))
            item.setForeground(QColor(COLORS["gold2"]))
        return item

    def fill_monthly(self):
        if not hasattr(self, "monthly_table"):
            return
        year, month = self.m_year.value(), self.m_month.value()
        headers = ["#", tr(self.lang, "hijri_date")] + [tr(self.lang, key) for key in PRAYER_KEYS]
        self.monthly_table.setColumnCount(2 + len(PRAYER_KEYS))
        self.monthly_table.setHorizontalHeaderLabels(headers)
        days = (date(year + (month == 12), 1 if month == 12 else month + 1, 1) - date(year, month, 1)).days
        self.monthly_table.setRowCount(days)
        today = datetime.now(self.tz).date()
        for day in range(1, days + 1):
            current = date(year, month, day)
            times = self.compute_day(current)
            hy, hm, hd = self.to_hijri(current)
            values = [str(day), format_hijri(hy, hm, hd, self.lang)] + [self.fmt(times.get(key)) for key in PRAYER_KEYS]
            for column, value in enumerate(values):
                self.monthly_table.setItem(day - 1, column, self.make_item(value, current == today))

    def fill_ramadan(self):
        if not hasattr(self, "ramadan_table"):
            return
        hy = self.r_year.value()
        start = self.from_hijri(hy, 9, 1)
        end = self.from_hijri(hy, 10, 1)
        days = (end - start).days
        self.ramadan_table.setColumnCount(4)
        self.ramadan_table.setHorizontalHeaderLabels([tr(self.lang, "hijri_date"), tr(self.lang, "gregorian_date"),
                                                      tr(self.lang, "suhoor"), tr(self.lang, "iftar")])
        self.ramadan_table.setRowCount(days)
        now = datetime.now(self.tz)
        today = now.date()
        is_ramadan = self.to_hijri(today)[1] == 9
        self.ramadan_status.setText(tr(self.lang, "ramadan_now") if is_ramadan else tr(self.lang, "ramadan_not_now"))
        for day in range(1, days + 1):
            current = self.from_hijri(hy, 9, day)
            times = self.compute_day(current)
            values = [tr(self.lang, "ramadan_day", day=day), current.strftime("%Y-%m-%d"),
                      self.fmt(times.get("fajr")), self.fmt(times.get("maghrib"))]
            for column, value in enumerate(values):
                self.ramadan_table.setItem(day - 1, column, self.make_item(value, current == today))

    def fill_calendar(self):
        if not hasattr(self, "calendar_table"):
            return
        year = self.c_year.value()
        self.calendar_table.setRowCount(0)
        for offset in range(-1, 2):
            hy = self.to_hijri(date(year, 6, 15))[0] + offset
            for day, month, key in EVENTS:
                current = self.from_hijri(hy, month, day)
                if current.year != year:
                    continue
                row = self.calendar_table.rowCount()
                self.calendar_table.insertRow(row)
                for column, value in enumerate([tr(self.lang, key), format_hijri(hy, month, day, self.lang),
                                                current.strftime("%Y-%m-%d")]):
                    self.calendar_table.setItem(row, column, self.make_item(value))

    def column_widths(self, cols):
        """Percentage widths that always sum to 100."""
        if cols >= 8:
            return ["5", "17", "13", "13", "13", "13", "13", "13"]
        if cols == 4:
            return ["26", "26", "24", "24"]
        return ["36", "32", "32"]

    def table_to_html(self, table, title, subtitle=""):
        """Qt's rich-text engine ignores modern CSS (cell padding, th background,
        colgroup) - so this builds old-school attribute-based HTML that it honours,
        and the table stretches across the whole page."""
        cols = table.columnCount()
        widths = self.column_widths(cols)
        head_cells = []
        for c in range(cols):
            item = table.horizontalHeaderItem(c)
            text = (item.text() if item else "").replace("&", "&amp;").replace("<", "&lt;")
            head_cells.append(
                '<th bgcolor="#d8b66a" width="%s%%" align="center">'
                "<font color='#12201b'><b>&nbsp;%s&nbsp;</b></font></th>" % (widths[c], text)
            )
        rows = []
        for r in range(table.rowCount()):
            cells = []
            bg = ' bgcolor="#eef3f0"' if r % 2 else ""
            for c in range(cols):
                item = table.item(r, c)
                text = (item.text() if item else "").replace("&", "&amp;").replace("<", "&lt;")
                cells.append('<td align="center"%s>&nbsp;%s&nbsp;</td>' % (bg, text))
            rows.append("<tr>%s</tr>" % "".join(cells))
        direction = "rtl" if self.lang == "ar" else "ltr"
        sub = (
            "<p align='center'><font size='3' color='#4a5a52'>%s</font></p>" % subtitle
            if subtitle
            else ""
        )
        return (
            "<html><body dir='%s'>"
            "<h1 align='center'><font size='6' color='#12201b'>%s</font></h1>%s"
            "<table width='100%%' border='1' cellspacing='0' cellpadding='9'>"
            "<tr>%s</tr>%s</table>"
            "</body></html>"
            % (direction, title, sub, "".join(head_cells), "".join(rows))
        )

    def current_subtitle(self):
        country = COUNTRIES.get(self.country)
        city_entry = self.city_entry()
        index = 0 if self.lang == "ar" else (1 if self.lang == "fr" else 2)
        city_label = ""
        if country:
            for code, ar, fr, _lat, _lon in country[4]:
                if code == self.city:
                    city_label = (ar, fr, EN_CITY.get(code, fr))[index]
                    break
        method_label = self.method_combo.currentText() if hasattr(self, "method_combo") else self.method
        return "%s  ·  %s  ·  %s  ·  %s" % (
            country[index] if country else "", city_label, method_label,
            (self.tz_edit.text().strip() if hasattr(self, "tz_edit") else self.tz_name),
        )

    def export_table(self, table, title, default_name, subtitle=""):
        path, _ = QFileDialog.getSaveFileName(self, "PDF", str(APP_DIR / default_name), "PDF (*.pdf)")
        if not path:
            return
        try:
            from PySide6.QtGui import QTextDocument
            from PySide6.QtPrintSupport import QPrinter
            # Enum locations moved between PySide6 releases - accept either form.
            mode = getattr(QPrinter, "HighResolution", None)
            if mode is None:
                mode = QPrinter.PrinterMode.HighResolution
            pdf = getattr(QPrinter, "PdfFormat", None)
            if pdf is None:
                pdf = QPrinter.OutputFormat.PdfFormat
            printer = QPrinter(mode)
            printer.setOutputFormat(pdf)
            printer.setOutputFileName(path)
            document = QTextDocument()
            document.setDefaultFont(QFont("Segoe UI", 11))
            document.setHtml(self.table_to_html(table, title, subtitle))
            document.print_(printer)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))

    def export_monthly(self):
        self.export_table(
            self.monthly_table,
            "%s %d-%02d" % (tr(self.lang, "monthly"), self.m_year.value(), self.m_month.value()),
            "nour-monthly.pdf",
            self.current_subtitle(),
        )

    def export_ramadan(self):
        self.export_table(
            self.ramadan_table,
            "%s %d" % (tr(self.lang, "ramadan"), self.r_year.value()),
            "nour-ramadan.pdf",
            self.current_subtitle(),
        )

    # ---------------- settings
    def write_config(self):
        """Collect the current settings and store them on disk (no dialogs)."""
        self.city = self.city_combo.currentData() or self.city
        self.method = self.method_combo.currentData() or self.method
        self.madhab_hanafi = self.asr_combo.currentData() == "hanafi"
        self.manual = self.manual_check.isChecked()
        self.lat = self.lat_spin.value()
        self.lon = self.lon_spin.value()
        zone_text = self.tz_edit.text().strip()
        if valid_zone(zone_text):
            self.tz_name = zone_text
        self.adhan_enabled = self.adhan_check.isChecked()
        self.adhan_path = self.adhan_edit.text().strip()
        self.volume = self.volume_slider.value()
        self.notify_enabled = self.notify_check.isChecked()
        self.hourly_enabled = self.hourly_check.isChecked()
        self.hourly_interval = self.hourly_interval_spin.value()
        self.notify_minutes = self.notify_spin.value()
        self.user_name = self.name_edit.text().strip()
        save_config({
            "language": self.lang, "theme": self.app_theme, "country": self.country, "city": self.city, "method": self.method,
            "hanafi": self.madhab_hanafi, "manual": self.manual, "lat": self.lat, "lon": self.lon,
            "tz": self.tz_name, "adhan_enabled": self.adhan_enabled, "adhan_path": self.adhan_path,
            "volume": self.volume, "notify_enabled": self.notify_enabled,
            "hourly_enabled": self.hourly_enabled, "hourly_interval": self.hourly_interval,
            "notify_minutes": self.notify_minutes, "user_name": self.user_name,
            "prayer_log": self.prayer_log,
            "hour12": self.hour12, "tune": self.tune, "hijri_adjust": self.hijri_adjust,
            "quran_surah": max(0, self.quran_list.currentRow()),
            "quran_reciter": max(0, self.quran_reciter.currentIndex()),
        })

    def save(self):
        if not valid_zone(self.tz_edit.text()):
            QMessageBox.warning(self, APP_NAME, tr(self.lang, "tz_invalid"))
            return
        self.write_config()
        if self.audio_out is not None:
            self.audio_out.setVolume(max(0.0, min(1.0, self.volume / 100.0)))
        self.refresh_all()
        QMessageBox.information(self, APP_NAME, tr(self.lang, "save_ok"))

    # ---------------- tray
    def make_icon(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(COLORS["gold"]))
        painter.drawEllipse(6, 6, 52, 52)
        painter.setBrush(QColor(COLORS["bg"]))
        painter.drawEllipse(18, 2, 46, 46)
        painter.end()
        return QIcon(pixmap)

    def init_tray(self):
        global TRAY
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self.make_icon(), self)
        self.tray.setToolTip(APP_NAME)
        menu = QMenu()
        show_action = menu.addAction(tr(self.lang, "open_nour"))
        show_action.triggered.connect(self.show_from_tray)
        quit_action = menu.addAction(tr(self.lang, "quit"))
        quit_action.triggered.connect(self.really_quit)
        self.tray_show_action = show_action
        self.tray_quit_action = quit_action
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()
        TRAY = self.tray

    def show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def tray_activated(self, reason):
        if reason in tray_click_reasons():
            self.show_from_tray()

    def stop_worker(self):
        if self.loc_worker is not None and self.loc_worker.isRunning():
            self.loc_worker.wait(8000)

    def really_quit(self):
        self._quit = True
        self.stop_worker()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if getattr(self, "_quit", False) or TRAY is None:
            self.stop_worker()
            event.accept()
            QApplication.instance().quit()
            return
        event.ignore()
        self.hide()
        try:
            TRAY.showMessage(APP_NAME, tr(self.lang, "tray_msg"), tray_info_icon(), 4000)
        except Exception:
            pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)  # lives in the tray; closeEvent decides when to quit
    app.setFont(QFont("Segoe UI", 10))
    for font_path in (APP_DIR / "AmiriQuran-Regular.ttf", bundle_dir() / "AmiriQuran-Regular.ttf"):
        if font_path.is_file():
            if QFontDatabase.addApplicationFont(str(font_path)) < 0:
                print("Could not load Mushaf font:", font_path)
            break
    window = MainWindow()
    window.show_page("today")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
