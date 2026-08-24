"""Configuration global parameters of the overall crawler
In particular, input mail selection, HTTP requests orchestration and scenario selection"""

import os
from os.path import join

MAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# running setup
RUN_CONFIG = {
    "MAIN_DIR": MAIN_DIR,

    # GENERAL
    # files
    # "input_folder": join(MAIN_DIR, "input", "com_extramini"),
    "input_folder": join(MAIN_DIR, "input", "com_mini"),
    # "input_folder": join(MAIN_DIR, "input", "com1k"),
    # "input_folder": join(MAIN_DIR, "input", "com10k"),

    # Max number of domains the controller can handle in one go.
    "CONTROLLER_LIMIT": 2000,  # Files will be split into these chunks before being fed to the controller

    "output_final_file_path": join(MAIN_DIR, "completed", "perf2.csv"),
    "CSV_OUTPUT_DELIMITER": ',',
    # Set this to the character you want as the delimiter, will apply to the output_file_final_path

    # Scenario
    "DO_REQUESTS": True,
    # "DO_REQUESTS": False,
    "DO_PAGE_PROCESSING": True,
    # "DO_PAGE_PROCESSING": False,
    "DO_CLASSIFICATION": True,
    # "DO_CLASSIFICATION": False,
    "DO_CONTENT_CLASSIFICATION": True,
    # "DO_CONTENT_CLASSIFICATION": False,
    "DO_SOCIAL_MEDIA": True,
    # "DO_SOCIAL_MEDIA": False,
    "DO_MAIL_EXCHANGE": True,
    # "DO_MAIL_EXCHANGE": False,
    "DO_HCJ_EXTRACTION": True,
    # "DO_HCJ_EXTRACTION": False,
    "DO_JS_INTERPRETATION": True,
    # "DO_JS_INTERPRETATION": False,
    "DO_CONCAT_FORMAT": True,
    "DO_SAMPLING": False,

    # REQUESTS ENGINE
    # "USE_UVLOOP": True,
    "USE_UVLOOP": False,
    # timeout for to request and extract the response of a single url
    "MINUTES_TO_TIMEOUT": 2,
    # maximum number of connection by TCP connector
    "LIMIT_REQUEST": 50,
    # maximum size of the queue = batch of urls automatically processed when a Python interpreter is
    # available (1 queue per process)
    # "MAX_WORKERS": 100,
    "MAX_WORKERS": 50,
    # number of folds to split input file (example: a 24,000 urls input file is processed in three batches of
    # 8,000, each batch is entirely done by one process)
    "BATCH_SPLIT": 3,
    # request engine/classification on multiple processes
    "MULTI_PROCESSING": True,
    # "MULTI_PROCESSING": False,
    # number of processes to use for request engine: 1 process = 1 Python interpreter = one queue = one batch at a time
    "MAX_PROCESSES": 3,
    "MAX_MB_SINGLE_URL": 200,

    # Whether to use Threads or Processes
    "PARALLEL_PREFER": "processes",
    # how many requests per second we should make at the most
    "REQUEST_RATE_LIMIT": 2000,

    # Force new visit if a website have already been visited in a former run
    "force_new_visit": False,
    # Allow multiple loops of requests for Timout error/Server disconnection errors
    "ENABLE_REVISITING": True,
    "MAX_REVISIT": 1,

    ## Chrome options
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",

    # ANTI-BLOCKING (aiohttp request layer -- url_visitor.py)
    # Rotate a real desktop browser User-Agent (one per domain, stable across that
    # domain's own retries) and send browser-like Accept/Sec-Fetch-* headers on the
    # aiohttp pass. Set False to revert to the single static USER_AGENT above with
    # no extra headers.
    "ENABLE_UA_ROTATION": True,
    "UA_POOL": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    ],
    # On HTTP 429: retry up to this many times, honoring a numeric Retry-After
    # header when present, else exponential backoff. Set to 0 to disable.
    "MAX_RETRIES_429": 3,
    # On HTTP 503 or a Cloudflare edge error (520-527, 530): short-backoff retries.
    # Set to 0 to disable.
    "MAX_RETRIES_5XX": 2,
    # base for the exponential backoff: delay = BACKOFF_BASE_SECONDS * 2**(retry_n-1)
    "BACKOFF_BASE_SECONDS": 1,
    # WAVE 5: transient connection-level failures (raised as exceptions before
    # any HTTP response is received -- refused/reset/dropped connection,
    # server disconnect) get this many backoff-and-retry attempts within the
    # same request, mirroring the 429/5xx retry above. Deliberately does NOT
    # cover DNS resolution errors (a domain that doesn't resolve is genuinely
    # dead, not transient) or the request-level TimeoutError (already burned
    # the full MINUTES_TO_TIMEOUT budget once; doubling that wait doesn't
    # help and just slows the whole batch down). Set to 0 to disable.
    "MAX_RETRIES_CONNECTION": 2,
    # A 403 (or a Cloudflare status that survives the retries above) gets one
    # real-browser attempt via request_full_file_with_browser() before being
    # classified as an error, reusing the existing to_revisit_with_js pipeline
    # so a successful browser fetch is reclassified normally. Set False to
    # revert to classifying these as errors immediately (old behaviour).
    "ENABLE_BROWSER_ON_403": True,

    # WAVE 4 (classification_parked.py / formatting.py): interstitial/infra gate,
    # empty-page floor, reclassify-on-browser-success, render timeout.
    # No proxies/stealth here -- genuine Cloudflare/Vercel JS challenges are left
    # unsolved on purpose; this wave is about not mis-labeling them as content.

    # 1. Interstitial/infra gate: a fetched page (from either request pass) showing
    # any of these signals is a challenge/block page, not real content, and is
    # routed to No content > Errors > Blocked/Undetermined -- this OVERRIDES the
    # park/ML classifier (including ml_feat_blocked), so a Cloudflare page whose
    # body contains the word "blocked" is caught here, not filed as Content>Blocked.
    "ENABLE_INTERSTITIAL_GATE": True,
    # WAVE 7: split from the old single BLOCKED_STATUS_CODES so
    # formatting.py's classification gate can route each terminal status to
    # the right proxy-actionable lv3 bucket -- BOT_BLOCKED_STATUS_CODES are
    # the ones a residential/rotating proxy retry can plausibly get past
    # (rate-limit or bot-challenge responses); ORIGIN_ERROR_STATUS_CODES are
    # Cloudflare's own "origin server unreachable" edge errors, which no
    # amount of proxying fixes since the block isn't on the client side.
    # BLOCKED_STATUS_CODES stays as their union: it still drives the
    # detect_interstitial() status-code leg and the BLOCKED_STATUS_PATTERN
    # browser-fallback trigger in classification_parked.py, where the only
    # question is "is this status blocked-ish at all" -- the bot/origin split
    # itself only matters downstream, in formatting.py's lv3 gate.
    "BOT_BLOCKED_STATUS_CODES": [403, 429, 503],
    "ORIGIN_ERROR_STATUS_CODES": [520, 521, 522, 523, 524, 525, 526, 527, 530],
    "BLOCKED_STATUS_CODES": [403, 429, 503, 520, 521, 522, 523, 524, 525, 526, 527, 530],
    "CHALLENGE_TITLES": [
        "Attention Required! | Cloudflare",
        "Just a moment",
        "Web server is down",
        "Cloudflare Tunnel error",
        "Vercel Security Checkpoint",
        "403 Forbidden",
        "503 Service Unavailable",
    ],
    "CHALLENGE_BODY_MARKERS": [
        "you have been blocked",
        "Performing security verification",
        "Checking your browser",
        "Ray ID:",
        "Incapsula incident ID",
        "cf-ray",
        "Error code 521",
        "Error 1033",
        "Enable JavaScript and cookies to continue",
    ],

    # 2. Empty-page gate: a page with this few visible words can't be meaningful
    # content regardless of flag_js_found/iframe/ML signals -- applied as a floor
    # that wins over those signals (previously the emptiness check was skipped
    # entirely whenever flag_js_found or an iframe was present).
    "ENABLE_EMPTY_WORD_FLOOR": True,
    "EMPTY_WORD_THRESHOLD": 10,

    # 3. Reclassification: if a browser-fallback fetch comes back with this many
    # words or more and isn't caught by the interstitial gate, treat it as real
    # content even though the initial request errored.
    "ENABLE_RECLASSIFY_ON_BROWSER_SUCCESS": True,
    "REAL_CONTENT_WORD_THRESHOLD": 100,

    # 4. Render timeout: Selenium page-load timeout for the browser-fallback pass
    # (previously only an implicit 15s wait was set, with no explicit page-load
    # timeout at all). A timeout is treated as undetermined -- it does not
    # overwrite the row's existing classification.
    "RENDER_TIMEOUT_SECONDS": 30,

    # WAVE 5 (classification_parked.py / formatting.py): ISP/hosting placeholder
    # gate, archive.org-redirect gate. Both mirror the interstitial gate above --
    # checked before the park/ML classifier, so they can never be filed as
    # Content/Parked.

    # 5. ISP/hosting placeholder gate: a domain with nothing configured often
    # still returns a plain HTTP 200 with the hosting provider's own generic
    # "can't be displayed" page instead of a 4xx/5xx. From the HTTP layer alone
    # this looks like a normal successful response, and its few words of
    # boilerplate can get the ML park-classifier to call it "Parked Notice
    # Individual Content". Kept deliberately narrow/specific (exact known
    # provider boilerplate, not generic phrases) to avoid catching real error
    # pages that are themselves meaningful custom content.
    "ENABLE_ISP_PLACEHOLDER_GATE": True,
    "ISP_PLACEHOLDER_BODY_MARKERS": [
        "Error. Page cannot be displayed. Please contact your service provider for more details.",
    ],

    # 6. Archive.org-redirect gate: a domain that hard-redirects to a specific
    # web.archive.org (Wayback Machine) snapshot isn't serving its own content
    # -- the words on that page belong to whoever archived it, not to this
    # domain, and the domain itself is effectively inactive. Reuses the
    # existing registrar-link detection (park_service ends up "web.archive.org"
    # via the "web"/".archive.org" entry in hosting_companies_with_tld.csv) so
    # this fires whenever that specific match happens, instead of letting it
    # fall through to "Parked Notice Registrar" or counting the archived page's
    # word count as if it were live content.
    "ENABLE_ARCHIVE_REDIRECT_GATE": True,
    "ARCHIVE_REDIRECT_DOMAINS": ["archive.org"],

    # path where url pickle are saved (if debug-mode=True)
    "PATH_URL_SAVE": join(MAIN_DIR, "inter", "urls"),

    # path where file pickle are saved(if debug-mode=True)
    "PATH_DOC_SAVE": join(MAIN_DIR, "inter"),

    # request engine progress notifications
    "LOG_EVERY_N": 500,

    # PAGE PROCESSING
    # Number of parallel workers (<= number of CPUs)
    "WORKERS_POST_PROCESSING": 5,

    # PARKING CLASSIFICATION
    # if True, save the original sentence in the column kw_park_notice, else just the attribute keyword in english
    "LANGUAGE_DEVELOPMENT_MODE": False,
    "PATH_URL_REVISIT_SAVE": join(MAIN_DIR, "inter", "revisit"),
    "name_model": "xgb_v1",
    "taxonomy_path": join(MAIN_DIR, "input", "taxonomy.csv"),
    "unique_words": join(MAIN_DIR, "input", "vocab_unique_words.csv"),
    "feature": "root",

    # SAMPLING 
    # The sampling_rate will determine how many domains per 100 will be randomly sampled. Each sample will get a unique browser visit 
    # to have a screenshot taken, which will be saved along with its raw-html. This data will then be prepped ready to be used in
    # LabTools for ML training.
    # Set the sampling_rate to a fractional percentage of the desired rate. e.g. 0.1 = 10% of pages will be sampled, or 1.0 = 100% of pages will be sampled.
    "SAMPLING_RATE": 0.001,
    "SAMPLING_MAX_SCREENSHOT_HEIGHT_PX": 1200,
    "SAMPLING_LOCAL_FOLDER": join(MAIN_DIR, "output", "sampling"),
    # "SAMPLING_DBNAME": "samplingdb", # direct db insert not (yet) implemented, use the rest API below.
    # "SAMPLING_DBHOST": "localhost",
    # "SAMPLING_DBPORT": 5432,
    # "SAMPLING_DBUSER": "dbuser",
    # "SAMPLING_DBPASS": "dbpass",

    "SAMPLING_REST_API_IMAGE_URL": "https://labtools.centr.org/image/",
    # web address if using a rest framework to accept samples, e.g. "https://labtools.centr.org/image/"
    "SAMPLING_REST_API_SAMPLE_URL": "https://labtools.centr.org/samples",
    # web address if using a rest framework to accept samples, e.g. "https://labtools.centr.org/samples"
    "SAMPLING_REST_API_USERNAME": "labtools",  # username used to upload samples using the rest API
    "SAMPLING_REST_API_PASSWORD": "8L%zDaC4E98#rX",  # password used to upload samples using the rest API
    "SAMPLING_REST_API_ALLOW_UPDATES": False,  # CRUD feature:
    # output_processing will try to Create a new sample from the crawler's final_ file using LabTool's REST API.
    # If a sample with the same "categorisation" data already exists (dict for dict match), LabTools will respond
    # with a HTTP Redirect code (302) to an url of the form "update-sample/<primary key>/".
    # The reponse.content will contain the database details of this sample (including the pk), so if
    # SAMPLING_REST_API_ALLOW_UPDATES is set to True, output_processing will re-upload (patch) the sample to the given URL.

    # DATABASE STORAGE
    # if True, the program will convert any csvs it finds in the output folder into the defined database and move the csvs to the storage folder
    # set these in the .env folder for security purposes, as this file is stored on the git.
    "USE_DB": False,
    "DBNAME": "signs_of_life",  # database where you're going to store all the of data
    "DBHOST": "dbpostgres",  # hostname or ip address of the db server
    "DBPORT": '5432',  # db access port
    "DBUSER": "postgres",  # db username
    "DBPASS": "/aPh.I6:Eda!YmmWUD}2",  # db password

    # DEBUGGING
    "VERBOSE_DEBUGGING": False,  # allows printing of extra debugging information while developing.
    # RUNTIME PERFORMANCE LOGGING
    "PERFORMANCE_LOGGING": False,  # runs the custom performance logging module to profile and analyse code performance
    # save intermediary files
    "DEBUG_MODE": False,
    "DEBUG_PRINT": False,
}

# version
fp_vers = join(MAIN_DIR, "app_domains", "version.txt")
if not os.path.isfile(fp_vers):
    raise FileNotFoundError("Missing version.txt in app_domains")
with open(fp_vers) as f:
    RUN_CONFIG["version"] = f.read()


# load environment file if available

def ProcessEnvSetting(setting):
    key, value = setting[0], setting[1]
    # convert text values to python recognized values
    if value.lower() == 'true':
        value = True
    elif value.lower() == 'false':
        value = False
    else:
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
    # Overwrite existing key. If a non-existent key is added, it will just be ignored.
    RUN_CONFIG[key] = value


env_file_path = join(os.path.dirname(os.path.dirname(__file__)), ".env")

try:
    with open(env_file_path, 'r') as f:
        for line in f:
            setting = line.replace('\n', '').split('=')
            if len(setting) == 2:
                ProcessEnvSetting(setting)
except IOError:
    print(f"Error: Could not read {env_file_path}")
    # Handle the error or raise an exception as needed

from utils import PerformanceLogger

PLOG = PerformanceLogger(filename="main_perf.log", enable_logging=RUN_CONFIG['PERFORMANCE_LOGGING'])
