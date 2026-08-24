"""Script handling final formatting of the full crawler results"""
from os.path import join
import os
import pandas as pd
import numpy as np
import re


from config import RUN_CONFIG

from utils import PerformanceLogger
plog = PerformanceLogger(filename="formatting_perf.log", enable_logging=RUN_CONFIG['PERFORMANCE_LOGGING'])


DEBUG_COLUMNS = ["input_url", "final_url", "tld", "category_lv1","category_lv2","category_lv3","category_lv4",
                 "language", "source", "target_url", "url", "ind_non_schema", "is_error", "comment",
                   "is_redirected","is_redirected_different_domain", "redirection_type",
                 "URL_history", "all_status_codes", "history",
                  "registrar_found", "park_service", "kw_parked", "kw_park_notice", "pred_is_empty",
                 "n_letter", "n_words", "flag_js_found", "document_write", "js_or_iframe_found",
                 "is_js_rendered_results", "flag_iframe", "original_url", "is_interstitial",
                 "is_isp_placeholder", "is_archived_redirect",
                 "has_facebook", "has_twitter", "has_linkedin", "has_reddit", "has_instagram", "has_github",
                 "feat_fb_lks", "feat_tw_lks", "feat_lk_lks", "feat_rd_lks", "feat_ig_lks", "feat_gh_lks",
                 "has_open_graph", "has_twitter_card", "has_schema_tag","has_mx_record", "MXRecord", "has_own_mx_record",
                 "to_sample", "ss_filename", "raw_filename", "clean_filename", "json_filename"
                 ]

TABLEAU_COLUMNS = ["input_url", "final_url", "tld", "category_lv1","category_lv2","category_lv3","category_lv4",
                   "has_facebook", "has_twitter", "has_linkedin", "has_reddit", "has_instagram", "has_github",
                   "has_open_graph", "has_twitter_card", "has_schema_tag","has_mx_record", "has_own_mx_record",
                   "ssl_enabled", "is_redirected","is_redirected_different_domain", "redirection_type", "all_status_codes","comment",
                   "language", "source", "target_url", "url",
                   "to_sample", "ss_filename", "raw_filename", "clean_filename", "json_filename", "fx_hcj__secu_xss", "fx_hcj__secu_xsrf",
                   "fx_hcj__secu_tls", "fx_hcj__secu_contentPolicy", "fx_hcj__secu_captcha", "fx_hcj__opti_cache",
                   "fx_hcj__opti_etag", "fx_hcj__opti_parkingPage", "fx_hcj__techno_ASP", "fx_hcj__techno_PHP",
                   "fx_hcj__techno_AWS", "fx_hcj__techno_Java", "fx_hcj__techno_Jquery", "fx_hcj__techno_React",
                   "fx_hcj__techno_Angular", "fx_hcj__service_adblock", "fx_hcj__service_wix", "fx_hcj__service_shopify",
                   "fx_hcj__service_shop", "fx_hcj__service_sucuri", "fx_hcj__service_googleAds",
                   "n_words", "n_letter", "ind_non_schema", "park_service", "flag_js_found", "tag_quantity", "URL_history",
                   "headers", "cookies", "links"
                   ]

# WAVE 6: word-count ceiling for the thin-body 403/429/503 gate below. Picked
# from canary evidence: still-blocked challenge pages that slipped through
# the is_interstitial detector topped out at 33 words (mlb.com, aa.com,
# nba.com, easyjet.com, homedepot.com, imf.org, hm.com); genuine recoveries
# that still carry an earlier/terminal 403 in all_status_codes (oracle.com,
# mercedes-benz.com, openai.com, mayoclinic.org, etc.) started at 75 words.
# 50 sits in the gap with margin on both sides.
THIN_BLOCKED_PAGE_WORD_THRESHOLD = 50

DICO_NAMING_LV4 = {
    "Other": ["Content", "Low content", "Other"],
    "Parked Notice Registrar": ["Content", "Low content", "Parked Notice Registrar"],
    # WAVE 7: lv3 'bot_blocked' groups every proxy-retryable block flavor (see
    # also Blocked_Interstitial below) so `WHERE category_lv3 = 'bot_blocked'`
    # is the Proxyseller re-crawl worklist, regardless of lv1/lv2 bucket. Split
    # out from origin-down responses (lv3 'unreachable', see Origin_Error)
    # since no proxy retry fixes a Cloudflare origin-unreachable edge error.
    "Blocked": ["Content", "Low content", "bot_blocked"],
    "Under construction": ["Content", "Low content", "Upcoming"],
    "Starter": ["Content", "Low content", "Upcoming"],
    "Expired": ["Content", "Low content", "Abandoned"],
    "Index of": ["Content", "Low content", "Not used"],
    "Blank Page": ["Content", "Low content", "Not used"],
    "For sale": ["Content", "Low content", "Parked Notice Individual Content"],
    "Reserved": ["Content", "Low content", "Parked Notice Individual Content"],
    "Parked Notice Individual Content": ["Content", "Low content", "Parked Notice Individual Content"],
    "No address found": ["No content", "Errors", "DNS Error"],
    "Refused Connection": ["No content", "Errors", "Connection Error"],
    "Timeout": ["No content", "Errors", "Connection Error"],
    "No Status Code": ["No content", "Errors", "Invalid Response"],
    "HTTP_401": ["No content", "Errors", "HTTP Error"],
    "HTTP_403": ["No content", "Errors", "HTTP Error"],
    "HTTP_404": ["No content", "Errors", "HTTP Error"],
    "HTTP_408": ["No content", "Errors", "HTTP Error"],
    "HTTP_500": ["No content", "Errors", "HTTP Error"],
    "HTTP_502": ["No content", "Errors", "HTTP Error"],
    "HTTP_504": ["No content", "Errors", "HTTP Error"],
    "HTTP_other": ["No content", "Errors", "HTTP Error"],
    "High content": ["Content", "High content", "High content"],
    # WAVE 4: distinct from "Blocked" above (Content>Low content>Blocked, for a
    # page whose OWN content is about being blocked) -- this is for a
    # Cloudflare/Vercel/etc. challenge or infra-error interstitial, which is not
    # real content at all. Assigned by a final override in final_parking_naming_v2
    # that runs after everything else, so it wins over the park/ML classifier.
    # lv3 'bot_blocked': this is the bot-challenge/rate-limit flavor of
    # interstitial (403/429/503 status leg, Cloudflare "Just a moment"/
    # "Attention Required", Vercel Security Checkpoint, Incapsula, or the
    # thin-body retry-cleared gate) -- see Origin_Error for the origin-down
    # flavor, which this dict entry no longer covers.
    "Blocked_Interstitial": ["No content", "Errors", "bot_blocked"],
    # WAVE 7: Cloudflare "origin server unreachable" edge errors (520-527,
    # 530 -- ORIGIN_ERROR_STATUS_CODES in config.py). Distinct from
    # Blocked_Interstitial/bot_blocked because these aren't a bot-detection
    # response at all -- Cloudflare's edge is up but the origin behind it
    # isn't, so a proxy retry (which only changes the client's IP/fingerprint)
    # can't fix it. lv3 'unreachable' keeps these out of the Proxyseller
    # re-crawl worklist that filters on category_lv3 = 'bot_blocked'.
    "Origin_Error": ["No content", "Errors", "unreachable"],
    # WAVE 5: HTTP-200 hosting/ISP default placeholder ("nothing configured
    # here") -- not a real response, not a park/registrar notice either.
    "ISP_Placeholder": ["No content", "Errors", "Invalid Response"],
    # WAVE 5: redirected to a specific archive.org snapshot instead of serving
    # its own content -- domain is effectively inactive, not "Parked".
    "Archived_Redirect": ["No content", "Errors", "Inactive"],
}

def final_parking_naming_v2(df):
    """Attribute final names to each of the 4 category level of parking classification"""
    df = df.copy(deep=True)

    # sub_category
    df["category_lv1"] = np.nan
    df["category_lv2"] = np.nan
    df["category_lv3"] = np.nan
    df["category_lv4"] = np.nan
    ind_classified = pd.Series(False, index=df.index)

    # NO CONTENT
    # split 1A
    ind_error = df["is_error"].apply(lambda x: str(x) in ["TRUE", True, "True"])

    # HTTP errors
    ind_cat_401_2 = df["comment"].apply(lambda x: (re.search("status code *: *40[12]", str(x)) is not None))
    ind_cat_403 = df["comment"].apply(lambda x: (re.search("status code *: *403", str(x)) is not None))
    ind_cat_404 = df["comment"].apply(lambda x: (re.search("status code *: *404", str(x)) is not None))
    ind_cat_408 = df["comment"].apply(lambda x: (re.search("status code *: *408", str(x)) is not None))
    ind_cat_500 = df["comment"].apply(lambda x: (re.search("status code *: *500", str(x)) is not None))
    ind_cat_502 = df["comment"].apply(lambda x: (re.search("status code *: *502", str(x)) is not None))
    ind_cat_504 = df["comment"].apply(lambda x: (re.search("status code *: *504", str(x)) is not None))
    # ind_cat_301_2_7_8 = df["comment"].apply(lambda x: (re.search("status code *: *30[1278]", str(x)) is not None))
    ind_status_code = df["comment"].apply(lambda x: (re.search("status code *:", str(x)) is not None))
    ind_other_status_code = ind_status_code & (~ind_cat_401_2) & (~ind_cat_403) & (~ind_cat_404) & (~ind_cat_408) & (
        ~ind_cat_500) & (~ind_cat_502) & (~ind_cat_504)

    # invalid responses
    ind_no_ns_record = df["comment"].apply(lambda x: (re.search("DNS resolution error", str(x), re.IGNORECASE) is not None))
    ind_refused_connection = df["comment"].apply(
        lambda x: (re.search("Connection closed|ServerDisconnected|Connection error", str(x), re.IGNORECASE) is not None))
    ind_timeout = df["comment"].apply(lambda x: (re.search("TimeoutError", str(x), re.IGNORECASE) is not None))
    ind_no_status_code = ind_error & (~ind_status_code) & (~ind_no_ns_record) & (~ind_refused_connection) & (
        ~ind_timeout)

    # LOW CONTENT
    # REGISTRAR
    ind_registrar = (df["registrar_found"] | df["is_full_js_parked"])& (~ind_error)

    # ML PRED
    # df["pred_ml_park"] = df["pred_ml_park"].fillna(value=-1)
    ind_ml_pred_park = df["pred_ml_park"]& (~ind_registrar)

    # list_spe_words = ["index_of", "construction","expired", "sale", "blocked", "starter", "reserved"]
    set_cols = set(list(df.columns))
    ind_cumul = ind_ml_pred_park.copy(deep=True)
    if "ml_feat_index_of" in set_cols:
        ind_index = ind_cumul & (df["ml_feat_index_of"] > 0)
    else:
        ind_index = pd.Series(False, index=df.index)
    ind_cumul = ind_cumul & (~ind_index)
    if "ml_feat_construction" in set_cols:
        ind_construction = ind_cumul & (df["ml_feat_construction"] > 0)
    else:
        ind_construction = pd.Series(False, index=df.index)
    ind_cumul = ind_cumul & (~ind_construction)
    if "ml_feat_sale" in set_cols:
        ind_sale = ind_cumul & (df["ml_feat_sale"] > 0)
    else:
        ind_sale = pd.Series(False, index=df.index)
    ind_cumul = ind_cumul & (~ind_sale)
    if "ml_feat_starter" in set_cols:
        ind_starter = ind_cumul & (df["ml_feat_starter"] > 0)
    else:
        ind_starter = pd.Series(False, index=df.index)
    ind_cumul = ind_cumul & (~ind_starter)
    if "ml_feat_expired" in set_cols:
        ind_expired = ind_cumul & (df["ml_feat_expired"] > 0)
    else:
        ind_expired = pd.Series(False, index=df.index)
    ind_cumul = ind_cumul & (~ind_expired)
    if "ml_feat_blocked" in set_cols:
        ind_blocked = ind_cumul & (df["ml_feat_blocked"] > 0)
    else:
        ind_blocked = pd.Series(False, index=df.index)
    ind_cumul = ind_cumul & (~ind_blocked)
    if "ml_feat_reserved" in set_cols:
        ind_reserved = ind_cumul & (df["ml_feat_reserved"] > 0)
    else:
        ind_reserved = pd.Series(False, index=df.index)
    ind_ml_other = ind_cumul & (~ind_reserved)

    # EMPTY
    ind_blank_page = df["pred_is_empty"] & (~df["flag_js_found"]) & (~ind_ml_pred_park) & (~ind_registrar) & (
        ~ind_error)
    # FIX (post-Wave4 validation): this used to also fire whenever
    # (ind_ml_other & pred_is_empty), i.e. it would override an ind_ml_other
    # page (a positive ML park-pattern detection, itself gated on
    # ind_ml_pred_park) back to "Blank Page" purely because pred_is_empty was
    # also true -- which happens for any page at/under EMPTY_WORD_THRESHOLD
    # words. Same bug as the word-count floor below: a positive parking
    # detection must win over the low-word-count rule, not get silently
    # re-overridden by it. ind_ml_other already requires ind_ml_pred_park,
    # which the line above already excludes -- so this clause is simply
    # removed rather than reintroducing the override.

    # WAVE 4: unconditional word-count floor -- overrides flag_js_found/iframe,
    # since a page with this few visible words can't be meaningful content
    # regardless of what those signals say (config: EMPTY_WORD_THRESHOLD). This
    # is what routes the image-based .sydney parking cluster (flag_js_found=True,
    # ~8 words) to empty/not-used instead of High content.
    # FIX (post-Wave4 validation): this must NOT override a positive registrar
    # or ML park-pattern detection -- those are affirmative signals that the
    # low word count IS the meaningful content (e.g. a one-line "domain is for
    # sale" registrar landing page, or a short parked-notice page), so they
    # take precedence over the floor just like the original ind_blank_page
    # above already excludes them via ~ind_registrar / ~ind_ml_pred_park.
    # Without these exclusions, low-word registrar/parked pages were getting
    # tagged "Parked Notice Registrar"/"Parked Notice Individual Content" at
    # line ~190/199 and then silently overwritten to "Blank Page" here.
    if RUN_CONFIG["ENABLE_EMPTY_WORD_FLOOR"] and "n_words" in set_cols:
        n_words_numeric = pd.to_numeric(df["n_words"], errors="coerce")
        ind_word_floor_empty = (n_words_numeric <= RUN_CONFIG["EMPTY_WORD_THRESHOLD"]) & (~ind_error) & (
            ~ind_registrar) & (~ind_ml_pred_park)
        ind_blank_page = ind_blank_page | ind_word_floor_empty

    # results
    df.loc[ind_cat_401_2, "category_lv4"] = "HTTP_401"
    df.loc[ind_cat_403, "category_lv4"] = "HTTP_403"
    df.loc[ind_cat_404, "category_lv4"] = "HTTP_404"
    df.loc[ind_cat_408, "category_lv4"] = "HTTP_408"
    df.loc[ind_cat_500, "category_lv4"] = "HTTP_500"
    df.loc[ind_cat_502, "category_lv4"] = "HTTP_502"
    df.loc[ind_cat_504, "category_lv4"] = "HTTP_504"
    df.loc[ind_other_status_code, "category_lv4"] = "HTTP_other"

    df.loc[ind_no_ns_record, "category_lv4"] = "No address found"
    df.loc[ind_refused_connection, "category_lv4"] = "Refused Connection"
    df.loc[ind_timeout, "category_lv4"] = "Timeout"
    df.loc[ind_no_status_code, "category_lv4"] = "No Status Code"

    df.loc[ind_registrar, "category_lv4"] = "Parked Notice Registrar"

    df.loc[ind_index, "category_lv4"] = "Index of"
    df.loc[ind_construction, "category_lv4"] = "Under construction"
    df.loc[ind_sale, "category_lv4"] = "For sale"
    df.loc[ind_starter, "category_lv4"] = "Starter"
    df.loc[ind_expired, "category_lv4"] = "Expired"
    df.loc[ind_blocked, "category_lv4"] = "Blocked"
    df.loc[ind_reserved, "category_lv4"] = "Reserved"
    df.loc[ind_ml_other, "category_lv4"] = "Parked Notice Individual Content"

    df.loc[ind_blank_page, "category_lv4"] = "Blank Page"

    ind_normal = df["category_lv4"].isnull()
    df.loc[ind_normal, "category_lv4"] = "High content"

    # WAVE 4: interstitial/infra gate override -- applied last so it wins over
    # every other rule above (HTTP-status buckets, park/ML classifier incl.
    # ml_feat_blocked, empty-page floor, High content fallback). This is the
    # override is_interstitial is meant to key off of; without it a page caught
    # by detect_interstitial() falls through to whatever ind_error-based rule
    # happens to match its comment text (e.g. "No Status Code"/Invalid Response)
    # instead of the dedicated Blocked/Undetermined bucket.
    # WAVE 5: same "applied last, wins over everything" reasoning as the
    # interstitial override above -- an ISP placeholder or archive.org
    # redirect must not fall through to Parked Notice Registrar/Individual
    # Content or High content just because it also happens to match one of
    # those rules' signals.
    if "is_isp_placeholder" in set_cols:
        ind_isp_placeholder = df["is_isp_placeholder"].apply(lambda x: str(x) in ["TRUE", True, "True"])
        df.loc[ind_isp_placeholder, "category_lv4"] = "ISP_Placeholder"

    if "is_archived_redirect" in set_cols:
        ind_archived_redirect = df["is_archived_redirect"].apply(lambda x: str(x) in ["TRUE", True, "True"])
        df.loc[ind_archived_redirect, "category_lv4"] = "Archived_Redirect"

    if "is_interstitial" in set_cols:
        ind_interstitial = df["is_interstitial"].apply(lambda x: str(x) in ["TRUE", True, "True"])
        df.loc[ind_interstitial, "category_lv4"] = "Blocked_Interstitial"

    # WAVE 6: thin-body bot-blocked-status gate -- independent of the
    # comment-derived ind_cat_403 etc. above (which only fire when the
    # "status code: NNN" text is present in `comment`) and independent of
    # is_interstitial (a content-pattern detector that doesn't catch every
    # case). Wave 3's retry/backoff can clear the error comment on a request
    # that still terminates on a bot-blocked status, leaving a thin
    # interstitial/challenge page that satisfies none of the rules above and
    # falls through to "High content". `all_status_codes` is built in
    # url_visitor.py as [terminal status] + [redirect history], so the first
    # token is the actual final status regardless of how many redirects
    # preceded it.
    # WAVE 7: scoped to RUN_CONFIG["BOT_BLOCKED_STATUS_CODES"] (403/429/503)
    # only, not the old combined list -- an origin-down terminal status
    # (520-527/530) is handled unconditionally by the Origin_Error gate right
    # below, which doesn't need (and shouldn't have) this word-count gate:
    # unlike a 403/429/503, there's no "genuine recovery that still shows an
    # earlier origin error in its history" case to guard against, since a
    # *terminal* origin-error status means the origin was down for the
    # response actually served.
    # Applied last, like the overrides above, so it wins over "High content";
    # gated on word count so genuine recoveries that still show a bot-blocked
    # status in their history aren't caught (see THIN_BLOCKED_PAGE_WORD_THRESHOLD).
    terminal_status = pd.Series("", index=df.index)
    if "all_status_codes" in set_cols:
        terminal_status = df["all_status_codes"].apply(
            lambda x: str(x).split("_")[0] if pd.notnull(x) and str(x) != "" else "")

    if "all_status_codes" in set_cols and "n_words" in set_cols:
        bot_blocked_status_strs = [str(c) for c in RUN_CONFIG["BOT_BLOCKED_STATUS_CODES"]]
        ind_terminal_bot_blocked_status = terminal_status.isin(bot_blocked_status_strs)
        n_words_numeric = pd.to_numeric(df["n_words"], errors="coerce")
        ind_thin_body = n_words_numeric <= THIN_BLOCKED_PAGE_WORD_THRESHOLD
        df.loc[ind_terminal_bot_blocked_status & ind_thin_body, "category_lv4"] = "Blocked_Interstitial"

    # WAVE 7: origin-down gate -- terminal status is one of Cloudflare's own
    # "origin server unreachable" edge errors (RUN_CONFIG["ORIGIN_ERROR_STATUS_CODES"]:
    # 520-527/530). Unconditional (no word-count gate, doesn't require
    # is_interstitial) because a *terminal* origin-error status is
    # authoritative on its own -- Cloudflare's edge served that status as the
    # final response, so there's no "genuine recovery" ambiguity the way
    # there is for 403/429/503 above. Applied last of all the override gates
    # so it wins over Blocked_Interstitial, the thin-body gate, HTTP_other,
    # and High content alike -- this is what keeps 52x/530 out of the
    # `category_lv3 = 'bot_blocked'` Proxyseller re-crawl worklist.
    if "all_status_codes" in set_cols:
        origin_error_status_strs = [str(c) for c in RUN_CONFIG["ORIGIN_ERROR_STATUS_CODES"]]
        ind_terminal_origin_error = terminal_status.isin(origin_error_status_strs)
        df.loc[ind_terminal_origin_error, "category_lv4"] = "Origin_Error"

    df["category_lv1"] = df["category_lv4"].apply(lambda x:DICO_NAMING_LV4[x][0])
    df["category_lv2"] = df["category_lv4"].apply(lambda x:DICO_NAMING_LV4[x][1])
    df["category_lv3"] = df["category_lv4"].apply(lambda x:DICO_NAMING_LV4[x][2])
    return df


def final_formatting(df, final_file_path):
    """ Derive final categories names and format final files"""
    plog.perf_go(f"Starting Final Formatting on {df}, {final_file_path}")
    df = df.copy(deep=True)

    # tld
    df["tld"] = df["url"].apply(lambda x: str(x).split(".")[-1])

    # parking
    if RUN_CONFIG["DO_CONTENT_CLASSIFICATION"]:
        plog.it(f"Performing Content Classification")
        try:
            df = final_parking_naming_v2(df)
        except Exception as e:
            plog.it(f"FAILURE! Catastrophic failure in content classification: {e}", is_error=True)
            plog.it(f"contents of df: {df}", is_error=True)
        plog.it(f"Content Classification Completed")

    # ads prediction
    # ind_link = df["has_ads_link"].apply(lambda x: float(x) == 1.0)
    # df.loc[ind_link, "pred_has_ads"] = "1"

    # Missing column ("in case there are no redirected page")
    for e in TABLEAU_COLUMNS:
        if e not in df.columns:
            df[e] = np.nan
    for e in DEBUG_COLUMNS:
        if e not in df.columns:
            df[e] = np.nan

    # input and target url
    df["input_url"] = df["url"]
    df["final_url"] = df["url"]
    ind_redirected = df["target_url"].notnull()
    df.loc[ind_redirected, "final_url"] = df.loc[ind_redirected, "target_url"]
    df["final_url"] = df["final_url"].apply(lambda x: str(x).replace("\n",""))
    df["target_url"] = df["target_url"].apply(lambda x: str(x).replace("\n",""))
    df["final_url"] = df["final_url"].str.replace("\t","")
    df["target_url"] = df["target_url"].str.replace("\t","")
    df["final_url"] = df["final_url"].str.replace("^I","")
    df["target_url"] = df["target_url"].str.replace("^I","")
    df["final_url"] = df["final_url"].str.replace(RUN_CONFIG['CSV_OUTPUT_DELIMITER'],"")
    df["target_url"] = df["target_url"].str.replace(RUN_CONFIG['CSV_OUTPUT_DELIMITER'],"")

    # reordering
    other_cols = [e for e in list(df.columns) if e not in DEBUG_COLUMNS]
    df = df[DEBUG_COLUMNS + other_cols]

    # save to file
    sep = RUN_CONFIG['CSV_OUTPUT_DELIMITER']
    plog.it(f'Saving CSV output to {final_file_path} using delimiter "{sep}"')
    df.to_csv(final_file_path[0:-4] + ".csv", sep=sep, encoding="utf-8-sig", index=False)
    # Original
    # df.to_csv(final_file_path[0:-4] + "_DEBUG.csv", sep=sep, encoding="utf-8-sig", index=False)

    plog.perf_end(f"Completed Final Formatting on {df}, {final_file_path}")


if __name__ == '__main__':
    f = join(os.path.dirname(__file__), "output", "language_full_results.csv")
    final_formatting(f, f[0:-4] + "TTTTTT.csv")
