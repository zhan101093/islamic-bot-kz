import os
import json
import logging
import random
from pathlib import Path
from dotenv import load_dotenv

import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ── Load env ──────────────────────────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID     = int(os.getenv("CHANNEL_ID", "-1003903707711"))

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
HISTORY_FILE = BASE_DIR / "post_history.json"
LOG_FILE     = BASE_DIR / "bot.log"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Suppress verbose HTTP polling logs from httpx/httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ── Gemini setup ──────────────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)

# ── Пост банкі: аят пен хадис алдын ала тексерілген ──────────────────────────
# Аят аудармалары: ҚМДБ бекіткен нұсқа негізінде.
# Хадис мәтіндері: Бұхари немесе Муслим жинақтарынан.
# Жаңа пост қосқанда осы форматты сақтаңыз.
POSTS = [
    {
        "topic": "Ата-анаға жақсылық жасау",
        "ayah_arabic": "وَقَضَىٰ رَبُّكَ أَلَّا تَعْبُدُوا إِلَّا إِيَّاهُ وَبِالْوَالِدَيْنِ إِحْسَانًا",
        "ayah_kazakh": "Раббың ана-әкеден басқаға ғибадат жасама деп бұйырды және ата-анаға жақсылық жасауды парыз етті.",
        "ayah_source": "Исра сүресі, 23-аят",
        "hadith": "Пайғамбарымыздан (с.а.с.) ең сауапты амал қайсысы деп сұрады. Ол: «Уақытында оқылған намаз», — деді. «Сосын не?» деген сұраққа: «Ата-анаға жақсылық жасау», — деді.",
        "hadith_source": "Бұхари, Муслим",
    },
    {
        "topic": "Көршіге жақсылық жасаудың сауабы",
        "ayah_arabic": "وَاعْبُدُوا اللَّهَ وَلَا تُشْرِكُوا بِهِ شَيْئًا ۖ وَبِالْوَالِدَيْنِ إِحْسَانًا وَبِذِي الْقُرْبَىٰ وَالْيَتَامَىٰ وَالْمَسَاكِينِ وَالْجَارِ ذِي الْقُرْبَىٰ وَالْجَارِ الْجُنُبِ",
        "ayah_kazakh": "Аллаhқа ғибадат жасаңдар және оған ешнәрсені серік қоспаңдар. Ата-анаға, туыстарға, жетімдерге, кедейлерге, жақын көршіге, алыс көршіге жақсылық жасаңдар.",
        "ayah_source": "Ниса сүресі, 36-аят",
        "hadith": "«Жәбірейіл (а.с.) маған көрші туралы сонша уақыт өсиет етті, мен оны мұрагер деп жариялайды-ау деп ойладым.»",
        "hadith_source": "Бұхари, Муслим",
    },
    {
        "topic": "Садақа берудің қасиеті",
        "ayah_arabic": "مَّثَلُ الَّذِينَ يُنفِقُونَ أَمْوَالَهُمْ فِي سَبِيلِ اللَّهِ كَمَثَلِ حَبَّةٍ أَنبَتَتْ سَبْعَ سَنَابِلَ فِي كُلِّ سُنبُلَةٍ مِّائَةُ حَبَّةٍ",
        "ayah_kazakh": "Аллаhтың жолында малын жұмсайтындардың мысалы — жеті масақ шығаратын бір дәннің мысалы сияқты; әр масақта жүз дән бар.",
        "ayah_source": "Бақара сүресі, 261-аят",
        "hadith": "«Садақа мал-мүлікті кемітпейді. Кешіргені үшін Аллаh адамның мәртебесін арттырады.»",
        "hadith_source": "Муслим",
    },
    {
        "topic": "Шүкіршілік етудің береке әкелуі",
        "ayah_arabic": "لَئِن شَكَرْتُمْ لَأَزِيدَنَّكُمْ ۖ وَلَئِن كَفَرْتُمْ إِنَّ عَذَابِي لَشَدِيدٌ",
        "ayah_kazakh": "«Егер шүкіршілік етсеңдер, Мен сендерге (нығметімді) арттырамын. Ал егер нанбасаңдар, расында Менің азабым қатты.»",
        "ayah_source": "Ибраhим сүресі, 7-аят",
        "hadith": "«Аллаhқа шүкіршілік етпеген адам адамдарға да алғысын айтпайды.»",
        "hadith_source": "Тирмизи, Әбу Дәуіт",
    },
    {
        "topic": "Өтірік айтпау — адамгершіліктің негізі",
        "ayah_arabic": "يَا أَيُّهَا الَّذِينَ آمَنُوا اتَّقُوا اللَّهَ وَكُونُوا مَعَ الصَّادِقِينَ",
        "ayah_kazakh": "«Уа, иман еткендер! Аллаhтан қорқыңдар және шыншылдармен бірге болыңдар.»",
        "ayah_source": "Тәубе сүресі, 119-аят",
        "hadith": "«Шыншылдық жақсылыққа апарады, жақсылық жаннатқа апарады. Адам шынайы болуға тырысып, Аллаhтың қасында шыншыл деп жазылады. Өтірік бұзақылыққа апарады, бұзақылық тозаққа апарады.»",
        "hadith_source": "Бұхари, Муслим",
    },
    {
        "topic": "Ашуды тежеудің даналығы",
        "ayah_arabic": "وَالْكَاظِمِينَ الْغَيْظَ وَالْعَافِينَ عَنِ النَّاسِ ۗ وَاللَّهُ يُحِبُّ الْمُحْسِنِينَ",
        "ayah_kazakh": "«...және ашуларын жұтатындар, адамдарды кешіретіндер. Аллаh жақсылық жасаушыларды жақсы көреді.»",
        "ayah_source": "Әли Имран сүресі, 134-аят",
        "hadith": "Бір адам Пайғамбарымыздан (с.а.с.) өсиет сұрады. Ол: «Ашуланба», — деді. Адам қайта сұрады, Пайғамбарымыз тағы да: «Ашуланба», — деп үш рет қайталады.",
        "hadith_source": "Бұхари",
    },
    {
        "topic": "Намаздың жүрекке тыныштық беруі",
        "ayah_arabic": "وَاسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ وَإِنَّهَا لَكَبِيرَةٌ إِلَّا عَلَى الْخَاشِعِينَ",
        "ayah_kazakh": "«Сабыр мен намаз арқылы (Аллаhтан) жәрдем сұраңдар. Расында бұл (намаз) — ізетті жандардан басқаларға ауыр.»",
        "ayah_source": "Бақара сүресі, 45-аят",
        "hadith": "«Намаз — жаннаттың кілті, дәрет — намаздың кілті.»",
        "hadith_source": "Тирмизи, Ахмад",
    },
    {
        "topic": "Кешірімділік — жүрек тазалығы",
        "ayah_arabic": "فَمَنْ عَفَا وَأَصْلَحَ فَأَجْرُهُ عَلَى اللَّهِ ۚ إِنَّهُ لَا يُحِبُّ الظَّالِمِينَ",
        "ayah_kazakh": "«Кешіріп, жөнге салған адамның сыйлығы Аллаhтың қасында. Расында Ол зұлымдарды жақсы көрмейді.»",
        "ayah_source": "Шура сүресі, 40-аят",
        "hadith": "«Садақа мал-мүлікті кемітпейді. Кешіргені үшін Аллаh адамның мәртебесін арттырады. Аллаh үшін кішіпейілділік танытқан адамды Аллаh биіктетеді.»",
        "hadith_source": "Муслим",
    },
    {
        "topic": "Тазалықтың иманнан екені",
        "ayah_arabic": "إِنَّ اللَّهَ يُحِبُّ التَّوَّابِينَ وَيُحِبُّ الْمُتَطَهِّرِينَ",
        "ayah_kazakh": "«Расында Аллаh тәубе ететіндерді де, тазаланатындарды да жақсы көреді.»",
        "ayah_source": "Бақара сүресі, 222-аят",
        "hadith": "«Тазалық — иманның жартысы.»",
        "hadith_source": "Муслим",
    },
    {
        "topic": "Қиындықты сабырмен қабылдау",
        "ayah_arabic": "يَا أَيُّهَا الَّذِينَ آمَنُوا اسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ",
        "ayah_kazakh": "«Уа, иман еткендер! Сабыр мен намаз арқылы жәрдем сұраңдар. Расында Аллаh сабырлылармен бірге.»",
        "ayah_source": "Бақара сүресі, 153-аят",
        "hadith": "«Мүминнің ісі таңқаларлық! Барлық ісі оған пайдалы. Қуанышты жағдай болса шүкіршілік етеді — бұл оған пайдалы. Қиындық жетсе сабыр етеді — бұл да оған пайдалы.»",
        "hadith_source": "Муслим",
    },
    {
        "topic": "Өзгені сынамаудың сауабы",
        "ayah_arabic": "يَا أَيُّهَا الَّذِينَ آمَنُوا اجْتَنِبُوا كَثِيرًا مِّنَ الظَّنِّ إِنَّ بَعْضَ الظَّنِّ إِثْمٌ",
        "ayah_kazakh": "«Уа, иман еткендер! Жаман ойдың көбінен аулақ болыңдар, расында кейбір жаман ой — күнә.»",
        "ayah_source": "Хужурат сүресі, 12-аят",
        "hadith": "«Өз нәпсіңе зиян тигізетін нәрсені өзгеге жасама. Міне, осы — исламның мәні.»",
        "hadith_source": "Тирмизи, Ахмад",
    },
    {
        "topic": "Бауырыңды сүю — иманның белгісі",
        "ayah_arabic": "إِنَّمَا الْمُؤْمِنُونَ إِخْوَةٌ فَأَصْلِحُوا بَيْنَ أَخَوَيْكُمْ",
        "ayah_kazakh": "«Мүминдер — бауырлар. Сондықтан екі бауырыңның арасын түзеңдер.»",
        "ayah_source": "Хужурат сүресі, 10-аят",
        "hadith": "«Өзі үшін жақсы көрген нәрсені бауыры үшін де жақсы көрмегенше, адамның иманы толық болмайды.»",
        "hadith_source": "Бұхари, Муслим",
    },
    {
        "topic": "Уақытты бағалау — мұсылманның парызы",
        "ayah_arabic": "وَالْعَصْرِ ‎﴿١﴾‏ إِنَّ الْإِنسَانَ لَفِي خُسْرٍ ‎﴿٢﴾‏ إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ",
        "ayah_kazakh": "«Уақыт куәгер! Расында адам зияндалу үстінде. Бірақ иман еткендер мен жақсы амал жасағандар — олардан басқа.»",
        "ayah_source": "Аср сүресі, 1-3-аяттар",
        "hadith": "«Екі нығмет бар: адамдардың көпшілігі осы екеуінде алданып жүреді — денсаулық пен бос уақыт.»",
        "hadith_source": "Бұхари",
    },
    {
        "topic": "Ұяттылық — иманның бір бөлігі",
        "ayah_arabic": "وَقُل لِّلْمُؤْمِنَاتِ يَغْضُضْنَ مِنْ أَبْصَارِهِنَّ وَيَحْفَظْنَ فُرُوجَهُنَّ",
        "ayah_kazakh": "«Мүмін әйелдерге де айт: көздерін (харамнан) сақтасын және ұятты жерлерін қорғасын.»",
        "ayah_source": "Нур сүресі, 31-аят",
        "hadith": "«Ұят — иманнан. Иманы бар адам жаннатта болады. Бұзақылық — қатыгездіктен. Қатыгез адам тозақта.»",
        "hadith_source": "Тирмизи",
    },
    {
        "topic": "Ысырапшылдықтан сақтану",
        "ayah_arabic": "وَلَا تُبَذِّرْ تَبْذِيرًا ‎﴿٢٦﴾‏ إِنَّ الْمُبَذِّرِينَ كَانُوا إِخْوَانَ الشَّيَاطِينِ",
        "ayah_kazakh": "«Ысырап жасама. Расында ысырапшылар — шайтандардың бауырлары.»",
        "ayah_source": "Исра сүресі, 26-27-аяттар",
        "hadith": "«Аллаh сендерге үш нәрсені жақсы көреді: Оған ғибадат етуді, оған ешнәрсені серік қоспауды және Аллаhтың арқанынан ұжымдасып ұстауды. Үш нәрсені жек көреді: сенімсіз сөздерді, көп сұрауды және малды ысырап етуді.»",
        "hadith_source": "Муслим",
    },
    {
        "topic": "Дұға — Аллаhпен байланыс",
        "ayah_arabic": "وَقَالَ رَبُّكُمُ ادْعُونِي أَسْتَجِبْ لَكُمْ",
        "ayah_kazakh": "«Раббың: «Маған дұға қылыңдар, қабыл аламын» — деді.»",
        "ayah_source": "Мүмін сүресі, 60-аят",
        "hadith": "«Дұға — ибадаттың өзегі.»",
        "hadith_source": "Тирмизи",
    },
    {
        "topic": "Зікірдің жүрекке тыныштық беруі",
        "ayah_arabic": "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ",
        "ayah_kazakh": "«Білімен! Аллаhты зікір ету арқылы жүректер тыныштық табады.»",
        "ayah_source": "Рад сүресі, 28-аят",
        "hadith": "«Тілдеріңізді Аллаhты зікір етуден ылғал ұстаңдар.»",
        "hadith_source": "Тирмизи, Ибн Мәжә",
    },
    {
        "topic": "Ілім іздеу — мұсылманның парызы",
        "ayah_arabic": "يَرْفَعِ اللَّهُ الَّذِينَ آمَنُوا مِنكُمْ وَالَّذِينَ أُوتُوا الْعِلْمَ دَرَجَاتٍ",
        "ayah_kazakh": "«Аллаh сендерден иман еткендердің де, ілім берілгендердің де дәрежесін биіктетеді.»",
        "ayah_source": "Мүжаделе сүресі, 11-аят",
        "hadith": "«Ілім іздеу — әрбір мұсылманға парыз.»",
        "hadith_source": "Ибн Мәжә",
    },
    {
        "topic": "Тәубе — жаңа бастаудың есігі",
        "ayah_arabic": "قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنفُسِهِمْ لَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ",
        "ayah_kazakh": "«Айт: «Уа, өздеріне зұлымдық жасаған Менің құлдарым! Аллаhтың рахметінен үміт үзбеңдер.»»",
        "ayah_source": "Зүмер сүресі, 53-аят",
        "hadith": "«Барлық адам баласы қателеседі. Қателесушілердің жақсысы — тәубе қылушылар.»",
        "hadith_source": "Тирмизи, Ибн Мәжә",
    },
    {
        "topic": "Жомарттықтың сыйы",
        "ayah_arabic": "وَمَا تُنفِقُوا مِنْ خَيْرٍ فَلِأَنفُسِكُمْ",
        "ayah_kazakh": "«Жақсылықтан не жұмсасаңдар — өздеріңіз үшін.»",
        "ayah_source": "Бақара сүресі, 272-аят",
        "hadith": "«Жомарт адам Аллаhқа жақын, жаннатқа жақын, адамдарға жақын.»",
        "hadith_source": "Тирмизи",
    },
    {
        "topic": "Туыстық байланысты сақтау",
        "ayah_arabic": "وَاتَّقُوا اللَّهَ الَّذِي تَسَاءَلُونَ بِهِ وَالْأَرْحَامَ",
        "ayah_kazakh": "«Аллаhтан қорқыңдар — Оның атымен бір-бірінен сұрайсыңдар — және туыстық байланысты үзбеңдер.»",
        "ayah_source": "Ниса сүресі, 1-аят",
        "hadith": "«Туыстық байланысты үзген адам жаннатқа кірмейді.»",
        "hadith_source": "Бұхари, Муслим",
    },
    {
        "topic": "Мейірімділік — Аллаhтың қасиеті",
        "ayah_arabic": "وَرَحْمَتِي وَسِعَتْ كُلَّ شَيْءٍ",
        "ayah_kazakh": "«Менің рахметім барлық нәрсені қамтыды.»",
        "ayah_source": "Аграф сүресі, 156-аят",
        "hadith": "«Адамдарға мейірімді болмағанға Аллаh та мейірімді болмайды.»",
        "hadith_source": "Бұхари, Муслим",
    },
    {
        "topic": "Тілді күзету — аманат",
        "ayah_arabic": "مَا يَلْفِظُ مِن قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ",
        "ayah_kazakh": "«Ол айтқан сөзді — оның жанында дайын тұрған күзетші жазып отырады.»",
        "ayah_source": "Қаф сүресі, 18-аят",
        "hadith": "«Аллаhқа және ақырет күніне иман еткен адам — жақсы сөз айтсын немесе үндемесін.»",
        "hadith_source": "Бұхари, Муслим",
    },
    {
        "topic": "Жетімдерге қамқорлық жасау",
        "ayah_arabic": "فَأَمَّا الْيَتِيمَ فَلَا تَقْهَرْ",
        "ayah_kazakh": "«Жетімге зорлық жасама.»",
        "ayah_source": "Духа сүресі, 9-аят",
        "hadith": "«Мен мен жетімге қамқорлық жасаушы — жаннатта осылай боламыз» деп Пайғамбарымыз (с.а.с.) екі саусағын жақындастырды.",
        "hadith_source": "Бұхари",
    },
    {
        "topic": "Адал еңбектің қадірі",
        "ayah_arabic": "وَقُلِ اعْمَلُوا فَسَيَرَى اللَّهُ عَمَلَكُمْ وَرَسُولُهُ وَالْمُؤْمِنُونَ",
        "ayah_kazakh": "«Амал жасаңдар — Аллаh, Оның елшісі және мүминдер сендердің амалдарыңды көреді.»",
        "ayah_source": "Тәубе сүресі, 105-аят",
        "hadith": "«Аллаh бір ісіңді жасасаң, оны жақсылап жасауды сүйеді.»",
        "hadith_source": "Байхақи",
    },
]


# ── History helpers ───────────────────────────────────────────────────────────
def load_history() -> list[str]:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_to_history(topic: str) -> None:
    history = load_history()
    history.append(topic)
    history = history[-len(POSTS):]
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_fresh_post(history: list[str]) -> dict:
    used = set(history[-len(POSTS):])
    fresh = [p for p in POSTS if p["topic"] not in used]
    if not fresh:
        fresh = POSTS
    return random.choice(fresh)


# ── Content generation ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Сен — қазақ тілінде жазатын автормысың. Тілің таза, жатық, тірі қазақша болуы шарт.

ОҚЫРМАНҒА ӘРДАЙЫМ «сіз» деп жаз. «Сен», «сенің», «саған» — ТЫЙЫМ.

Тыйым салынған сөздер:
— «ұяттылық» → «ұят»
— «маңызын тереңдетеді», «мәнін баяндайды» — кеңсе тілі, жоқ
— «апарып соғады», «себепші болады», «артуына әкеледі» — орысша кальк, жоқ

Сөйлем ережесі:
— Бір сөйлемде бір ой
— Сөйлем нүктемен, леп немесе сұрақ белгісімен аяқталсын — үзілмесін

━━ ОЙТОЛҒАУ (2-3 сөйлем) ━━
— Аятты/хадисті қайталама — мағынасын өмірден ашып бер
— «Бұл аят...», «Осы хадис...» деп басталма
— Оқырманның жүрегіне тисін

━━ ТАПСЫРМА — ҚАТАҢ ФОРМАТ ━━
Тапсырма ТЕК бір сөйлемнен тұрады:
[Нақты амал] — [қысқа пайдасы].

Мысалдар:
✅ Бүгін көршіңізге амандасыңыз — жақын адам сезімі иманды нығайтады. 🤝
✅ Кешкісін үш нәрсеге Аллаhқа алғыс айтыңыз — ризашылық жүрекке тыныштық береді. 🤲
✅ Ашуланған сәтте тоқтап, тыныс алыңыз — ашуды жұту — сауап. 💛

Міне, осы үлгіден ауытқыма: амал + сызықша + пайда + нүкте + эмодзи.
"""

REFLECTION_TEMPLATE = """
Тақырып: {topic}
Аят: {ayah_kazakh} ({ayah_source})
Хадис: {hadith} ({hadith_source})

Тек мына форматта жаз — басқа ештеңе қоспа:

💭 Ойтолғау:
[2-3 сөйлем, оқырманға «сіз» деп, аятты қайталамай, өмірден]

✅ Тапсырма:
[нақты амал] — [пайдасы]. [эмодзи]
"""

gemini_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT,
)


async def generate_post(post: dict) -> str:
    prompt = REFLECTION_TEMPLATE.format(**post)
    try:
        response = await gemini_model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=600,
                temperature=0.75,
            ),
        )
        reflection = response.text.strip()

        text = (
            f"*{post['topic']}*\n\n"
            f"📖 {post['ayah_arabic']}\n"
            f"_{post['ayah_kazakh']}_ ({post['ayah_source']})\n\n"
            f"📜 _{post['hadith']}_ ({post['hadith_source']})\n\n"
            f"{reflection}"
        )
        if len(text) > 4096:
            text = text[:4093] + "..."
        return text
    except Exception as e:
        logger.error(f"Gemini generation error: {e}")
        raise


# ── Post sender ───────────────────────────────────────────────────────────────
async def send_daily_post(app: Application) -> None:
    history = load_history()
    post    = pick_fresh_post(history)
    logger.info(f"Generating post for topic: {post['topic']}")
    try:
        content = await generate_post(post)
        await app.bot.send_message(
            chat_id    = CHANNEL_ID,
            text       = content,
            parse_mode = "Markdown",
        )
        save_to_history(post["topic"])
        logger.info(f"✅ Post sent | topic: {post['topic']}")
    except Exception as e:
        logger.error(f"❌ Failed to send post: {e}")


# ── Command handlers ──────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Ассалаумағалейкум! 👋\n\n"
        "Бот іске қосылды. Посттар 12 сағат сайын жіберіледі.\n\n"
        "Командалар:\n"
        "/post — қазір пост жіберу\n"
        "/plan — келесі посттар тақырыбы\n"
        "/history — соңғы тақырыптар\n"
        "/status — бот күйі"
    )


async def cmd_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⏳ Пост жасалуда...")
    history = load_history()
    post    = pick_fresh_post(history)
    try:
        content = await generate_post(post)
        await context.application.bot.send_message(
            chat_id    = CHANNEL_ID,
            text       = content,
            parse_mode = "Markdown",
        )
        save_to_history(post["topic"])
        await update.message.reply_text("✅ Пост каналға жіберілді!")
    except Exception as e:
        logger.error(f"cmd_post error: {e}")
        await update.message.reply_text(f"❌ Қате шықты:\n`{e}`", parse_mode="Markdown")


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history = load_history()
    if not history:
        await update.message.reply_text("Тарих бос.")
        return
    lines = "\n".join(f"{i+1}. {t}" for i, t in enumerate(history[-10:]))
    await update.message.reply_text(f"📋 *Соңғы 10 тақырып:*\n\n{lines}", parse_mode="Markdown")


async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history = load_history()
    used = set(history[-len(POSTS):])
    fresh = [p for p in POSTS if p["topic"] not in used]
    if not fresh:
        fresh = POSTS
    lines = "\n".join(f"{i+1}. {p['topic']}" for i, p in enumerate(fresh))
    await update.message.reply_text(
        f"📋 *Келесі посттар ({len(fresh)} қалды):*\n\n{lines}",
        parse_mode="Markdown"
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Telegram error: {context.error}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history = load_history()
    msg = (
        f"🟢 *Бот жұмыс істеуде*\n\n"
        f"📡 Канал ID: `{CHANNEL_ID}`\n"
        f"📝 Жіберілген посттар: {len(history)}\n"
        f"🔄 Қалған тақырыптар: {len(POSTS) - len(set(history))}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set in .env")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in .env")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("post",    cmd_post))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("plan",    cmd_plan))
    app.add_error_handler(error_handler)

    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
    scheduler.add_job(
        send_daily_post,
        trigger           = "cron",
        hour              = "9,20",
        minute            = 0,
        kwargs            = {"app": app},
        id                = "post_morning",
        misfire_grace_time= 3600,
    )
    scheduler.start()
    logger.info("Scheduler started — posts at 09:00 and 20:00 (Almaty)")

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
