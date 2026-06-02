import streamlit as st
import pickle
import os
import pandas as pd
import db
import requests
from urllib.parse import quote_plus
import html
import random
import math
import difflib
import re
import importlib
import json
import streamlit.components.v1 as components
try:
    import anthropic
except Exception:
    anthropic = None


try:
    db.init_db()
except Exception as e:
    st.error(f"Database initialization error: {e}")
    st.stop()

# One-time watchlist reset — remove after first successful run
try:
    db.reset_watchlist_table()
except Exception:
    pass

MOOD_MAP = {
    'Happy': {
        'emoji':       '😄',
        'keywords':    ['comedy', 'animation', 'family', 'musical', 'fun', 'joy', 'laugh', 'cheerful', 'light', 'bollywood', 'dance', 'music', 'celebrat'],
        'color':       '#f7c948',
        'description': "Movies to make you smile and laugh",
        'bg':          'rgba(247,201,72,0.08)',
        'border':      'rgba(247,201,72,0.25)',
    },
    'Sad': {
        'emoji':       '😢',
        'keywords':    ['drama', 'emotional', 'loss', 'grief', 'tear', 'melancholy', 'tragedy', 'heartbreak', 'death'],
        'color':       '#5b8dee',
        'description': "Feel all the feels with these emotional stories",
        'bg':          'rgba(91,141,238,0.08)',
        'border':      'rgba(91,141,238,0.25)',
    },
    'Thrilled': {
        'emoji':       '🤩',
        'keywords':    ['action', 'thriller', 'adventure', 'suspense', 'chase', 'explosion', 'spy', 'war', 'fight', 'hero'],
        'color':       '#E50914',
        'description': "Edge-of-your-seat action and thrills",
        'bg':          'rgba(229,9,20,0.08)',
        'border':      'rgba(229,9,20,0.25)',
    },
    'Romantic': {
        'emoji':       '💕',
        'keywords':    ['romance', 'love', 'wedding', 'relationship', 'kiss', 'couple', 'passion', 'heart', 'date', 'hindi', 'bollywood', 'pyaar'],
        'color':       '#ff6b9d',
        'description': "Love stories to warm your heart",
        'bg':          'rgba(255,107,157,0.08)',
        'border':      'rgba(255,107,157,0.25)',
    },
    'Scared': {
        'emoji':       '😱',
        'keywords':    ['horror', 'fear', 'ghost', 'monster', 'dark', 'supernatural', 'evil', 'haunted', 'zombie', 'curse'],
        'color':       '#9b59b6',
        'description': "Spine-chilling movies for the brave",
        'bg':          'rgba(155,89,182,0.08)',
        'border':      'rgba(155,89,182,0.25)',
    },
    'Inspired': {
        'emoji':       '💪',
        'keywords':    ['inspire', 'sport', 'biography', 'success', 'dream', 'motivat', 'overcome', 'champion', 'real', 'true', 'biopic', 'marathi', 'hindi'],
        'color':       '#2ecc71',
        'description': "True stories and journeys that motivate",
        'bg':          'rgba(46,204,113,0.08)',
        'border':      'rgba(46,204,113,0.25)',
    },
    'Curious': {
        'emoji':       '🧠',
        'keywords':    ['mystery', 'sci-fi', 'science', 'space', 'future', 'discover', 'detective', 'puzzle', 'conspiracy', 'mind'],
        'color':       '#1abc9c',
        'description': "Mind-bending stories for the thinkers",
        'bg':          'rgba(26,188,156,0.08)',
        'border':      'rgba(26,188,156,0.25)',
    },
    'Adventurous': {
        'emoji':       '🌍',
        'keywords':    ['adventure', 'journey', 'explore', 'travel', 'quest', 'fantasy', 'magic', 'world', 'epic', 'sword', 'hindi', 'period'],
        'color':       '#e67e22',
        'description': "Epic journeys and grand adventures",
        'bg':          'rgba(230,126,34,0.08)',
        'border':      'rgba(230,126,34,0.25)',
    },
}

st.set_page_config(
    page_title="MoodFlix - Premium Streaming UI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)
CSS_STYLES = r"""
<style>
section[data-testid="stMain"] .cm-navbar
[data-testid="stPopover"] > button > svg[data-testid="chevronDownIcon"] {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}

section[data-testid="stMain"] .cm-navbar
[data-testid="stPopover"] > button {
    padding: 7px 12px !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
    height: auto !important;
    min-width: 0 !important;
    overflow: hidden !important;
}
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800;900&display=swap');
/* UI FIX 5: global dark enforcement */
.stApp,
.stApp > *,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],
.main,
.block-container {
    background: transparent !important;
    background-color: transparent !important;
}
[data-testid="stHorizontalBlock"] > div,
[data-testid="column"] > div,
[data-testid="stVerticalBlock"] > div {
    background: transparent !important;
    background-color: transparent !important;
}
[data-testid="stContainer"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
}
input[type="text"],
input[type="search"],
.stTextInput input {
    background: rgba(255,255,255,0.06) !important;
    background-color: rgba(255,255,255,0.06) !important;
    color: #eef0f3 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 50px !important;
    box-shadow: none !important;
}
input[type="text"]:focus,
input[type="search"]:focus,
.stTextInput input:focus {
    background: rgba(255,255,255,0.08) !important;
    background-color: rgba(255,255,255,0.08) !important;
    border-color: rgba(229,9,20,0.5) !important;
    box-shadow: 0 0 0 3px rgba(229,9,20,0.12) !important;
    outline: none !important;
}

/* UI FIX 1: iframe/component background */
iframe {
    background: transparent !important;
    background-color: transparent !important;
    color-scheme: dark !important;
    border: none !important;
    outline: none !important;
}
[data-testid="stComponentContainer"],
[data-testid="stComponentContainer"] > div {
    background: transparent !important;
    background-color: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
}
.element-container:has(iframe) {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* UI FIX 3: remove red outline on components */
iframe:focus,
iframe:focus-visible,
[data-testid="stComponentContainer"]:focus,
[data-testid="stComponentContainer"]:focus-visible {
    outline: none !important;
    border: none !important;
    box-shadow: none !important;
}
.stComponentContainer,
div:has(> iframe) {
    outline: none !important;
    border: none !important;
}

/* UI FIX 6: component wrapper */
div[data-testid="stComponentContainer"] iframe {
    background: transparent !important;
    border: none !important;
    outline: none !important;
}

/* UI FIX 4: navbar icon buttons */
.cm-nav-icon-btn {
    display: flex !important;
    align-items: center !important;
    gap: 2px !important;
    background: rgba(255, 255, 255, 0.06) !important;
    background-color: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 50px !important;
    padding: 6px 12px !important;
    cursor: pointer !important;
    transition: background 0.2s ease !important;
    color: #eef0f3 !important;
    position: relative !important;
    box-shadow: none !important;
    -webkit-appearance: none !important;
    appearance: none !important;
}
.cm-nav-icon-btn:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    border-color: rgba(255, 255, 255, 0.15) !important;
}
.cm-notif-dot {
    position: absolute !important;
    top: 4px !important;
    right: 10px !important;
    width: 7px !important;
    height: 7px !important;
    background: #E50914 !important;
    border-radius: 50% !important;
    border: 1.5px solid #05060a !important;
}
.cm-navbar button,
.cm-navbar .stButton button,
.cm-navbar [data-testid="baseButton-secondary"],
.cm-navbar [data-testid="baseButton-primary"] {
    background: rgba(255,255,255,0.06) !important;
    background-color: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #eef0f3 !important;
    border-radius: 50px !important;
    box-shadow: none !important;
}
.cm-navbar [data-testid="stPopover"],
.cm-navbar [data-testid="stPopover"] > div {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}
.cm-navbar [data-testid="stPopover"] > button {
    background: rgba(255,255,255,0.06) !important;
    background-color: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 50px !important;
    color: #eef0f3 !important;
    box-shadow: none !important;
}
* {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
}
:root{
    --bg-900:#05060a;
    --bg-800:#0b0f1a;
    --accent:#E50914;
    --accent-2:#ff6b6b;
    --muted:#bdbdbd;
    --panel:rgba(12,16,26,0.72);
    --panel-border:rgba(255,255,255,0.06);
    --glass: rgba(255,255,255,0.03);
}
*{box-sizing:border-box}
html,body,#root, .appview-container, .main {background:linear-gradient(180deg,var(--bg-900),var(--bg-800)) !important;}
body {font-family: 'Poppins', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; color: #eef0f3}
header, .reportview-container .main header {display:none !important}
.stApp > header {display:none !important}
.stApp{animation:cmFadeIn .42s cubic-bezier(.22,.9,.15,1) both}
.css-18e3th9 {padding:0 !important}

/* Streamlit default spacing reset */
.block-container {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}
header {
    visibility: hidden;
}
.main {
    padding-top: 0rem !important;
}

[data-testid="stAppViewContainer"] .main .block-container{
    margin-top:0 !important;
    padding-top:0 !important;
}

@media (prefers-reduced-motion: reduce){
    .stApp{animation:none}
    *{transition:none !important}
}

@keyframes cmFadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
@keyframes cmPulseGlow{0%,100%{box-shadow:0 0 0 rgba(229,9,20,0)}50%{box-shadow:0 0 20px rgba(229,9,20,0.12)}}
@keyframes cmBellRing{0%{transform:rotate(0deg)}15%{transform:rotate(8deg)}30%{transform:rotate(-6deg)}45%{transform:rotate(5deg)}60%{transform:rotate(-3deg)}75%{transform:rotate(2deg)}100%{transform:rotate(0deg)}}

/* ── NAVBAR ── */
.cm-navbar {
    position: sticky;
    top: 0;
    left: 0;
    right: 0;
    height: 96px;
    z-index: 99999;
    background: #0d0d0d;
    border-bottom: 2px solid rgba(229,9,20,0.5);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 0 40px;
}
/* Target the real Streamlit navbar block */
.block-container > div:first-child > div:first-child > div:first-child
> div[data-testid="stHorizontalBlock"] {
    min-height: 90px !important;
    padding-top: 20px !important;
    padding-bottom: 20px !important;
    padding-left: 32px !important;
    padding-right: 32px !important;
    background: rgba(9,12,20,0.97) !important;
    backdrop-filter: blur(20px) !important;
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 99999 !important;
    align-items: center !important;
}

/* Make each column inside navbar vertically centered */
.block-container > div:first-child > div:first-child > div:first-child
> div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    display: flex !important;
    align-items: center !important;
}
[data-testid="stHorizontalBlock"]:first-of-type {
    min-height: 88px !important;
    align-items: center !important;
    padding: 0 16px !important;
    background: rgba(9,12,20,0.97) !important;
    backdrop-filter: blur(20px) !important;
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 99999 !important;
}
.cm-navbar::after {
    display: none;
}
.cm-logo {
    font-family: Georgia, serif;
    font-size: 28px;
    font-weight: 900;
    letter-spacing: 0px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0px;
    border-bottom: 3px solid #E50914;
    margin-right: 20px;
    padding-bottom: 3px;
}
.cm-logo-mood {
    color: #ffffff;
}
.cm-logo-flix {
    color: #E50914;
}

/* Nav buttons — all five unified */
div.st-key-nav_home button,
div.st-key-nav_movies button,
div.st-key-nav_popular button,
div.st-key-nav_spin button,
div.st-key-nav_chat button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #bdbdbd !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 14px 22px !important;
    border-radius: 999px !important;
    white-space: nowrap !important;
    transition: all 0.18s ease !important;
    font-family: 'Poppins', sans-serif !important;
    box-shadow: none !important;
    letter-spacing: -0.1px !important;
    width: 100% !important;
    min-height: 52px !important;
    line-height: 1.2 !important;
}
div.st-key-nav_home button:hover,
div.st-key-nav_movies button:hover,
div.st-key-nav_popular button:hover,
div.st-key-nav_spin button:hover,
div.st-key-nav_chat button:hover {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #fff !important;
    transform: translateY(-1px) !important;
}


/* UI FIX 2: input dark style */
/* Search column wrapper */
div.stElementContainer.st-key-navbar_movie_search {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    background-color: transparent !important;
    width: 240px !important;
}

/* Hide label */
div.stElementContainer.st-key-navbar_movie_search label {
    display: none !important;
    height: 0 !important;
}

/* Input wrapper — pill shape */
div.stElementContainer.st-key-navbar_movie_search > div {
    background: transparent !important;
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
}
div.stElementContainer.st-key-navbar_movie_search > div > div {
    background: rgba(255,255,255,0.06) !important;
    background-color: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 20px !important;
    height: 48px !important;
    padding: 7px 16px !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
    position: relative !important;
    outline: none !important;
    color-scheme: dark !important;
    width: 240px !important;
}
div.stElementContainer.st-key-navbar_movie_search > div > div::before {
    content: '🔍' !important;
    position: absolute !important;
    left: 10px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    font-size: 12px !important;
    pointer-events: none !important;
    z-index: 1 !important;
    opacity: 0.55 !important;
}
div.stElementContainer.st-key-navbar_movie_search > div > div:focus-within {
    background: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.18) !important;
    box-shadow: none !important;
}

/* Actual input field */
div.stElementContainer.st-key-navbar_movie_search input {
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    color: rgba(255,255,255,0.3) !important;
    font-size: 14px !important;
    font-family: 'Poppins', sans-serif !important;
    font-weight: 500 !important;
    height: 48px !important;
    padding: 0 !important;
    text-indent: 0 !important;
    caret-color: rgba(255,255,255,0.6) !important;
    color-scheme: dark !important;
    width: 100% !important;
}
div.stElementContainer.st-key-navbar_movie_search input:-webkit-autofill,
div.stElementContainer.st-key-navbar_movie_search input:-webkit-autofill:hover,
div.stElementContainer.st-key-navbar_movie_search input:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0px 1000px rgba(20,20,30,0.98) inset !important;
    -webkit-text-fill-color: #eef0f3 !important;
    caret-color: #eef0f3 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    transition: background-color 5000s ease-in-out 0s !important;
}

/* Remove any stray white background around navbar inputs */
.cm-navbar .stTextInput,
.cm-navbar .stTextInput > div,
.cm-navbar .stTextInput > div > div,
.cm-navbar .stTextInput input {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}
/* Fix white background on search input */
div.stElementContainer.st-key-navbar_movie_search > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 20px !important;
}

/* Force dark background on input field itself */
div.stElementContainer.st-key-navbar_movie_search input {
    background: transparent !important;
    background-color: transparent !important;
    color: rgba(255,255,255,0.3) !important;
    -webkit-box-shadow: none !important;
    box-shadow: none !important;
}

/* Remove Streamlit's default white autofill background */
div.stElementContainer.st-key-navbar_movie_search input:-webkit-autofill,
div.stElementContainer.st-key-navbar_movie_search input:-webkit-autofill:hover,
div.stElementContainer.st-key-navbar_movie_search input:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0px 1000px rgba(20,22,32,0.98) inset !important;
    -webkit-text-fill-color: #eef0f3 !important;
    caret-color: #E50914 !important;
    border-radius: 999px !important;
}

/* Remove ALL Streamlit default styling on the input wrapper */
div.stElementContainer.st-key-navbar_movie_search [data-baseweb="input"] {
    background: transparent !important;
    background-color: transparent !important;
}
div.stElementContainer.st-key-navbar_movie_search [data-baseweb="base-input"] {
    background: transparent !important;
    background-color: transparent !important;
}

/* Override Streamlit theme light background */
div.stElementContainer.st-key-navbar_movie_search * {
    background-color: transparent !important;
}
div.stElementContainer.st-key-navbar_movie_search > div > div {
    background-color: rgba(255,255,255,0.06) !important;
    height: 48px !important;
    border-radius: 999px !important;
}
div.stElementContainer.st-key-navbar_movie_search input::placeholder {
    color: rgba(255,255,255,0.3) !important;
    font-size: 13px !important;
}
div.stElementContainer.st-key-navbar_movie_search input {
    height: 48px !important;
    font-size: 14px !important;
    padding: 0 16px !important;
}

/* Remove default Streamlit focus ring */
div.stElementContainer.st-key-navbar_movie_search [data-focused="true"],
div.stElementContainer.st-key-navbar_movie_search > div > div:focus {
    box-shadow: none !important;
    outline: none !important;
}

/* Hide any extra icons Streamlit adds inside input */
div.stElementContainer.st-key-navbar_movie_search svg,
div.stElementContainer.st-key-navbar_movie_search
    [data-testid="InputInstructions"] {
    display: none !important;
}

/* Bell popover — clean circle */
.cm-bell-slot [data-testid="stPopover"] > button {
    min-width: 54px !important;
    padding: 9px 12px !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
    font-size: 24px !important;
    color: #fff !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0 !important;
    overflow: hidden !important;
    transition: all 0.18s ease !important;
    height: 54px !important;
    width: 54px !important;
}
.cm-bell-slot [data-testid="stPopover"] > button:hover {
    background: rgba(255,255,255,0.08) !important;
}
.cm-bell-slot [data-testid="stPopover"] {
    position:relative !important;
}
.cm-bell-slot [data-testid="stPopover"]::after {
    content: '3' !important;
    position: absolute !important;
    top: -4px !important;
    right: -4px !important;
    min-width: 16px !important;
    height: 16px !important;
    padding: 0 4px !important;
    background: #E50914 !important;
    border-radius: 999px !important;
    color: #ffffff !important;
    font-size: 10px !important;
    font-weight: 800 !important;
    line-height: 16px !important;
    text-align: center !important;
    pointer-events: none !important;
    z-index: 99 !important;
}

/* Avatar popover — glowing circle, NO label */
.cm-account-slot [data-testid="stPopover"] > button {
    min-width: 54px !important;
    padding: 9px 14px !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0 !important;
    overflow: hidden !important;
    transition: all 0.2s ease !important;
    line-height: 1 !important;
    position: relative !important;
    animation: none !important;
    height: 54px !important;
    width: 54px !important;
}
.cm-account-slot [data-testid="stPopover"] > button:hover {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.16) !important;
    transform: none !important;
    box-shadow: none !important;
}
@keyframes avatarPulse {
    0%,100%{box-shadow:0 0 0 0 rgba(229,9,20,0);}
    50%{box-shadow:0 0 10px rgba(229,9,20,0.2);}
}

/* HIDE chevrons and "Profile" label text completely */
div[data-testid="stPopover"] > button > p,
div[data-testid="stPopover"] > button > div,
div[data-testid="stPopover"] > button > svg,
div[data-testid="stPopover"] > button > span > svg,
div[data-testid="stPopover"] svg[data-testid="chevronDownIcon"],
div[data-testid="stPopover"] svg[data-baseweb="icon"],
div[data-testid="stPopover"] [data-testid="stMarkdownContainer"],
div[data-testid="stPopover"] > button [data-baseweb="icon"] {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stPopover"] > button {
    gap: 0 !important;
    justify-content: center !important;
    overflow: hidden !important;
}
.cm-account-slot div[data-testid="stPopover"] > button:hover{
    transform: none !important;
    border-color: rgba(255,255,255,0.16) !important;
    background: rgba(255,255,255,0.08) !important;
}

.cm-notification-list{display:flex;flex-direction:column;gap:10px;margin-top:10px}
.cm-notification-item{padding:12px 14px;border-radius:12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);color:#fff;font-size:13px;line-height:1.45}
.cm-notification-item strong{display:block;margin-bottom:4px}

.cm-auth-panel{margin:30px 0 10px 0;padding:22px;border-radius:14px;background:linear-gradient(180deg, rgba(12,16,28,0.98), rgba(15,20,35,0.98));border:1px solid rgba(255,255,255,0.04);box-shadow:0 12px 40px rgba(0,0,0,0.36)}
.cm-auth-panel .stTabs [data-baseweb="tab-list"]{gap:10px}
.cm-auth-panel .stTabs [data-baseweb="tab"]{background:rgba(255,255,255,0.02);color:#fff;border-radius:10px;padding:10px 16px}
.cm-auth-panel .stTabs [aria-selected="true"]{background:linear-gradient(90deg,rgba(229,9,20,0.14),rgba(255,95,109,0.06)) !important;color:#fff !important}
.cm-auth-panel input{background:rgba(255,255,255,0.02) !important;color:#fff !important;border:1px solid rgba(255,255,255,0.06) !important}
.cm-auth-panel label{color:#fff !important}
.cm-auth-panel .stForm{background:transparent !important}
.cm-auth-panel .stButton > button{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;border:none}
.cm-auth-panel .stButton > button:hover{background:linear-gradient(135deg,#ff3b3b,#ff6b6b);color:#fff}

/* User details box */
.cm-user-details-box {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 12px 14px;
    margin: 10px 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.cm-user-detail-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}
.cm-detail-label {
    color: #6b7280;
    font-size: 11.5px;
    font-weight: 500;
    flex-shrink: 0;
}
.cm-detail-value {
    color: #e9edf2;
    font-size: 12px;
    font-weight: 600;
    text-align: right;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 160px;
}

/* Logout button */
div.st-key-logout_btn button {
    background: linear-gradient(135deg,
        rgba(229,9,20,0.15), rgba(255,95,109,0.08)) !important;
    border: 1px solid rgba(229,9,20,0.25) !important;
    color: #ff6b6b !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    transition: all 0.18s ease !important;
    margin: 6px 0 !important;
}
div.st-key-logout_btn button:hover {
    background: linear-gradient(135deg,
        rgba(229,9,20,0.3), rgba(255,95,109,0.18)) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(229,9,20,0.2) !important;
}

/* Users section header */
.cm-users-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 12px 0 8px 0;
}
.cm-users-title {
    color: #fff;
    font-size: 13px;
    font-weight: 700;
}
.cm-users-badge {
    background: rgba(229,9,20,0.15);
    border: 1px solid rgba(229,9,20,0.25);
    color: #ff6b6b;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 9px;
    border-radius: 999px;
}

/* User row */
.cm-user-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
}
.cm-user-row-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg,
        rgba(229,9,20,0.2), rgba(255,95,109,0.12));
    border: 1px solid rgba(229,9,20,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: 800;
    font-size: 13px;
    flex-shrink: 0;
}
.cm-user-row-name {
    color: #e9edf2;
    font-size: 12.5px;
    font-weight: 600;
}
.cm-user-row-email {
    color: #6b7280;
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 160px;
}

/* Delete button */
div[class*="st-key-confirm_yes_"] button {
    background: rgba(46,204,113,0.15) !important;
    border: 1px solid rgba(46,204,113,0.3) !important;
    color: #2ecc71 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
    min-height: 36px !important;
    padding: 4px 8px !important;
    letter-spacing: 0px !important;
}
div[class*="st-key-confirm_no_"] button {
    background: rgba(229,9,20,0.10) !important;
    border: 1px solid rgba(229,9,20,0.25) !important;
    color: #ff6b6b !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
    min-height: 36px !important;
    padding: 4px 8px !important;
    letter-spacing: 0px !important;
}
div[class*="st-key-confirm_yes_"] button:hover {
    background: rgba(46,204,113,0.25) !important;
    transform: translateY(-1px) !important;
}
div[class*="st-key-confirm_no_"] button:hover {
    background: rgba(229,9,20,0.2) !important;
    transform: translateY(-1px) !important;
}

/* Delete icon button — fixed size */
div[class*="st-key-del_user_"] button {
    background: rgba(229,9,20,0.08) !important;
    border: 1px solid rgba(229,9,20,0.15) !important;
    color: #ff6b6b !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 4px !important;
    min-height: 36px !important;
    min-width: 36px !important;
    width: 36px !important;
    white-space: nowrap !important;
    transition: all 0.15s ease !important;
}
div[class*="st-key-del_user_"] button:hover {
    background: rgba(229,9,20,0.2) !important;
    transform: scale(1.08) !important;
}

/* Confirm box */
.cm-del-confirm {
    background: rgba(229,9,20,0.07);
    border: 1px solid rgba(229,9,20,0.18);
    border-radius: 8px;
    padding: 7px 10px;
    color: #ff6b6b;
    font-size: 12px;
    margin: 6px 0 4px 0;
    white-space: nowrap;
}
.cm-del-confirm strong {
    color: #fff;
    font-weight: 700;
}

div.st-key-nav_profile button,
div.st-key-nav_profile,
div[data-testid="stColumn"]:has(div.st-key-nav_profile) * {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    white-space: nowrap !important;
}

/* New & Popular tab styling */
.stTabs [data-baseweb="tab-list"]{gap:8px;background:transparent;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:2px}
.stTabs [data-baseweb="tab"]{background:transparent;color:#bdbdbd;border-radius:8px 8px 0 0;padding:10px 20px;font-weight:600;font-size:14px;border:none;transition:all .18s ease}
.stTabs [aria-selected="true"]{background:linear-gradient(180deg, rgba(229,9,20,0.12), transparent) !important;color:#fff !important;border-bottom:2px solid #E50914 !important}
.stTabs [data-baseweb="tab"]:hover{color:#fff;background:rgba(255,255,255,0.03)}

.cm-genre-pills{display:flex;flex-wrap:nowrap;gap:10px;overflow-x:auto;padding:8px 4px 16px 4px;scrollbar-width:none;-ms-overflow-style:none}
.cm-genre-pills::-webkit-scrollbar{display:none}
.cm-genre-pill{display:inline-flex;align-items:center;justify-content:center;white-space:nowrap;padding:9px 20px;border-radius:999px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);color:#bdbdbd;font-size:13px;font-weight:600;text-decoration:none;cursor:pointer;flex-shrink:0;transition:all .18s ease;font-family:'Poppins', sans-serif;letter-spacing:.2px}
.cm-genre-pill:hover{background:rgba(229,9,20,0.12);border-color:rgba(229,9,20,0.3);color:#fff;transform:translateY(-2px)}
.cm-genre-pill-active{background:linear-gradient(135deg, rgba(229,9,20,0.85), rgba(255,95,109,0.65)) !important;border-color:transparent !important;color:#fff !important;box-shadow:0 4px 18px rgba(229,9,20,0.3)}
.cm-genre-pill-active:hover{transform:translateY(-2px);box-shadow:0 6px 22px rgba(229,9,20,0.4)}

/* Remove white wrapper around bell popover */
.cm-bell-slot > div,
.cm-bell-slot > div > div,
.cm-bell-slot [data-testid="stPopover"],
.cm-bell-slot [data-testid="stPopover"] > div,
.cm-account-slot > div,
.cm-account-slot > div > div,
.cm-account-slot [data-testid="stPopover"],
.cm-account-slot [data-testid="stPopover"] > div{
    background:transparent !important;
    background-color:transparent !important;
    border:none !important;
    box-shadow:none !important;
    padding:0 !important;
}

/* Remove white wrapper around avatar popover */
.cm-avatar-slot > div,
.cm-avatar-slot > div > div,
.cm-avatar-slot [data-testid="stPopover"],
.cm-avatar-slot [data-testid="stPopover"] > div{
    background:transparent !important;
    background-color:transparent !important;
    border:none !important;
    box-shadow:none !important;
    padding:0 !important;
}


.cm-main{margin-top:28px;margin-left:0;padding:40px 60px 120px 60px}

.cm-hero{position:relative;border-radius:24px;overflow:hidden;height:580px;background:linear-gradient(180deg, rgba(0,0,0,0.18), rgba(0,0,0,0.6));display:flex;align-items:flex-end;padding:48px;box-shadow:0 18px 60px rgba(0,0,0,0.6)}
.cm-hero .backdrop{position:absolute;inset:0;background-size:cover;background-position:center;filter:contrast(1.05) saturate(1.06) brightness(0.84);transform:scale(1.02);z-index:1}
.cm-hero .hero-poster{position:absolute;left:56px;bottom:48px;height:84%;width:auto;z-index:2;border-radius:14px;box-shadow:0 26px 70px rgba(0,0,0,0.8);object-fit:contain;transition:transform .36s ease}
.cm-hero:hover .hero-poster{transform:translateY(-8px)}
.cm-hero .overlay{position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,15,26,0.05) 0%, rgba(11,15,26,0.9) 60%);z-index:3}
.cm-hero .hero-content{position:relative;z-index:4;max-width:820px;padding:36px;margin-left:300px}
.cm-hero h1{font-size:52px;margin:0 0 18px 0;font-weight:900;color:#fff;letter-spacing:-0.6px;line-height:1.06}
.cm-hero p.tag{color:var(--muted);font-size:16px;margin-bottom:22px;line-height:1.5;font-weight:500}
.cm-hero .hero-cta{display:flex;gap:16px;align-items:center}
.btn-play{display:inline-flex;align-items:center;justify-content:center;text-decoration:none;background:linear-gradient(135deg,var(--accent),var(--accent-2));border:none;color:#fff;padding:12px 28px;border-radius:10px;font-weight:800;font-size:15px;box-shadow:0 10px 30px rgba(229,9,20,0.22);cursor:pointer;transition:all 0.18s ease;letter-spacing:0.2px}
.btn-play:hover{transform:translateY(-3px);box-shadow:0 14px 36px rgba(229,9,20,0.38);color:#fff !important}
.btn-list{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);color:#fff;padding:12px 28px;border-radius:10px;font-weight:700;font-size:15px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center}
.btn-list:hover{background:rgba(255,255,255,0.07);border-color:var(--accent)}

.cm-section{margin-top:56px;margin-bottom:20px}
.cm-section .section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;padding:0 8px}
.cm-section .title{font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.4px}
.cm-carousel{display:flex;gap:18px;overflow-x:auto;padding:12px 8px;scrollbar-width:none}
.cm-carousel::-webkit-scrollbar{height:8px}
.cm-carousel::-webkit-scrollbar-track{background:transparent;border-radius:10px}
.cm-carousel::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.10);border-radius:10px}

.card{min-width:220px;max-width:220px;border-radius:14px;overflow:hidden;background:linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.005));border:1px solid rgba(255,255,255,0.04);backdrop-filter:blur(6px);transition:transform .32s cubic-bezier(.2,.9,.2,1), box-shadow .32s;position:relative}
.card-img-container{width:100%;height:330px;overflow:hidden;position:relative;background:linear-gradient(135deg,#14141b,#10141f)}
.card img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .36s ease}
.card:hover img{transform:scale(1.06)}
.card-poster-link{display:block;position:relative;overflow:hidden;border-radius:12px 12px 0 0;cursor:pointer;text-decoration:none;z-index:3}
.card-play-overlay{position:absolute;inset:0;background:rgba(0,0,0,0);display:flex;align-items:center;justify-content:center;transition:background 0.22s ease;border-radius:12px 12px 0 0}
.card:hover .card-play-overlay{background:rgba(0,0,0,0.45)}
.card-play-icon{width:52px;height:52px;border-radius:50%;background:rgba(229,9,20,0.9);display:flex;align-items:center;justify-content:center;font-size:20px;color:#fff;opacity:0;transform:scale(0.7);transition:all 0.22s cubic-bezier(0.22,0.9,0.15,1);box-shadow:0 8px 28px rgba(229,9,20,0.5);padding-left:3px}
.card:hover .card-play-icon{opacity:1;transform:scale(1)}
.card-trailer{position:absolute;left:12px;bottom:52px;background:rgba(229,9,20,0.85);color:#fff !important;text-decoration:none;font-size:11px;font-weight:700;padding:5px 11px;border-radius:6px;opacity:0;transform:translateY(6px);transition:opacity 0.18s ease, transform 0.18s ease;z-index:6;white-space:nowrap;letter-spacing:0.2px;box-shadow:0 4px 14px rgba(229,9,20,0.4)}
.card:hover .card-trailer{opacity:1;transform:translateY(0)}
.card-trailer:hover{background:#E50914 !important;box-shadow:0 6px 18px rgba(229,9,20,0.6) !important;transform:translateY(-2px) !important}
.card-recommend{position:absolute;left:12px;bottom:12px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);color:#fff !important;text-decoration:none;font-size:11px;font-weight:700;padding:5px 11px;border-radius:6px;opacity:0;transform:translateY(6px);transition:opacity 0.18s ease, transform 0.18s ease, background 0.18s ease;z-index:6;white-space:nowrap;letter-spacing:0.2px}
.card:hover .card-recommend{opacity:1;transform:translateY(0)}
.card-recommend:hover{background:rgba(255,255,255,0.14) !important;transform:translateY(-2px) !important}
.card-add{position:absolute;right:12px;bottom:12px;background:linear-gradient(135deg,var(--accent),var(--accent-2));padding:7px 13px;border-radius:8px;color:#fff !important;text-decoration:none;font-weight:700;font-size:11.5px;opacity:0;transform:translateY(8px);transition:opacity 0.18s ease, transform 0.18s ease;z-index:6;white-space:nowrap}
.card:hover .card-add{opacity:1;transform:translateY(0)}
.card-poster{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.3s ease}
.card:hover .card-poster{transform:scale(1.04)}
.card-rating{position:absolute;top:10px;left:10px;z-index:7}
.heart{z-index:7}
.card .card-add{position:absolute;right:12px;bottom:12px;background:linear-gradient(135deg,var(--accent),var(--accent-2));padding:8px 14px;border-radius:8px;color:#fff;text-decoration:none;font-weight:700;font-size:12px;opacity:0;transform:translateY(8px);transition:opacity .18s ease, transform .18s ease, box-shadow .18s ease;z-index:5;white-space:nowrap}
.card:hover .card-add{opacity:1;transform:translateY(0);box-shadow:0 6px 18px rgba(229,9,20,0.4)}
.card-add:hover{box-shadow:0 8px 24px rgba(229,9,20,0.55) !important;transform:translateY(-2px) !important}
.card .meta{padding:14px}
.badge{position:absolute;left:12px;top:12px;background:rgba(0,0,0,0.6);color:#fff;padding:8px 12px;border-radius:8px;font-weight:800;font-size:13px}
.heart{position:absolute;right:12px;top:12px;background:rgba(0,0,0,0.55);padding:10px;border-radius:50%;cursor:pointer;transition:transform .18s ease, background .22s ease;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;font-size:16px;width:38px;height:38px;z-index:5;color:#fff}
.heart:hover{background:rgba(229,9,20,0.82) !important;transform:scale(1.15)}
.card:hover{transform:translateY(-10px);box-shadow:0 20px 48px rgba(0,0,0,0.6)}
.card .title{font-weight:800;color:#fff;font-size:15px;margin-bottom:6px;line-height:1.28}
.card .sub{color:var(--muted);font-size:13px;opacity:0.9}

/* Mood section header */
.cm-mood-header {
    margin: 32px 0 16px 0;
}
.cm-mood-sub {
    color: #bdbdbd;
    font-size: 13px;
    margin: 4px 0 0 0;
}

/* Mood buttons base */
div[class*="st-key-mood_btn_"] button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #bdbdbd !important;
    border-radius: 999px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 0 !important;
    transition: all 0.2s ease !important;
    font-family: 'Poppins', sans-serif !important;
    box-shadow: none !important;
    white-space: nowrap !important;
}
div[class*="st-key-mood_btn_"] button:hover {
    background: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: #fff !important;
    transform: translateY(-2px) !important;
}

/* Mood result banner */
.cm-mood-result {
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(255,255,255,0.02);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 16px 0 8px 0;
    border: 1px solid rgba(255,255,255,0.05);
}

/* Section title shared style */
.cm-section-title {
    color: #fff;
    font-size: 20px;
    font-weight: 800;
    margin: 0 0 4px 0;
    letter-spacing: -0.3px;
}

/* Because You Watched section */
.cm-byw-header {
    margin: 32px 0 12px 0;
}
.cm-byw-sub {
    color: #bdbdbd;
    font-size: 13px;
    margin: 4px 0 0 0;
}

/* Source movie badge */
.cm-byw-source {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 18px 0 6px 0;
    padding: 10px 16px;
    background: rgba(255,255,255,0.02);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.05);
    border-left: 3px solid #E50914;
}
.cm-byw-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #E50914;
    flex-shrink: 0;
    box-shadow: 0 0 8px rgba(229,9,20,0.6);
    animation: bywPulse 2s ease-in-out infinite;
}
@keyframes bywPulse {
    0%, 100% { box-shadow: 0 0 4px rgba(229,9,20,0.4); }
    50%       { box-shadow: 0 0 12px rgba(229,9,20,0.8); }
}
.cm-byw-label {
    color: #bdbdbd;
    font-size: 12px;
    font-weight: 500;
}
.cm-byw-title {
    color: #fff;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: -0.2px;
}

/* AI Chat page */
.cm-chat-suggestions-label {
    color: #bdbdbd;
    font-size: 12px;
    font-weight: 600;
    margin: 12px 0 10px 0;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* Suggestion buttons */
div[class*="st-key-suggestion_"] button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    color: #bdbdbd !important;
    border-radius: 12px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 10px 8px !important;
    text-align: left !important;
    transition: all 0.18s ease !important;
    font-family: 'Poppins', sans-serif !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 52px !important;
    line-height: 1.4 !important;
}
div[class*="st-key-suggestion_"] button:hover {
    background: rgba(229,9,20,0.08) !important;
    border-color: rgba(229,9,20,0.2) !important;
    color: #fff !important;
    transform: translateY(-2px) !important;
}

/* Chat container */
.cm-chat-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 20px 0;
    max-height: 520px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(229,9,20,0.3) transparent;
}
.cm-chat-container::-webkit-scrollbar { width: 4px; }
.cm-chat-container::-webkit-scrollbar-thumb {
    background: rgba(229,9,20,0.3);
    border-radius: 999px;
}

/* Chat bubbles */
.cm-chat-bubble {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    animation: bubbleIn 0.25s ease both;
}
@keyframes bubbleIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.cm-chat-bubble.cm-chat-user {
    flex-direction: row-reverse;
}

/* Avatars */
.cm-chat-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
}
.cm-chat-avatar-user {
    background: linear-gradient(135deg,rgba(229,9,20,0.6),rgba(255,95,109,0.4));
    border: 1.5px solid rgba(229,9,20,0.4);
}
.cm-chat-avatar-ai {
    background: linear-gradient(135deg,rgba(26,188,156,0.3),rgba(52,152,219,0.2));
    border: 1.5px solid rgba(26,188,156,0.3);
}

/* Message text bubbles */
.cm-chat-text {
    max-width: 72%;
    padding: 14px 18px;
    border-radius: 16px;
    font-size: 13.5px;
    line-height: 1.65;
    font-family: 'Poppins', sans-serif;
}
.cm-chat-text-user {
    background: linear-gradient(135deg,rgba(229,9,20,0.25),rgba(255,95,109,0.15));
    border: 1px solid rgba(229,9,20,0.2);
    color: #fff;
    border-bottom-right-radius: 4px;
}
.cm-chat-text-ai {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    color: #e9edf2;
    border-bottom-left-radius: 4px;
}

/* Chat message container dark theme */
div[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 4px 0 !important;
}

/* User message bubble */
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
div[data-testid="stMarkdownContainer"] {
    background: linear-gradient(135deg,rgba(229,9,20,0.2),rgba(255,95,109,0.12)) !important;
    border: 1px solid rgba(229,9,20,0.2) !important;
    border-radius: 16px 16px 4px 16px !important;
    padding: 12px 16px !important;
    color: #fff !important;
    font-size: 13.5px !important;
    max-width: 70% !important;
    margin-left: auto !important;
}

/* AI message bubble */
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
div[data-testid="stMarkdownContainer"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 16px 16px 16px 4px !important;
    padding: 12px 16px !important;
    color: #e9edf2 !important;
    font-size: 13.5px !important;
    max-width: 75% !important;
}

/* Bold text inside AI bubble */
div[data-testid="stChatMessage"] strong {
    color: #fff !important;
    font-weight: 800 !important;
}

/* Italic text inside AI bubble */
div[data-testid="stChatMessage"] em {
    color: #bdbdbd !important;
    font-style: italic !important;
}

/* Avatar circles */
div[data-testid="stChatMessage"]
img[data-testid="chatAvatarIcon-user"],
div[data-testid="stChatMessage"]
img[data-testid="chatAvatarIcon-assistant"] {
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
}

/* st.chat_input styling */
div[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 14px !important;
    padding: 4px 8px !important;
}
div[data-testid="stChatInput"]:focus-within {
    border-color: rgba(229,9,20,0.4) !important;
    box-shadow: 0 0 0 3px rgba(229,9,20,0.08) !important;
}
div[data-testid="stChatInput"] textarea {
    color: #fff !important;
    font-size: 13.5px !important;
    font-family: 'Poppins', sans-serif !important;
    background: transparent !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #6b7280 !important;
}
/* Send button inside chat_input */
div[data-testid="stChatInput"] button {
    background: linear-gradient(135deg,#E50914,#ff6b6b) !important;
    border-radius: 8px !important;
    border: none !important;
    color: #fff !important;
}

/* Autocomplete dropdown container */
.cm-autocomplete {
    position: absolute !important;
    top: 48px !important;
    left: 0 !important;
    right: 0 !important;
    min-width: 320px !important;
    max-width: 460px !important;
    background: rgba(10,13,22,0.98) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 16px !important;
    overflow: visible !important;
    z-index: 999999 !important;
    box-shadow:
        0 20px 60px rgba(0,0,0,0.8),
        0 0 0 1px rgba(229,9,20,0.08) !important;
    backdrop-filter: blur(20px) !important;
    animation: acDropIn 0.15s cubic-bezier(0.22,0.9,0.15,1) both !important;
    max-height: 380px !important;
}

/* Anchor autocomplete to search input wrapper */
div.stElementContainer.st-key-navbar_movie_search {
    position: relative !important;
    z-index: 99999 !important;
}
/* Allow dropdown to overflow navbar columns */
.cm-navbar [data-testid="column"] {
    overflow: visible !important;
}
@keyframes acDropIn {
    from { opacity:0; transform:translateY(-8px) scale(0.98); }
    to   { opacity:1; transform:translateY(0) scale(1); }
}

/* Each suggestion item */
.cm-ac-item {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 10px 14px !important;
    text-decoration: none !important;
    transition: background 0.12s ease !important;
    border-bottom: 1px solid rgba(255,255,255,0.04) !important;
    cursor: pointer !important;
}
.cm-ac-item:last-child {
    border-bottom: none !important;
}
.cm-ac-item:hover {
    background: rgba(229,9,20,0.08) !important;
}
.cm-ac-title {
    color: #e9edf2 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    font-family: 'Poppins', sans-serif !important;
}
.cm-ac-highlight {
    color: #E50914 !important;
    font-weight: 800 !important;
}
.cm-ac-genre {
    color: #6b7280 !important;
    font-size: 11px !important;
    margin-top: 2px !important;
}
.cm-ac-poster {
    width: 36px !important;
    height: 52px !important;
    border-radius: 6px !important;
    object-fit: cover !important;
    flex-shrink: 0 !important;
}
.cm-ac-poster-fallback {
    width: 36px !important;
    height: 52px !important;
    border-radius: 6px !important;
    background: rgba(229,9,20,0.10) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 18px !important;
    flex-shrink: 0 !important;
}
.cm-ac-badge {
    font-size: 10px !important;
    font-weight: 700 !important;
    padding: 3px 8px !important;
    border-radius: 999px !important;
    flex-shrink: 0 !important;
    white-space: nowrap !important;
}
.cm-ac-badge-green  {
    background: rgba(46,204,113,0.12) !important;
    color: #2ecc71 !important;
}
.cm-ac-badge-blue   {
    background: rgba(52,152,219,0.12) !important;
    color: #3498db !important;
}
.cm-ac-badge-yellow {
    background: rgba(241,196,15,0.12) !important;
    color: #f1c40f !important;
}

/* Make search column position relative for dropdown */
div[data-testid="stColumn"]:has(
    div.stElementContainer.st-key-navbar_movie_search
) {
    position: relative !important;
    overflow: visible !important;
    z-index: 9999 !important;
}

.cm-hero-selected-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(229,9,20,0.15);
    border: 1px solid rgba(229,9,20,0.3);
    color: #ff6b6b;
    font-size: 11px;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 999px;
    margin-bottom: 10px;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    animation: badgeFadeIn 0.3s ease both;
}
@keyframes badgeFadeIn {
    from { opacity:0; transform:translateY(-4px); }
    to   { opacity:1; transform:translateY(0); }
}

/* Profile page header */
.cm-profile-page-header {
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 32px 0 24px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 28px;
}
.cm-profile-page-avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg,#E50914,#ff6b6b);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    font-weight: 900;
    color: #fff;
    flex-shrink: 0;
    border: 3px solid rgba(229,9,20,0.4);
    box-shadow: 0 0 24px rgba(229,9,20,0.2);
}
.cm-profile-page-name {
    color: #fff;
    font-size: 28px;
    font-weight: 900;
    margin: 0 0 4px 0;
}
.cm-profile-page-sub {
    color: #bdbdbd;
    font-size: 13px;
    margin: 0;
}

/* Stat cards */
.cm-stat-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    transition: all 0.18s ease;
}
.cm-stat-card:hover {
    background: rgba(255,255,255,0.05);
    border-color: rgba(229,9,20,0.2);
    transform: translateY(-2px);
}
.cm-stat-icon {
    font-size: 28px;
    margin-bottom: 10px;
}
.cm-stat-value {
    color: #fff;
    font-size: 32px;
    font-weight: 900;
    margin-bottom: 6px;
    line-height: 1;
}
.cm-stat-label {
    color: #bdbdbd;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* Genre bars */
.cm-genre-bars {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 8px;
}
.cm-genre-bar-row {
    display: flex;
    align-items: center;
    gap: 14px;
}
.cm-genre-bar-label {
    color: #e9edf2;
    font-size: 13px;
    font-weight: 600;
    min-width: 90px;
}
.cm-genre-bar-track {
    flex: 1;
    height: 8px;
    background: rgba(255,255,255,0.06);
    border-radius: 999px;
    overflow: hidden;
}
.cm-genre-bar-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.6s cubic-bezier(0.22,0.9,0.15,1);
}
.cm-genre-bar-count {
    color: #bdbdbd;
    font-size: 12px;
    font-weight: 600;
    min-width: 24px;
    text-align: right;
}

/* Back button */
div.st-key-detail_back button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #bdbdbd !important;
    border-radius: 999px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 6px 18px !important;
    margin: 16px 0 0 0 !important;
    transition: all 0.16s ease !important;
}
div.st-key-detail_back button:hover {
    background: rgba(229,9,20,0.1) !important;
    border-color: rgba(229,9,20,0.3) !important;
    color: #fff !important;
}

/* Hero backdrop */
.cm-detail-hero {
    position: relative;
    border-radius: 18px;
    overflow: hidden;
    min-height: 360px;
    margin: 16px 0 0 0;
}
.cm-detail-backdrop {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center top;
    filter: blur(18px) brightness(0.35) saturate(1.2);
    transform: scale(1.08);
}
.cm-detail-backdrop-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(
        135deg,
        rgba(5,6,10,0.7) 0%,
        rgba(5,6,10,0.3) 100%
    );
}
.cm-detail-hero-content {
    position: relative;
    display: flex;
    gap: 32px;
    padding: 36px 32px;
    align-items: flex-start;
}

/* Poster */
.cm-detail-poster {
    width: 200px;
    min-width: 200px;
    height: 300px;
    object-fit: cover;
    border-radius: 14px;
    box-shadow: 0 16px 48px rgba(0,0,0,0.7);
    border: 1px solid rgba(255,255,255,0.08);
}
.cm-detail-poster-fallback {
    width: 200px;
    min-width: 200px;
    height: 300px;
    border-radius: 14px;
    background: rgba(229,9,20,0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 56px;
    border: 1px solid rgba(229,9,20,0.2);
}

/* Info panel */
.cm-detail-info {
    flex: 1;
    min-width: 0;
    padding-top: 8px;
}
.cm-detail-title {
    color: #fff;
    font-size: 32px;
    font-weight: 900;
    margin: 0 0 14px 0;
    line-height: 1.2;
    letter-spacing: -0.5px;
}

/* Genre pills */
.cm-detail-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
}
.cm-detail-pill {
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    border: 1.5px solid;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}

/* Overview */
.cm-detail-overview {
    color: #bdbdbd;
    font-size: 14px;
    line-height: 1.7;
    margin: 0 0 20px 0;
    max-width: 540px;
}

/* Action buttons */
.cm-detail-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}
.cm-detail-btn-add {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg,#E50914,#ff6b6b);
    color: #fff !important;
    text-decoration: none !important;
    font-weight: 700;
    font-size: 14px;
    padding: 12px 28px;
    border-radius: 999px;
    transition: all 0.18s ease;
    box-shadow: 0 4px 18px rgba(229,9,20,0.35);
}
.cm-detail-btn-add:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(229,9,20,0.5);
}

/* Cast cards */
.cm-detail-cast {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}
.cm-cast-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    min-width: 70px;
}
.cm-cast-avatar {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg,rgba(229,9,20,0.3),rgba(255,95,109,0.2));
    border: 1.5px solid rgba(229,9,20,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: 800;
    color: #fff;
}
.cm-cast-name {
    color: #bdbdbd;
    font-size: 11px;
    font-weight: 600;
    text-align: center;
    max-width: 70px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Clear button */
div.st-key-clear_chat button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #bdbdbd !important;
    border-radius: 8px !important;
    font-size: 12px !important;
}
div.st-key-clear_chat button:hover {
    background: rgba(229,9,20,0.1) !important;
    color: #fff !important;
}

/* ── NAVBAR VERTICAL ALIGNMENT FIX ── */

/* Force the entire navbar horizontal block to center vertically */
.cm-navbar [data-testid="stHorizontalBlock"] {
    align-items: center !important;
    height: 64px !important;
}

/* Force EVERY column inside navbar to center vertically */
.cm-navbar [data-testid="stColumn"],
.cm-navbar [data-testid="stColumn"] > div,
.cm-navbar [data-testid="stColumn"] > div > div {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Logo column — align left not center */
.cm-navbar [data-testid="stColumn"]:first-child,
.cm-navbar [data-testid="stColumn"]:first-child > div,
.cm-navbar [data-testid="stColumn"]:first-child > div > div {
    justify-content: flex-start !important;
    align-items: center !important;
}

/* Search column — remove all top/bottom spacing */
div.stElementContainer.st-key-navbar_movie_search {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    display: flex !important;
    align-items: center !important;
    height: 38px !important;
}

div.stElementContainer.st-key-navbar_movie_search > div {
    margin: 0 !important;
    padding: 0 !important;
    height: 34px !important;
    display: flex !important;
    align-items: center !important;
}

/* Remove Streamlit default top padding on all elements inside navbar */
.cm-navbar .stElementContainer,
.cm-navbar .stMarkdown,
.cm-navbar .element-container {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Logo markdown — remove default paragraph margin */
.cm-navbar .stMarkdown p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
    display: flex !important;
    align-items: center !important;
}

/* ── NAVBAR ONE LINE FIX ── */

/* Main navbar row — force single line, center all */
.cm-navbar [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: center !important;
    height: 64px !important;
    gap: 8px !important;
}

/* Every column inside navbar — center vertically */
.cm-navbar [data-testid="stColumn"] {
    display: flex !important;
    align-items: center !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}

.cm-navbar [data-testid="stColumn"] > div {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}

/* Logo — push up by 6px to visually align with nav buttons */
.cm-navbar [data-testid="stColumn"]:first-child .stMarkdown,
.cm-navbar [data-testid="stColumn"]:first-child .stMarkdown p,
.cm-navbar [data-testid="stColumn"]:first-child .stMarkdown div {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
    position: relative !important;
    top: 0 !important;
}

/* Bell — exact dark circle */
.cm-navbar .cm-bell-slot [data-testid="stPopover"] > button {
    min-width: 52px !important;
    padding: 7px 12px !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
    width: 52px !important;
    height: 52px !important;
    font-size: 22px !important;
    gap: 0 !important;
    overflow: hidden !important;
}

/* Avatar — exact dark circle */
.cm-navbar .cm-account-slot [data-testid="stPopover"] > button {
    min-width: 52px !important;
    padding: 7px 14px !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
    font-size: 22px !important;
    color: transparent !important;
    gap: 0 !important;
    overflow: hidden !important;
    width: 52px !important;
    height: 52px !important;
}
.cm-navbar .cm-account-slot [data-testid="stPopover"] > button::before {
    content: '' !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    background: #E50914 !important;
    display: inline-flex !important;
    flex-shrink: 0 !important;
}
.cm-navbar .cm-account-slot [data-testid="stPopover"] > button::after {
    content: 'User ▾' !important;
    color: #ffffff !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
}

/* Force navbar columns single line vertically centered */
.cm-navbar [data-testid="stHorizontalBlock"] {
    flex-wrap:nowrap !important;
    align-items:center !important;
}
.cm-navbar [data-testid="stColumn"] {
    padding-top:0 !important;
    padding-bottom:0 !important;
}

/* Search bar — force same height and vertical center as nav buttons */
div.stElementContainer.st-key-navbar_movie_search {
    margin: 0 !important;
    padding: 0 !important;
    height: 34px !important;
    display: flex !important;
    align-items: center !important;
    position: relative !important;
    top: 0px !important;
    width: 240px !important;
}

div.stElementContainer.st-key-navbar_movie_search > div {
    margin: 0 !important;
    padding: 0 !important;
    height: 38px !important;
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
}

div.stElementContainer.st-key-navbar_movie_search > div > div {
    height: 38px !important;
    display: flex !important;
    align-items: center !important;
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}

div.stElementContainer.st-key-navbar_movie_search input {
    height: 38px !important;
    line-height: 38px !important;
    margin: 0 !important;
    padding: 0 0 0 22px !important;
}

/* Remove ALL default Streamlit top/bottom spacing inside navbar */
.cm-navbar .stElementContainer,
.cm-navbar .element-container,
.cm-navbar .stMarkdown,
.cm-navbar .stButton,
.cm-navbar .stPopover {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Bell and avatar popover buttons — center them */
div.cm-bell-slot,
div.cm-account-slot,
div.cm-bell-slot > div,
div.cm-account-slot > div,
div.cm-bell-slot [data-testid="stPopover"],
div.cm-account-slot [data-testid="stPopover"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    height: 36px !important;
}

/* Bell button exact circle */
div.cm-bell-slot [data-testid="stPopover"] > button {
    min-width: 46px !important;
    padding: 7px 12px !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
    width: 46px !important;
    height: 46px !important;
    font-size: 20px !important;
    gap: 0 !important;
    overflow: hidden !important;
}

/* Avatar button exact circle */
div.cm-account-slot [data-testid="stPopover"] > button {
    min-width: 46px !important;
    padding: 7px 14px !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
    font-size: 20px !important;
    color: transparent !important;
    display: flex !important;
    align-items: center !important;
    gap: 0 !important;
    overflow: hidden !important;
    width: 46px !important;
    height: 46px !important;
}
div.cm-account-slot [data-testid="stPopover"] > button::before {
    content: '' !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    background: #E50914 !important;
    display: inline-flex !important;
    flex-shrink: 0 !important;
}
div.cm-account-slot [data-testid="stPopover"] > button::after {
    content: 'User ▾' !important;
    color: #ffffff !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    display: inline-flex !important;
    align-items: center !important;
}

@media (max-width:900px){
    .cm-navbar{height:auto;min-height:78px;padding:16px}
    .cm-nav{gap:8px}
    .cm-search{min-width:100%;width:100%}
    .cm-main{margin-left:0;padding:18px}
    .cm-hero{height:420px}
    .cm-hero h1{font-size:28px}
    .card{min-width:150px}
}

/* Spin page */
.cm-spin-hero{padding:18px 0 12px 0}
.cm-spin-title{color:#fff;font-size:30px;font-weight:900;margin:0 0 6px 0}
.cm-spin-sub{color:#bdbdbd;font-size:13.5px;margin:0}
.cm-spin-shell{
    background:linear-gradient(120deg,rgba(229,9,20,0.08),rgba(7,10,18,0.3));
    border:1px solid rgba(255,255,255,0.06);
    border-radius:20px;
    padding:18px 22px;
    margin-bottom:18px;
}
.cm-wheel-wrap{position:relative;width:360px;height:360px;margin:10px auto 16px auto}
.cm-wheel{
    width:100%;height:100%;border-radius:50%;
    background:conic-gradient(
        #d90416 0deg 36deg,
        #7b4bd3 36deg 72deg,
        #f06b95 72deg 108deg,
        #f2b94b 108deg 144deg,
        #1db98a 144deg 180deg,
        #d47b2b 180deg 216deg,
        #3d84c6 216deg 252deg,
        #2fb667 252deg 288deg,
        #f072a6 288deg 324deg,
        #f0c06d 324deg 360deg
    );
    border:6px solid rgba(229,9,20,0.6);
    box-shadow:0 0 28px rgba(229,9,20,0.3), inset 0 0 18px rgba(0,0,0,0.6);
    position:relative;
    transform:rotate(var(--spin-angle, 0deg));
    transition:transform 3.2s cubic-bezier(0.16, 0.95, 0.2, 1);
}
.cm-wheel-center{
    position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    width:62px;height:62px;border-radius:50%;
    background:#0c0f18;border:3px solid rgba(229,9,20,0.5);
    display:flex;align-items:center;justify-content:center;color:#fff;font-size:22px;
    box-shadow:0 0 18px rgba(0,0,0,0.6);
}
.cm-wheel-pointer{
    position:absolute;left:50%;top:-8px;transform:translateX(-50%);
    width:0;height:0;border-left:10px solid transparent;border-right:10px solid transparent;
    border-bottom:16px solid #e50914;filter:drop-shadow(0 2px 6px rgba(229,9,20,0.6));
}
.cm-wheel-label{
    position:absolute;left:50%;top:50%;transform-origin:center center;
    font-size:11px;font-weight:700;color:#fff;text-shadow:0 2px 4px rgba(0,0,0,0.6);
    display:flex;align-items:center;gap:6px;
}
div.st-key-spin_now button{
    background:linear-gradient(90deg,#e50914,#ff6b6b) !important;
    border:none !important;color:#fff !important;font-weight:900 !important;
    font-size:15px !important;border-radius:12px !important;
    padding:12px 22px !important;box-shadow:0 10px 30px rgba(229,9,20,0.3) !important;
}
div.st-key-spin_now button:hover{transform:translateY(-2px) !important;box-shadow:0 14px 38px rgba(229,9,20,0.45) !important}
.cm-spin-right-title{color:#fff;font-size:22px;font-weight:900;margin:10px 0 6px 0}
.cm-spin-right-sub{color:#9aa4b2;font-size:13px;margin:0 0 14px 0}
.cm-spin-chips{display:flex;flex-wrap:wrap;gap:8px}
div[class*="st-key-spin_chip_"] button{
    background:rgba(255,255,255,0.04) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    color:#e6e9ef !important;
    border-radius:999px !important;
    font-size:12px !important;
    font-weight:600 !important;
    padding:6px 12px !important;
}
div[class*="st-key-spin_chip_"] button:hover{
    background:rgba(229,9,20,0.12) !important;
    border-color:rgba(229,9,20,0.35) !important;
    transform:translateY(-1px) !important;
}
.cm-spin-history{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.cm-spin-pill{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);color:#bdbdbd;border-radius:999px;font-size:11.5px;font-weight:600;padding:6px 10px}

/* Mood filter label */
.cm-ai-mood-label {
    color: #6b7280;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 0 0 8px;
}

/* Mood filter buttons */
div[class*="st-key-mood_filter_"] button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    color: #bdbdbd !important;
    border-radius: 999px !important;
    font-size: 11.5px !important;
    font-weight: 600 !important;
    padding: 6px 4px !important;
    white-space: nowrap !important;
    transition: all 0.15s ease !important;
    font-family: 'Poppins', sans-serif !important;
    min-height: 34px !important;
}
div[class*="st-key-mood_filter_"] button:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #fff !important;
    transform: translateY(-1px) !important;
}

/* Active mood pill above input */
.cm-active-mood-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(229,9,20,0.08);
    border: 1px solid rgba(229,9,20,0.2);
    border-radius: 999px;
    padding: 5px 14px;
    color: #ff6b6b;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 8px;
}
.cm-active-mood-pill strong {
    color: #fff;
}

/* Search correction suggestions */
.cm-search-suggest {
    margin: 18px auto 6px;
    max-width: 720px;
    background: rgba(12,16,26,0.7);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.32);
}
.cm-search-suggest-label {
    color: #9aa4b2;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.cm-search-suggest-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
    text-decoration: none;
    color: #eef0f3;
    transition: all 0.18s ease;
    margin-bottom: 8px;
}
.cm-search-suggest-item:hover {
    background: rgba(229,9,20,0.08);
    border-color: rgba(229,9,20,0.2);
    transform: translateY(-1px);
}
.cm-search-suggest-title {
    font-size: 13.5px;
    font-weight: 600;
    color: #fff;
}
.cm-search-suggest-hl {
    color: #ff6b6b;
    font-weight: 800;
}
.cm-search-suggest-cta {
    font-size: 11px;
    font-weight: 700;
    color: #ff6b6b;
}
.cm-search-suggest-empty {
    text-align: center;
    color: #bdbdbd;
    font-size: 14px;
    padding: 24px 0 12px;
}

/* Autocomplete empty state */
.cm-ac-empty {
    padding: 14px 16px;
    color: #bdbdbd;
    font-size: 12.5px;
    text-align: center;
}

/* Chips header divider */
.cm-chips-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0 0 12px;
}
.cm-chips-line {
    flex: 1;
    height: 1px;
}
.cl1 { background: linear-gradient(90deg,transparent,rgba(255,255,255,0.08)); }
.cl2 { background: linear-gradient(270deg,transparent,rgba(255,255,255,0.08)); }
.cm-chips-label {
    color: #6b7280;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    white-space: nowrap;
}

/* Clear chat button */
div.st-key-clear_chat button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    color: #6b7280 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
}
div.st-key-clear_chat button:hover {
    background: rgba(229,9,20,0.08) !important;
    color: #ff6b6b !important;
    border-color: rgba(229,9,20,0.2) !important;
}

/* AI hero section */
.cm-ai-bg {
    position: relative;
    padding: 32px 28px 26px;
    border-radius: 22px;
    background:
        radial-gradient(900px 300px at 12% 0%, rgba(229,9,20,0.18), transparent 60%),
        radial-gradient(700px 320px at 85% 10%, rgba(26,188,156,0.14), transparent 60%),
        linear-gradient(135deg, rgba(8,10,16,0.98), rgba(12,16,28,0.92));
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
    overflow: hidden;
    margin: 10px 0 18px;
}
.cm-ai-grid-lines {
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 36px 36px;
    opacity: 0.25;
    pointer-events: none;
}
.cm-ai-orb {
    position: absolute;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    filter: blur(2px);
    opacity: 0.65;
    animation: cmOrbFloat 10s ease-in-out infinite;
}
.cm-ai-orb.orb1 {
    top: -40px;
    left: -30px;
    background: radial-gradient(circle, rgba(229,9,20,0.5), transparent 65%);
}
.cm-ai-orb.orb2 {
    bottom: -60px;
    right: 12%;
    background: radial-gradient(circle, rgba(26,188,156,0.45), transparent 65%);
    animation-delay: 1.2s;
}
.cm-ai-orb.orb3 {
    top: 10%;
    right: -50px;
    background: radial-gradient(circle, rgba(255,107,107,0.4), transparent 65%);
    animation-delay: 2.4s;
}
@keyframes cmOrbFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
.cm-ai-film-left,
.cm-ai-film-right {
    position: absolute;
    top: 18px;
    bottom: 18px;
    width: 56px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    opacity: 0.75;
    pointer-events: none;
}
.cm-ai-film-left { left: 12px; }
.cm-ai-film-right { right: 12px; }
.cm-fl-hole {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: rgba(255,255,255,0.12);
    box-shadow: 0 0 0 1px rgba(255,255,255,0.05) inset;
}
.cm-fl-frame {
    width: 36px;
    height: 30px;
    border-radius: 8px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
}
.cm-ai-star {
    position: absolute;
    color: rgba(255,255,255,0.45);
    font-size: 12px;
    opacity: 0.8;
    animation: cmStarTwinkle 4.5s ease-in-out infinite;
}
.cm-ai-star.s1 { top: 14%; left: 28%; }
.cm-ai-star.s2 { top: 30%; right: 22%; animation-delay: 0.8s; }
.cm-ai-star.s3 { bottom: 22%; left: 18%; animation-delay: 1.4s; }
.cm-ai-star.s4 { bottom: 30%; right: 30%; animation-delay: 2s; }
.cm-ai-star.s5 { top: 18%; right: 40%; animation-delay: 2.6s; }
@keyframes cmStarTwinkle {
    0%, 100% { opacity: 0.4; transform: scale(0.95); }
    50% { opacity: 0.9; transform: scale(1.08); }
}
.cm-ai-hero-inner {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    gap: 18px;
}
.cm-ai-top-row {
    display: flex;
    justify-content: flex-end;
}
.cm-ai-live-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(26,188,156,0.1);
    border: 1px solid rgba(26,188,156,0.35);
    color: #b7f5e8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
}
.cm-ai-live-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #1abc9c;
    box-shadow: 0 0 10px rgba(26,188,156,0.6);
}
.cm-ai-title-row {
    display: flex;
    align-items: center;
    gap: 14px;
}
.cm-ai-robot-icon {
    width: 54px;
    height: 54px;
    border-radius: 16px;
    background: rgba(229,9,20,0.12);
    border: 1px solid rgba(229,9,20,0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}
.cm-ai-title {
    margin: 0;
    font-size: 34px;
    font-weight: 900;
    color: #fff;
    letter-spacing: -0.5px;
}
.cm-ai-title-ai {
    color: #ff6b6b;
}
.cm-ai-subtitle {
    margin: 6px 0 0;
    color: rgba(255,255,255,0.7);
    font-size: 14px;
}
.cm-ai-hl {
    color: #fff;
    font-weight: 700;
}
.cm-ai-stats-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
}
.cm-ai-stat-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    color: #e9edf2;
}
.cm-ai-stat-val { font-size: 16px; font-weight: 800; }
.cm-ai-stat-lbl { font-size: 11px; color: rgba(255,255,255,0.6); font-weight: 600; }

/* AI chat mini cards */
.cm-mini-card {
    background: rgba(12,16,26,0.8);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 10px 26px rgba(0,0,0,0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.cm-mini-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 36px rgba(0,0,0,0.45);
}
.cm-mini-card-title {
    padding: 8px 10px 4px;
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.3;
}
.cm-mini-card-trailer {
    padding: 0 10px 10px;
    color: #ff6b6b;
    font-size: 11px;
    font-weight: 700;
}

@media (max-width: 900px) {
    .cm-ai-film-left,
    .cm-ai-film-right,
    .cm-ai-star { display: none; }
    .cm-ai-stats-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .cm-ai-title { font-size: 28px; }
    .cm-ai-bg { padding: 24px 20px; }
}

/* ══ NL SEARCH: CSS START ══ */
/* NL search cards */
.nl-carousel { display: flex; gap: 18px; overflow-x: auto; padding: 8px 2px 14px; }
.nl-card {
    min-width: 170px;
    max-width: 170px;
    background: rgba(12,16,26,0.75);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 10px 26px rgba(0,0,0,0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.nl-card:hover { transform: translateY(-4px); box-shadow: 0 16px 34px rgba(0,0,0,0.45); }
.nl-card-poster { position: relative; width: 100%; height: 245px; background: #111522; }
.nl-card-poster img { width: 100%; height: 100%; object-fit: cover; display: block; }
.nl-card-overlay {
    position: absolute; inset: 0; display: flex; align-items: flex-end; justify-content: center;
    gap: 8px; padding: 0 10px 10px; opacity: 0; transition: opacity 0.2s ease;
    background: linear-gradient(0deg, rgba(5,6,10,0.8), rgba(5,6,10,0.0));
}
.nl-card:hover .nl-card-overlay { opacity: 1; }
.nl-trailer-btn, .nl-list-btn {
    font-size: 11px; font-weight: 700; padding: 6px 10px; border-radius: 999px; text-decoration: none;
    background: rgba(255,255,255,0.08); color: #fff; border: 1px solid rgba(255,255,255,0.12);
}
.nl-trailer-btn { background: rgba(229,9,20,0.85); border-color: rgba(229,9,20,0.8); }
.nl-card-info { padding: 10px 12px 12px; }
.nl-card-title { font-size: 12.5px; font-weight: 700; color: #fff; line-height: 1.3; }
.nl-card-reason {
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    font-style: italic;
    line-height: 1.4;
    margin-top: 4px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.nl-ai-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: linear-gradient(135deg, #E50914, #ff6b6b);
    color: white;
    font-size: 9px;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 20px;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(229,9,20,0.4);
}

.cm-search-hint {
    font-size: 11px;
    color: rgba(255,255,255,0.3);
    padding: 6px 12px;
    font-style: italic;
    animation: cmHintPulse 3s ease-in-out infinite;
}

@keyframes cmHintPulse { 0%,100% { opacity: 0.55; } 50% { opacity: 1; } }
@keyframes cmSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
/* ══ NL SEARCH: CSS END ══ */
</style>
"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)
st.markdown("""
<script>
(function() {
    function interceptLinks() {
        document.addEventListener('click', function(e) {
            var el = e.target;
            while (el && el.tagName !== 'A') { el = el.parentElement; }
            if (!el) return;
            var href = el.getAttribute('href');
            if (!href) return;
            if (href.charAt(0) !== '?') return;
            e.preventDefault();
            e.stopPropagation();
            var base = window.location.protocol + '//' + window.location.host + window.location.pathname;
            window.location.href = base + href;
        }, true);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', interceptLinks);
    } else {
        interceptLinks();
    }
})();
</script>
""", unsafe_allow_html=True)
st.markdown(
    """
    <script>
    (function(){
        const applySpellcheck = () => {
            const inputs = document.querySelectorAll('div.st-key-navbar_movie_search input');
            inputs.forEach((el) => {
                el.setAttribute('spellcheck', 'false');
                el.setAttribute('autocorrect', 'off');
                el.setAttribute('autocapitalize', 'off');
            });
        };
        applySpellcheck();
        const obs = new MutationObserver(applySpellcheck);
        obs.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

# Constants
TMDB_API_KEY = "a71b1374a6f462f48dc76e74d341ffba"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
GENRE_OPTIONS = [
    'All', 'Action', 'Adventure', 'Animation', 'Comedy',
    'Crime', 'Documentary', 'Drama', 'Fantasy', 'Horror',
    'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War'
]

def _normalize_language_value(value: str) -> str:
    v = str(value or '').strip().lower()
    if not v or v == 'nan':
        return 'en'
    if v in {'mr', 'marathi', 'mar'} or 'marathi' in v:
        return 'mr'
    if v in {'hi', 'hindi', 'hin'} or 'hindi' in v or 'bollywood' in v:
        return 'hi'
    if v in {'en', 'english'} or 'english' in v or 'hollywood' in v:
        return 'en'
    return v

def _load_indian_movies_csv() -> pd.DataFrame:
    path = os.path.join(os.path.dirname(__file__), "indian_movies.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        indian_df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

    cols = ["movie_id", "title", "tags", "poster_url", "language"]
    for col in cols:
        if col not in indian_df.columns:
            indian_df[col] = ""

    indian_df = indian_df[cols]
    indian_df["title"] = indian_df["title"].fillna("").astype(str)
    indian_df["language"] = indian_df["language"].fillna("").astype(str)
    indian_df["language"] = indian_df["language"].apply(lambda v: _normalize_language_value(v))
    indian_df = indian_df[indian_df["title"].str.strip() != ""]
    return indian_df


@st.cache_data(show_spinner=False, ttl=300)
def load_movies():
    rows = []
    try:
        rows = db.get_all_movies()
    except Exception:
        rows = []

    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(columns=["movie_id", "title", "tags", "poster_url"])

    if "tags" not in df.columns:
        df["tags"] = ""
    if "poster_url" not in df.columns:
        df["poster_url"] = ""
    if "language" not in df.columns:
        df["language"] = ""

    df["poster_url"] = df["poster_url"].fillna("").astype(str)

    def _normalize_poster_url(value):
        v = str(value).strip()
        if not v or v.lower() == "nan":
            return ""
        if v.startswith("http"):
            return v
        if v.startswith("/"):
            return f"{TMDB_IMAGE_BASE}{v}"
        return ""

    df["poster_url"] = df["poster_url"].apply(_normalize_poster_url)

    df["language"] = df["language"].fillna("").astype(str)
    df["language"] = df["language"].apply(lambda v: _normalize_language_value(v))

    indian_df = _load_indian_movies_csv()
    if not indian_df.empty:
        existing_titles = set(df["title"].astype(str).str.strip().str.lower()) if not df.empty else set()
        missing_mask = ~indian_df["title"].astype(str).str.strip().str.lower().isin(existing_titles)
        missing_df = indian_df[missing_mask]
        if not missing_df.empty:
            db.insert_movies(missing_df[["movie_id", "title", "tags", "poster_url", "language"]])

        df = pd.concat([df, indian_df], ignore_index=True)
        df["_title_norm"] = df["title"].astype(str).str.strip().str.lower()
        lang_map = dict(
            zip(
                indian_df["title"].astype(str).str.strip().str.lower(),
                indian_df["language"].astype(str).str.lower(),
            )
        )
        df["language"] = df.apply(
            lambda row: lang_map.get(str(row.get("title", "")).strip().lower(), row.get("language", "")),
            axis=1,
        )
        df["language"] = df["language"].fillna("").astype(str).apply(lambda v: _normalize_language_value(v))
        df = df.drop_duplicates(subset=["_title_norm"], keep="first").drop(columns=["_title_norm"])

    tmdb_csv_path = os.path.join(os.path.dirname(__file__), "tmdb_5000_movies.csv")
    tmdb_lang_df = pd.DataFrame()
    if os.path.exists(tmdb_csv_path):
        try:
            tmdb_lang_df = pd.read_csv(
                tmdb_csv_path,
                usecols=["title", "original_language"],
            )
        except Exception:
            tmdb_lang_df = pd.DataFrame()

    if not tmdb_lang_df.empty:
        tmdb_lang_df = tmdb_lang_df.dropna(subset=["title"]).copy()
        tmdb_lang_df["title"] = tmdb_lang_df["title"].astype(str).str.strip()
        tmdb_lang_df["original_language"] = (
            tmdb_lang_df["original_language"].fillna("").astype(str).str.strip().str.lower()
        )
        tmdb_lang_df = tmdb_lang_df[tmdb_lang_df["title"] != ""]
        tmdb_lang_df = tmdb_lang_df.rename(columns={"original_language": "language_tmdb"})

        df = df.merge(tmdb_lang_df, on="title", how="left")
        df["language"] = df["language"].fillna("")
        df["language_tmdb"] = df["language_tmdb"].fillna("")
        df["language"] = df.apply(
            lambda row: row["language"] if str(row["language"]).strip() else row["language_tmdb"],
            axis=1,
        )
        df = df.drop(columns=["language_tmdb"])

    df["language"] = df["language"].fillna("en").astype(str).apply(lambda v: _normalize_language_value(v))

    if df.empty:
        sample = [
            {"movie_id": "1", "title": "Nova Horizon", "tags": "sci-fi space future adventure"},
            {"movie_id": "2", "title": "Crimson Tide", "tags": "thriller war submarine action"},
            {"movie_id": "3", "title": "Midnight Echoes", "tags": "horror mystery supernatural"},
            {"movie_id": "4", "title": "Stellar Drift", "tags": "sci-fi drama romance"},
            {"movie_id": "5", "title": "Neon City", "tags": "cyberpunk action thriller"},
        ]
        return pd.DataFrame(sample)

    return df


load_data = load_movies


def get_anthropic_client():
    if anthropic is None:
        raise RuntimeError("Anthropic SDK is not available. Install 'anthropic' to use this feature.")
    return anthropic.Anthropic()


def get_movies_by_genre(df_local, genre=None, limit=None):
    """Filter movies from DB dataframe by genre tag."""
    working = df_local.copy()
    working['tags'] = working['tags'].fillna('').astype(str)
    if genre and genre.lower() != 'all':
        working = working[working['tags'].str.contains(genre, case=False, na=False)]
    if limit:
        working = working.head(limit)
    return working.reset_index(drop=True)


def get_movies_by_mood(df, mood_key, limit=20):
    """Filter movies by mood keywords from tags column."""
    mood = MOOD_MAP.get(mood_key)
    if not mood or df is None or df.empty:
        return pd.DataFrame()

    keywords = mood['keywords']
    working = df.copy()
    working['tags'] = working['tags'].fillna('').astype(str).str.lower()

    def mood_score(tags):
        return sum(1 for kw in keywords if kw in tags)

    working['_mood_score'] = working['tags'].apply(mood_score)
    matched = working[working['_mood_score'] > 0]
    matched = matched.sort_values('_mood_score', ascending=False)
    matched = matched.drop(columns=['_mood_score'])

    return matched.head(limit).reset_index(drop=True)


def advanced_search_movies(
    df_local: pd.DataFrame,
    genres=None,
    min_rating: float = 5.0,
    year_range=(2020, 2024),
    page: int = 1,
    per_page: int = 10,
):
    if df_local is None or df_local.empty:
        return {
            "results": pd.DataFrame(),
            "total_results": 0,
            "total_pages": 0,
            "page": 1,
            "per_page": per_page,
        }

    working = df_local.copy()
    if "tags" not in working.columns:
        working["tags"] = ""
    working["tags"] = working["tags"].fillna("").astype(str)

    selected_genres = [g.strip() for g in (genres or ["Horror", "Action", "Comedy"]) if str(g).strip()]
    if selected_genres:
        genre_pattern = "|".join(re.escape(g) for g in selected_genres)
        working = working[working["tags"].str.contains(genre_pattern, case=False, na=False)]

    rating_series = None
    if "rating" in working.columns:
        rating_series = pd.to_numeric(working["rating"], errors="coerce")
    elif "vote_average" in working.columns:
        rating_series = pd.to_numeric(working["vote_average"], errors="coerce") / 2
    elif "score" in working.columns:
        rating_series = pd.to_numeric(working["score"], errors="coerce")
    elif "stars" in working.columns:
        rating_series = pd.to_numeric(working["stars"], errors="coerce")
    else:
        if "movie_id" in working.columns:
            rating_series = working["movie_id"].apply(score_from_id)
        else:
            rating_series = pd.Series([0] * len(working), index=working.index)

    working = working.assign(_rating=rating_series)
    working = working[working["_rating"].fillna(0) >= float(min_rating)]

    year_series = None
    if "release_year" in working.columns:
        year_series = pd.to_numeric(working["release_year"], errors="coerce")
    elif "year" in working.columns:
        year_series = pd.to_numeric(working["year"], errors="coerce")
    elif "release_date" in working.columns:
        year_series = pd.to_datetime(working["release_date"], errors="coerce").dt.year
    else:
        year_series = pd.Series([pd.NA] * len(working), index=working.index)

    start_year, end_year = year_range
    working = working.assign(_year=year_series)
    working = working[working["_year"].between(int(start_year), int(end_year), inclusive="both")]

    total_results = int(len(working))
    total_pages = int(math.ceil(total_results / per_page)) if total_results else 0
    safe_page = max(1, min(int(page), total_pages)) if total_pages else 1
    start_idx = (safe_page - 1) * per_page
    end_idx = start_idx + per_page
    page_df = working.iloc[start_idx:end_idx].drop(columns=["_rating", "_year"]).reset_index(drop=True)

    return {
        "results": page_df,
        "total_results": total_results,
        "total_pages": total_pages,
        "page": safe_page,
        "per_page": per_page,
    }


@st.cache_data(show_spinner=False, ttl=300)
def get_search_suggestions(query, df, max_results=8):
    """
    Return movie title suggestions matching the query.
    Uses 3 strategies: starts-with, contains, fuzzy match.
    Returns list of dicts: [{title, poster_url, tags_preview}]
    """
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip().lower()
    working = df.copy()
    working['title_lower'] = working['title'].str.lower().fillna('')
    working['tags'] = working['tags'].fillna('').astype(str)

    results = []
    seen = set()

    # Strategy 1: Starts with query (highest priority)
    starts = working[working['title_lower'].str.startswith(q)]
    for _, row in starts.head(4).iterrows():
        t = str(row['title']).strip()
        if t not in seen:
            seen.add(t)
            results.append({
                'title':       t,
                'poster_url':  row.get('poster_url', ''),
                'match_type':  'starts',
                'tags_preview': _get_genre_preview(str(row.get('tags', ''))),
            })

    # Strategy 2: Contains query anywhere in title
    contains = working[
        working['title_lower'].str.contains(q, na=False) &
        ~working['title_lower'].str.startswith(q)
    ]
    for _, row in contains.head(3).iterrows():
        t = str(row['title']).strip()
        if t not in seen:
            seen.add(t)
            results.append({
                'title':       t,
                'poster_url':  row.get('poster_url', ''),
                'match_type':  'contains',
                'tags_preview': _get_genre_preview(str(row.get('tags', ''))),
            })

    # Strategy 3: Fuzzy match (for typos)
    if len(results) < 4:
        import difflib
        all_titles = working['title_lower'].tolist()
        fuzzy = difflib.get_close_matches(q, all_titles, n=4, cutoff=0.45)
        for match in fuzzy:
            row = working[working['title_lower'] == match]
            if row.empty:
                continue
            t = str(row.iloc[0]['title']).strip()
            if t not in seen:
                seen.add(t)
                results.append({
                    'title':       t,
                    'poster_url':  row.iloc[0].get('poster_url', ''),
                    'match_type':  'fuzzy',
                    'tags_preview': _get_genre_preview(str(row.iloc[0].get('tags', ''))),
                })

    return results[:max_results]


def _get_genre_preview(tags):
    """Extract 2 readable genre labels from tags string."""
    READABLE = {
        'horror': 'Horror',   'comedy': 'Comedy',
        'action': 'Action',   'romance': 'Romance',
        'drama': 'Drama',     'thriller': 'Thriller',
        'adventur': 'Adventure', 'fantasy': 'Fantasy',
        'animat': 'Animation', 'scifi': 'Sci-Fi',
        'biographi': 'Biography', 'mysteri': 'Mystery',
        'war': 'War',         'sport': 'Sports',
        'music': 'Musical',   'famili': 'Family',
        'crime': 'Crime',     'histor': 'Historical',
        'space': 'Space',     'magic': 'Magic',
    }
    words = tags.lower().split()
    found = []
    seen = set()
    for word in words:
        for stem, label in READABLE.items():
            if word.startswith(stem) and label not in seen:
                found.append(label)
                seen.add(label)
                break
        if len(found) >= 2:
            break
    return ' · '.join(found) if found else 'Movie'


def get_because_you_watched(df, user_id, topn=8):
    """
    For each movie in user's watchlist (last 3),
    find similar movies using similarity.pkl via recommend().
    Returns list of dicts: [{'source_title': str, 'movies': DataFrame}]
    """
    if not user_id:
        return []

    try:
        watchlist_rows = db.get_watchlist(int(user_id))
    except Exception:
        return []

    if not watchlist_rows:
        return []

    recent = watchlist_rows[:3]
    results = []

    seen_titles = set()
    watchlist_titles = {str(r.get('title', '')).strip().lower() for r in watchlist_rows}

    for row in recent:
        source_title = str(row.get('title', '')).strip()
        if not source_title:
            continue

        try:
            recs = recommend(source_title, df, topn=topn + 5)
        except Exception:
            continue

        if not recs:
            continue

        rec_df = pd.DataFrame(recs)

        rec_df = rec_df[
            ~rec_df['title'].str.strip().str.lower().isin(watchlist_titles) &
            ~rec_df['title'].str.strip().str.lower().isin(seen_titles)
        ]

        if rec_df.empty:
            continue

        rec_df = rec_df.head(topn).reset_index(drop=True)

        for t in rec_df['title'].str.strip().str.lower():
            seen_titles.add(t)

        results.append({
            'source_title': source_title,
            'movies': rec_df,
        })

    return results


def get_user_stats(user_id, df):
    """Get stats for profile page."""
    if not user_id:
        return {}

    try:
        watchlist = db.get_watchlist(int(user_id))
    except Exception:
        watchlist = []

    # Favourite genres from watchlist tags
    READABLE_TAGS = {
        'horror': 'Horror', 'comedy': 'Comedy', 'action': 'Action',
        'romance': 'Romance', 'drama': 'Drama', 'thriller': 'Thriller',
        'adventur': 'Adventure', 'fantasy': 'Fantasy', 'animat': 'Animation',
        'scifi': 'Sci-Fi', 'biographi': 'Biography', 'mysteri': 'Mystery',
        'war': 'War', 'sport': 'Sports', 'famili': 'Family', 'crime': 'Crime',
        'magic': 'Magic', 'space': 'Space', 'music': 'Musical',
    }

    genre_counts = {}
    for row in watchlist:
        tags = str(row.get('tags', '')).lower().split()
        for word in tags:
            for stem, label in READABLE_TAGS.items():
                if word.startswith(stem):
                    genre_counts[label] = genre_counts.get(label, 0) + 1
                    break

    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        'total_watched': len(watchlist),
        'top_genres': top_genres,
        'watchlist': watchlist,
    }


def get_movie_context_for_ai(df, limit=300):
    """
    Build a compact movie list string from DB to inject into Claude prompt.
    Format: ID | Title | Tags (first 80 chars)
    """
    if df is None or df.empty:
        return "No movies available."

    working = df.head(limit).copy()
    working['tags'] = working['tags'].fillna('').astype(str).str[:80]

    lines = []
    for _, row in working.iterrows():
        title = str(row.get('title', '')).strip()
        tags = str(row.get('tags', '')).strip()
        lines.append(f"{title} | {tags}")

    return "\n".join(lines)


def get_trailer_url(title):
    """
    Build a YouTube search URL for the movie trailer.
    No API needed — uses YouTube search directly.
    """
    query = quote_plus(f"{title} official trailer")
    return f"https://www.youtube.com/results?search_query={query}"


def get_tmdb_trailer_url(movie_id, title):
    """
    Try TMDB API first for exact trailer link.
    Falls back to YouTube search if API fails.
    """
    TMDB_API_KEY = "a71b1374a6f462f48dc76e74d341ffba"
    try:
        resp = requests.get(
            f"https://api.themoviedb.org/3/movie/{int(movie_id)}/videos"
            f"?api_key={TMDB_API_KEY}",
            timeout=5,
        )
        data = resp.json()
        videos = data.get('results', [])

        # Find official trailer first
        for v in videos:
            if (
                v.get('site') == 'YouTube'
                and v.get('type') == 'Trailer'
                and v.get('official', False)
            ):
                return f"https://www.youtube.com/watch?v={v['key']}"

        # Any trailer
        for v in videos:
            if v.get('site') == 'YouTube' and v.get('type') == 'Trailer':
                return f"https://www.youtube.com/watch?v={v['key']}"

        # Any YouTube video
        for v in videos:
            if v.get('site') == 'YouTube':
                return f"https://www.youtube.com/watch?v={v['key']}"

    except Exception:
        pass

    # Fallback: YouTube search
    return get_trailer_url(title)


def _local_recommend(user_message, df):
    """
    100% offline fallback using similarity.pkl + keyword matching.
    Triggered automatically if API fails.
    """
    import re
    import random
    import difflib

    msg = user_message.lower().strip()

    GENRE_KEYWORDS = {
        r'funny|comedy|laugh|humor': 'comedy',
        r'scary|horror|ghost|terrif': 'horror',
        r'romantic|love|romance|couple': 'romance',
        r'action|fight|thrill|adventure': 'action',
        r'sad|emotional|drama|cry': 'drama',
        r'sci.fi|space|future|alien': 'scifi',
        r'mystery|detective|crime|thriller': 'thriller',
        r'inspire|sport|champion|biography': 'biography',
        r'family|kids|animation|cartoon': 'animation',
        r'fantasy|magic|wizard|dragon': 'fantasy',
    }

    source_movie = None
    for pattern in ['like ', 'similar to ', 'same as ']:
        if pattern in msg:
            after = msg.split(pattern, 1)[1]
            candidate = ' '.join(after.split()[:4]).strip('.,!?')
            titles = df['title'].str.lower().tolist()
            matches = difflib.get_close_matches(candidate, titles, n=1, cutoff=0.4)
            if matches:
                row = df[df['title'].str.lower() == matches[0]]
                if not row.empty:
                    source_movie = row.iloc[0]['title']
            break

    detected_genre = None
    for pattern, genre in GENRE_KEYWORDS.items():
        if re.search(pattern, msg):
            detected_genre = genre
            break

    lines = []
    movies = pd.DataFrame()

    if source_movie:
        recs = recommend(source_movie, df, topn=8)
        if recs:
            movies = pd.DataFrame(recs).head(5)
            lines.append(f"🎬 Movies similar to **{source_movie}**:\n")
        else:
            return f"🤔 Couldn't find **{source_movie}** in database. Try another title!"
    elif detected_genre:
        genre_df = df[df['tags'].str.contains(detected_genre, case=False, na=False)]
        movies = genre_df.sample(n=min(len(genre_df), 5), random_state=42).reset_index(drop=True)
        lines.append("🎬 Top picks for you:\n")
    else:
        movies = df.sample(n=5, random_state=7).reset_index(drop=True)
        lines.append("🎬 Here are some great picks:\n")

    EMOJIS = ['🥇', '🥈', '🥉', '🎬', '🍿']
    for i, (_, row) in enumerate(movies.iterrows()):
        title = str(row.get('title', '')).strip()
        tags = str(row.get('tags', '')).strip()
        stop_words = {'about', 'their', 'these', 'which', 'there', 'after'}
        tag_words = [
            w for w in tags.split()[:30]
            if len(w) >= 6
            and w not in stop_words
            and not w.endswith('elv')
            and not w.endswith('ighli')
            and w.isalpha()
        ]
        tag_labels = {
            'horror': 'Horror', 'comedy': 'Comedy', 'action': 'Action',
            'romance': 'Romance', 'thriller': 'Thriller', 'drama': 'Drama',
            'animation': 'Animation', 'fantasy': 'Fantasy', 'scifi': 'Sci-Fi',
            'adventure': 'Adventure', 'biography': 'Biography',
            'murder': 'Murder Mystery', 'zombie': 'Zombie',
        }
        labeled = [tag_labels[w] for w in tag_words if w in tag_labels]
        reason_words = labeled or tag_words
        reason = ', '.join(reason_words[:3]).title() if reason_words else 'Great pick'
        lines.append(f"{EMOJIS[i] if i < 5 else '🎥'} **{title}** — {reason}")

    follow_ups = [
        "\n\nWant something more specific? Tell me a mood or genre! 🎭",
        "\n\nShall I find something scarier, funnier, or more romantic? 💬",
        "\n\nWant picks from a specific genre or era? Just ask! 📽️",
    ]
    lines.append(random.choice(follow_ups))
    return "\n".join(lines)


def ask_cinematch_ai(user_message, df, chat_history):
    """Call OpenRouter API for real AI responses. Falls back to offline if API fails."""
    import requests
    import re
    import random
    import difflib

    OPENROUTER_API_KEY = "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"

    catalog_lines = []
    if df is not None and not df.empty:
        sample = df[['title', 'language']].dropna().head(200)
        for _, row in sample.iterrows():
            lang = str(row.get('language', 'en'))
            lang_label = {'hi': 'Hindi', 'mr': 'Marathi', 'en': 'English'}.get(lang, 'English')
            catalog_lines.append(f"{row['title']} ({lang_label})")
    catalog_text = "\n".join(catalog_lines)

    messages = [
        {
            "role": "system",
            "content": f"""You are MoodFlix AI, a friendly movie recommendation assistant.
You know Hollywood, Bollywood Hindi and Marathi cinema deeply.
Recommend only movies from the catalog below when suggesting titles.
Answer movie questions enthusiastically and concisely.
Understand Hinglish queries naturally.
Keep responses to 4-5 sentences max or a short bullet list.
If asked about a specific movie give a clear yes or no with reasons.
Format movie titles in bold.

Available movies:
{catalog_text}"""
        }
    ]

    for entry in (chat_history or [])[-6:]:
        role = entry.get('role', 'user')
        content = entry.get('content', '')
        if role in ('user', 'assistant') and content:
            messages.append({"role": role, "content": str(content)})

    messages.append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "MoodFlix"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": messages,
                "max_tokens": 600
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
        elif response.status_code == 401:
            return "⚠️ Invalid OpenRouter API key. Please update ENTER_YOUR_KEY_HERE in app.py."
        elif response.status_code == 429:
            return "⚠️ Rate limit reached. Please wait a moment and try again."
        else:
            return _offline_fallback(user_message, df)

    except requests.exceptions.ConnectionError:
        return "⚠️ No internet connection detected."
    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. Please try again."
    except Exception:
        return _offline_fallback(user_message, df)


def _offline_fallback(user_message, df):
    """Keyword fallback when API is unreachable."""
    import random
    user_lower = user_message.lower()
    keyword_map = {
        'sad':      ['drama', 'emotional'],
        'happy':    ['comedy', 'fun'],
        'scary':    ['horror', 'thriller'],
        'romantic': ['romance', 'love'],
        'action':   ['action', 'adventure'],
        'funny':    ['comedy', 'humor'],
        'hindi':    ['hindi', 'bollywood'],
        'marathi':  ['marathi'],
        'inspired': ['sport', 'biography'],
    }
    matched = []
    for word, tags in keyword_map.items():
        if word in user_lower:
            for tag in tags:
                if df is not None and not df.empty:
                    hits = df[df['tags'].str.contains(tag, case=False, na=False)]
                    matched.extend(hits['title'].head(3).tolist())
    matched = list(dict.fromkeys(matched))[:5]
    if matched:
        return "Here are some picks:\n\n" + "\n".join([f"• {m}" for m in matched])
    return "Tell me a mood like sad, funny, action or a language like Hindi and I will find the perfect movie! 🎬"


def push_notification(message):
    if not message:
        return
    notifications = st.session_state.setdefault('notifications', [])
    notifications.insert(0, str(message))
    st.session_state['notifications'] = notifications[:6]


def sync_current_user():
    user_id = st.session_state.get('user_id')

    # Restore from backup keys if primary missing (survives reruns)
    if not user_id:
        user_id = st.session_state.get('_auth_user_id')
        if user_id:
            st.session_state['user_id'] = user_id

    if not user_id:
        saved_username = st.session_state.get('username') or st.session_state.get('_auth_username')
        if saved_username:
            recovered = db.get_user_by_username(str(saved_username).strip())
            if recovered:
                st.session_state['user_id'] = recovered.get('id')
                st.session_state['username'] = recovered.get('username')
                st.session_state['_auth_user_id'] = recovered.get('id')
                st.session_state['_auth_username'] = recovered.get('username')
                return recovered
        return None

    current_user = db.get_current_user(user_id=int(user_id))
    if not current_user:
        clear_login_state()
        return None

    st.session_state['user_id'] = current_user.get('id')
    st.session_state['username'] = current_user.get('username')
    st.session_state['_auth_user_id'] = current_user.get('id')
    st.session_state['_auth_username'] = current_user.get('username')
    return current_user


def find_movie_row_by_title(movie_title):
    if not movie_title or 'title' not in df.columns:
        return None

    title_series = df['title'].fillna('').astype(str)
    exact_mask = title_series.str.lower() == str(movie_title).strip().lower()
    if exact_mask.any():
        return df[exact_mask].iloc[0]

    partial_mask = title_series.str.contains(str(movie_title).strip(), case=False, na=False)
    if partial_mask.any():
        return df[partial_mask].iloc[0]

    return None


def process_watchlist_add(title: str, user_id: int):
    if not title or not user_id:
        return {"success": False, "message": "Missing title or user."}

    try:
        # Look up movie by title in DB
        movie = db.get_movie_by_title(str(title).strip())

        if not movie:
            # Try case-insensitive search
            all_movies = db.get_all_movies()
            movie = next(
                (m for m in all_movies
                 if m.get('title','').strip().lower() == str(title).strip().lower()),
                None
            )

        if not movie:
            return {"success": False, "message": f"Movie '{title}' not found in database."}

        # Use the DB primary key 'id', NOT 'movie_id'
        db_movie_id = movie.get('id')
        if not db_movie_id:
            return {"success": False, "message": "Movie ID not found."}

        result = db.add_to_watchlist(int(user_id), int(db_movie_id))
        return result

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def flush_pending_watchlist():
    pending_title = str(st.session_state.get('pending_watchlist_title', '')).strip()
    user_id = st.session_state.get('user_id')
    if not pending_title or not user_id:
        return

    result = process_watchlist_add(pending_title, user_id)
    st.session_state['pending_watchlist_title'] = ''
    if result.get('message'):
        push_notification(result['message'])
        st.toast(result['message'])

@st.cache_data(show_spinner=False)
def get_movie_poster_url(movie_id, title):
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}",
            timeout=10,
        )
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"{TMDB_IMAGE_BASE}{poster_path}"
    except:
        pass
    return None

def score_from_id(mid):
    try:
        r = (int(str(mid)[-2:]) % 40) / 10 + 3.0
    except:
        r = round(random.uniform(3.0, 4.8), 1)
    return round(min(max(r, 2.5), 5.0), 1)

SIM_PATH = 'similarity.pkl'

@st.cache_resource
def load_similarity():
    if os.path.exists(SIM_PATH):
        try:
            return pickle.load(open(SIM_PATH, 'rb'))
        except:
            return None
    return None

similarity = load_similarity()

def get_query_param(name, default=''):
    value = st.query_params.get(name, default)
    if isinstance(value, list):
        return value[0] if value else default
    return value

def normalize_search_text(value):
    if not isinstance(value, str):
        return ''
    return re.sub(r'[^a-z0-9]+', '', value.lower().strip())


def parse_search_tokens(query):
    """Parse multi-keyword search; commas imply AND, otherwise OR."""
    if not isinstance(query, str):
        return [], 'any'

    raw_parts = [p.strip() for p in re.split(r'[,+]', query) if p.strip()]
    if len(raw_parts) > 1:
        return raw_parts, 'all'

    tokens = [
        token for token in re.findall(r'[A-Za-z0-9]+', query.lower())
        if len(token) > 1
    ]
    return tokens, 'any'


def autocomplete_search(query, movie_titles):
    """Return top 5 matching movie titles using partial + fuzzy matching."""
    if not isinstance(query, str):
        return []

    q = query.strip().lower()
    if not q:
        return []

    titles = [t for t in movie_titles if isinstance(t, str) and t.strip()]
    if not titles:
        return []

    lower_titles = [t.lower() for t in titles]
    exact = [titles[i] for i, lt in enumerate(lower_titles) if lt == q]
    if exact:
        return exact[:1]

    starts = [titles[i] for i, lt in enumerate(lower_titles) if lt.startswith(q)]
    contains = [titles[i] for i, lt in enumerate(lower_titles) if q in lt and not lt.startswith(q)]
    fuzzy = difflib.get_close_matches(q, lower_titles, n=5, cutoff=0.55)
    fuzzy_titles = []
    for match in fuzzy:
        for i, lt in enumerate(lower_titles):
            if lt == match:
                fuzzy_titles.append(titles[i])
                break

    suggestions = []
    for title in starts + contains + fuzzy_titles:
        if title not in suggestions:
            suggestions.append(title)
        if len(suggestions) >= 5:
            break

    return suggestions[:5]

def build_title_matches(query, df_local):
    if not isinstance(query, str):
        return pd.DataFrame(), 'none'

    working = df_local.copy()
    working['title'] = working['title'].fillna('')
    working['tags'] = working['tags'].fillna('')
    working['title_normalized'] = working['title'].map(normalize_search_text)

    query_clean = query.strip()
    query_normalized = normalize_search_text(query_clean)
    if not query_normalized:
        return pd.DataFrame(), 'none'

    exact_matches = working[working['title_normalized'] == query_normalized]
    if not exact_matches.empty:
        return exact_matches.reset_index(drop=True), 'exact'

    title_choices = working['title_normalized'].tolist()
    fuzzy_candidates = difflib.get_close_matches(query_normalized, title_choices, n=5, cutoff=0.72)
    if fuzzy_candidates:
        fuzzy_matches = working[working['title_normalized'].isin(fuzzy_candidates)]
        if not fuzzy_matches.empty:
            return fuzzy_matches.drop_duplicates(subset=['title']).reset_index(drop=True), 'fuzzy'

    query_tokens = [normalize_search_text(token) for token in re.findall(r'[A-Za-z0-9]+', query_clean)]
    query_tokens = [token for token in query_tokens if token]

    partial_mask = working['title_normalized'].str.contains(query_normalized, na=False)
    if query_tokens:
        token_pattern = '|'.join(re.escape(token) for token in query_tokens)
        partial_mask = partial_mask | working['title_normalized'].str.contains(token_pattern, na=False)
    partial_mask = partial_mask | working['title'].str.contains(query_clean, case=False, na=False)

    partial_matches = working[partial_mask]
    if not partial_matches.empty:
        return partial_matches.drop_duplicates(subset=['title']).head(20).reset_index(drop=True), 'partial'

    return pd.DataFrame(), 'none'


def get_movie_suggestions(query, movie_titles):
    """Return top 5 closest movie titles based on fuzzy + partial matching."""
    if not isinstance(query, str):
        return []

    q = query.strip().lower()
    if not q:
        return []

    titles = [t for t in movie_titles if isinstance(t, str) and t.strip()]
    if not titles:
        return []

    lower_titles = [t.lower() for t in titles]
    exact = [titles[i] for i, lt in enumerate(lower_titles) if lt == q]
    if exact:
        return exact[:1]

    partial = [titles[i] for i, lt in enumerate(lower_titles) if q in lt]
    fuzzy = difflib.get_close_matches(q, lower_titles, n=5, cutoff=0.55)
    fuzzy_titles = []
    for match in fuzzy:
        for i, lt in enumerate(lower_titles):
            if lt == match:
                fuzzy_titles.append(titles[i])
                break

    suggestions = []
    for title in partial + fuzzy_titles:
        if title not in suggestions:
            suggestions.append(title)
        if len(suggestions) >= 5:
            break

    return suggestions[:5]


def fuzzy_search(query, movie_titles):
    query_clean = str(query or '').strip().lower()
    if not query_clean:
        return []

    normalized_titles = {}
    for title in movie_titles or []:
        title_text = str(title).strip()
        if title_text:
            normalized_titles.setdefault(title_text.lower(), title_text)

    if not normalized_titles:
        return []

    matches = difflib.get_close_matches(
        query_clean,
        list(normalized_titles.keys()),
        n=10,
        cutoff=0.5,
    )
    return [normalized_titles[match] for match in matches]


def search_movies(search_query, movies_df):
    if movies_df is None or movies_df.empty:
        return pd.DataFrame(), 'none'

    query = str(search_query or '').strip()
    if not query:
        return movies_df.iloc[0:0].copy(), 'empty'

    working = movies_df.copy()
    if 'title' not in working.columns:
        working['title'] = ''
    if 'tags' not in working.columns:
        working['tags'] = ''

    working['title'] = working['title'].fillna('').astype(str)
    working['tags'] = working['tags'].fillna('').astype(str)

    query_lower = query.lower()
    query_pattern = re.escape(query_lower)

    title_mask = working['title'].str.lower().str.contains(query_pattern, na=False)
    tag_mask = working['tags'].str.lower().str.contains(query_pattern, na=False)
    results = working[title_mask | tag_mask].copy()

    if not results.empty:
        title_exact = results['title'].str.lower() == query_lower
        title_contains = results['title'].str.lower().str.contains(query_pattern, na=False)
        tag_contains = results['tags'].str.lower().str.contains(query_pattern, na=False)
        results['_search_rank'] = 0
        results.loc[tag_contains, '_search_rank'] += 1
        results.loc[title_contains, '_search_rank'] += 2
        results.loc[title_exact, '_search_rank'] += 3
        results = (
            results.sort_values(by=['_search_rank', 'title'], ascending=[False, True])
            .drop(columns=['_search_rank'])
            .reset_index(drop=True)
        )
        return results, 'direct'

    fuzzy_titles = fuzzy_search(query, working['title'].tolist())
    if fuzzy_titles:
        fuzzy_df = working[working['title'].isin(fuzzy_titles)].copy()
        if not fuzzy_df.empty:
            return fuzzy_df.drop_duplicates(subset=['title']).reset_index(drop=True), 'fuzzy'

    return working.iloc[0:0].copy(), 'none'

def find_tag_matches(query, df_local, limit=20, tokens=None, match_mode='any'):
    if not isinstance(query, str):
        return pd.DataFrame()

    working = df_local.copy()
    working['tags'] = working['tags'].fillna('')
    query_clean = query.strip().lower()
    if not query_clean:
        return pd.DataFrame()

    if tokens is None:
        tokens, match_mode = parse_search_tokens(query_clean)

    stop_words = {
        'in', 'of', 'the', 'a', 'an', 'and', 'or', 'to', 'for', 'with', 'on', 'at',
        'movie', 'movies', 'film', 'films', 'show', 'me', 'please', 'suggest',
        'recommend', 'like', 'similar', 'more', 'less', 'but', 'without', 'where',
        'that', 'this', 'these', 'those', 'marathi', 'hindi', 'english', 'hollywood',
        'bollywood', 'inmarathi', 'in hindi', 'inenglish',
    }
    tokens = [t for t in (tokens or []) if t and t not in stop_words]

    if not tokens:
        return pd.DataFrame()

    masks = [working['tags'].str.contains(token, case=False, na=False) for token in tokens]
    combined_mask = masks[0]
    for mask in masks[1:]:
        if match_mode == 'all':
            combined_mask = combined_mask & mask
        else:
            combined_mask = combined_mask | mask

    filtered = working[combined_mask]
    lang_pref = detect_language_preference(query)
    if lang_pref and 'language' in filtered.columns:
        filtered = filtered[filtered['language'].str.lower() == lang_pref]

    return filtered.drop_duplicates(subset=['title']).head(limit).reset_index(drop=True)


def render_search_results(search_query, results_df, match_type='direct'):
    query_text = str(search_query or '').strip()
    if not query_text:
        return

    if results_df is None or results_df.empty:
        st.markdown(
            (
                '<div class="cm-search-suggest-empty">'
                f'🔍 No movies found for "{html.escape(query_text)}"'
                '</div>'
                '<div style="margin-top:10px;color:var(--muted);font-size:13px;line-height:1.7">'
                'Suggestions:<br>'
                '• Check spelling<br>'
                '• Try fewer words<br>'
                '• Try related genres'
                '</div>'
            ),
            unsafe_allow_html=True,
        )
        return

    display_df = results_df.copy()
    if 'tags_preview' not in display_df.columns:
        display_df['tags_preview'] = display_df['tags'].fillna('').astype(str)

    if match_type == 'fuzzy':
        st.markdown(
            '<div style="font-size:13px;color:rgba(255,255,255,0.45);margin:0 0 8px 0">'
            'Showing closest matches'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        render_carousel(f'Search Results for: "{query_text}"', display_df.reset_index(drop=True)),
        unsafe_allow_html=True,
    )

# ══ NL SEARCH: CORE HELPERS START ══
def is_natural_language_query(query: str) -> bool:
    query = (query or '').strip()
    if not query:
        return False
    words = query.split()
    nl_triggers = [
        'show', 'find', 'suggest', 'recommend', 'like', 'similar', 'want',
        'something', 'movie about', 'films about', 'kuch', 'dikhao', 'wali',
        'jaisi', 'aisi', 'ek', 'mujhe', 'chahiye', 'type', 'kind of', 'sort of',
        'but more', 'except', 'without', 'featuring', 'where', 'that has',
        'sad', 'happy', 'funny', 'scary', 'romantic', 'emotional', 'thrilling',
        'ladki', 'sapne', 'family', 'dikhaye', 'dekh', 'dekhne', 'saath',
    ]
    if len(words) > 3:
        return True
    lower_q = query.lower()
    if any(trigger in lower_q for trigger in nl_triggers):
        return True
    return False


def detect_language_preference(query: str) -> str:
    q = (query or '').lower()
    if re.search(r'\bmarathi\b', q):
        return 'mr'
    if re.search(r'\bhindi\b|\bbollywood\b', q):
        return 'hi'
    if re.search(r'\benglish\b|\bhollywood\b', q):
        return 'en'
    return ''


def detect_mood_keywords(query: str) -> list:
    q = (query or '').lower()
    mood_map = {
        'sad': ['drama', 'emotional', 'tear', 'traged', 'loss', 'grief', 'melanch', 'heartbreak'],
        'happy': ['comedy', 'family', 'joy', 'fun', 'laugh', 'cheerful'],
        'funny': ['comedy', 'fun', 'laugh', 'humor'],
        'scary': ['horror', 'ghost', 'monster', 'haunt', 'evil', 'supernatural'],
        'romantic': ['romance', 'love', 'couple', 'heart', 'wedding'],
        'thriller': ['thriller', 'mystery', 'suspense', 'crime', 'twist'],
        'emotional': ['drama', 'emotional', 'tear', 'heartbreak'],
    }
    for trigger, keywords in mood_map.items():
        if trigger in q:
            return keywords
    return []


def filter_by_keywords(df_local: pd.DataFrame, keywords: list) -> pd.DataFrame:
    if df_local is None or df_local.empty or not keywords:
        return df_local
    working = df_local.copy()
    working['tags'] = working['tags'].fillna('').astype(str).str.lower()
    mask = False
    for kw in keywords:
        mask = mask | working['tags'].str.contains(kw, case=False, na=False)
    return working[mask]


def render_nl_carousel(section_title, df_rows, reasons):
    cards = []
    for _, row in df_rows.iterrows():
        title = row.get('title', 'Untitled')
        mid = row.get('movie_id', '')
        reason = reasons.get(title, '')
        img = row.get('poster_url')
        if not img or img is None or not isinstance(img, str):
            img = get_movie_poster_url(mid, title)
        if not img or img is None or not isinstance(img, str):
            img = ''
        detail_href = '?detail=' + quote_plus(str(title))

        trailer_movie_id = str(row.get('movie_id') or '').strip()
        if trailer_movie_id and trailer_movie_id != 'None':
            trailer_url = get_tmdb_trailer_url(trailer_movie_id, title)
        else:
            trailer_url = get_trailer_url(title)

        current_view = str(st.session_state.get('current_view', 'home')).strip().lower()
        view_param = current_view if current_view in {'home', 'my_list', 'movies', 'new_popular'} else 'home'
        add_href = '?add_title=' + quote_plus(str(title)) + '&view=' + view_param

        card_html = '<div class="nl-card">'
        card_html += f'<a href="{detail_href}" target="_self" style="position:absolute;inset:0;z-index:1;"></a>'
        card_html += '<div class="nl-card-poster">'
        if img:
            card_html += (
                f'<img src="{img}" alt="{html.escape(str(title))}" loading="lazy" '
                'onerror="this.onerror=null;this.src=\"\";this.style.display=\"none\";">'
            )
        else:
            card_html += (
                '<div style="width:100%;height:100%;background:#1a1a2e;display:flex;'
                'align-items:center;justify-content:center;color:#9aa4b2;letter-spacing:1px;'
                'font-weight:800;font-size:22px;">🎬</div>'
            )
        card_html += '<div class="nl-ai-badge">🧠 AI Pick</div>'
        card_html += (
            '<div class="nl-card-overlay">'
            f'<a class="nl-trailer-btn" href="{trailer_url}" target="_blank" rel="noopener noreferrer">▶ Trailer</a>'
            f'<a class="nl-list-btn" href="{add_href}" target="_self">+ My List</a>'
            '</div>'
        )
        card_html += '</div>'
        card_html += (
            '<div class="nl-card-info">'
            f'<div class="nl-card-title">{html.escape(str(title))}</div>'
            f'<div class="nl-card-reason">✨ {html.escape(str(reason))}</div>'
            '</div>'
        )
        card_html += '</div>'
        cards.append(card_html)

    cards_html = ''.join(cards)
    return (
        '<div class="cm-section">'
        f'<div class="section-header"><div class="title">{section_title}</div>'
        '<div style="color:var(--muted);font-weight:700;cursor:pointer">See All →</div></div>'
        f'<div class="nl-carousel">{cards_html}</div>'
        '</div>'
    )


def render_nl_search_results(query: str, result: dict, df_local: pd.DataFrame) -> bool:
    """Render AI natural language search results with understanding card + movie carousel."""
    understood = result.get('understood', {})
    recommendations = result.get('recommendations', [])
    error = result.get('error')

    if understood:
        mood = understood.get('mood', '')
        genre = understood.get('genre', '')
        theme = understood.get('theme', '')
        lang_pref = understood.get('language_preference', '')
        explanation = understood.get('explanation', '')
        similar_to = understood.get('similar_to', [])

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(229,9,20,0.08), rgba(255,107,157,0.05));
                border: 1px solid rgba(229,9,20,0.2);
                border-radius: 16px;
                padding: 20px 24px;
                margin: 16px 0;
                position: relative;
                overflow: hidden;
            ">
                <div style="
                    position:absolute;top:0;left:0;right:0;height:3px;
                    background:linear-gradient(90deg,#E50914,#ff6b6b,#E50914);
                "></div>

                <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
                    <div style="
                        width:36px;height:36px;border-radius:50%;
                        background:rgba(229,9,20,0.15);
                        display:flex;align-items:center;justify-content:center;
                        font-size:18px
                    ">🧠</div>
                    <div>
                        <div style="font-size:13px;font-weight:700;color:#E50914;letter-spacing:0.5px">AI UNDERSTOOD YOUR SEARCH</div>
                        <div style="font-size:11px;color:rgba(255,255,255,0.4);margin-top:1px">Here's what MoodFlix detected</div>
                    </div>
                </div>

                <div style="font-size:14px;color:rgba(255,255,255,0.85);line-height:1.6;margin-bottom:16px;font-style:italic">
                    "{html.escape(explanation)}"
                </div>

                <div style="display:flex;flex-wrap:wrap;gap:8px">
                    {f'<span style="background:rgba(229,9,20,0.15);border:1px solid rgba(229,9,20,0.3);color:#ff8080;font-size:11px;padding:4px 10px;border-radius:20px;font-weight:600">😊 {html.escape(mood)}</span>' if mood else ''}
                    {f'<span style="background:rgba(91,141,238,0.12);border:1px solid rgba(91,141,238,0.3);color:#8ab4f8;font-size:11px;padding:4px 10px;border-radius:20px;font-weight:600">🎬 {html.escape(genre)}</span>' if genre else ''}
                    {f'<span style="background:rgba(46,204,113,0.12);border:1px solid rgba(46,204,113,0.3);color:#6ee7a0;font-size:11px;padding:4px 10px;border-radius:20px;font-weight:600">💡 {html.escape(theme)}</span>' if theme else ''}
                    {f'<span style="background:rgba(255,153,51,0.12);border:1px solid rgba(255,153,51,0.3);color:#ffb347;font-size:11px;padding:4px 10px;border-radius:20px;font-weight:600">🌐 {html.escape(lang_pref)}</span>' if lang_pref and lang_pref != "any" else ''}
                    {''.join([f'<span style="background:rgba(155,89,182,0.12);border:1px solid rgba(155,89,182,0.3);color:#c39bd3;font-size:11px;padding:4px 10px;border-radius:20px;font-weight:600">🎯 Like: {html.escape(s)}</span>' for s in (similar_to or [])[:3]])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if error:
        st.warning("⚠️ AI search is temporarily unavailable. Showing best matches from your library.")
        return False

    if not recommendations:
        st.info("No matching movies found. Try rephrasing your query.")
        return False

    matched_rows = []
    reasons = {}
    for rec in recommendations:
        title = str(rec.get('title', '')).strip()
        reason = str(rec.get('reason', '')).strip()
        if not title:
            continue
        match = df_local[df_local['title'] == title]
        if match.empty:
            match = df_local[df_local['title'].str.lower() == title.lower()]
        if match.empty:
            all_titles = df_local['title'].tolist()
            close = difflib.get_close_matches(title, all_titles, n=1, cutoff=0.7)
            if close:
                match = df_local[df_local['title'] == close[0]]
        if not match.empty:
            matched_rows.append(match.iloc[0])
            reasons[match.iloc[0]['title']] = reason

    if not matched_rows:
        st.info("Couldn't match AI recommendations to available movies.")
        return False

    rec_df = pd.DataFrame(matched_rows).reset_index(drop=True)
    st.markdown(
        render_nl_carousel("🧠 Perfect Matches For You", rec_df, reasons),
        unsafe_allow_html=True,
    )
    return True


def render_nl_fallback_results(query: str, df_local: pd.DataFrame):
    lang_pref = detect_language_preference(query)
    mood_keywords = detect_mood_keywords(query)
    tag_tokens, match_mode = parse_search_tokens(query)
    tag_matches = find_tag_matches(
        query,
        df_local,
        limit=12,
        tokens=tag_tokens,
        match_mode=match_mode,
    )

    if not tag_matches.empty and mood_keywords:
        filtered = filter_by_keywords(tag_matches, mood_keywords)
        if not filtered.empty:
            tag_matches = filtered.head(12).reset_index(drop=True)

    if tag_matches.empty and lang_pref:
        working = df_local.copy()
        if 'language' in working.columns:
            working['language'] = working['language'].fillna('').astype(str).str.lower()
            working = working[working['language'] == lang_pref]
        if not working.empty and mood_keywords:
            working = filter_by_keywords(working, mood_keywords)
        if not working.empty:
            tag_matches = working.sample(
                n=min(len(working), 12),
                random_state=42,
            ).reset_index(drop=True)

    if tag_matches.empty:
        st.info("No matching movies found. Try rephrasing your query.")
        return

    label = "🔎 Best matches"
    if lang_pref == 'mr':
        label = "🎯 Marathi Picks"
    elif lang_pref == 'hi':
        label = "🎯 Hindi Picks"
    elif lang_pref == 'en':
        label = "🎯 English Picks"

    st.markdown(
        render_carousel(label, tag_matches.reset_index(drop=True)),
        unsafe_allow_html=True,
    )
# ══ NL SEARCH: CORE HELPERS END ══

def recommend(title, df_local, topn=5):
    if similarity is None:
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        cv = CountVectorizer(max_features=5000, stop_words='english')
        vectors = cv.fit_transform(df_local['tags'].fillna('')).toarray()
        sim = cosine_similarity(vectors)
    else:
        sim = similarity

    if title not in df_local['title'].values:
        return []
    idx = int(df_local[df_local['title'] == title].index[0])
    distances = sim[idx]
    movie_list = sorted(list(enumerate(distances)), key=lambda x: x[1], reverse=True)[1: topn+1]
    results = []
    for i in movie_list:
        r = df_local.iloc[i[0]]
        results.append({'title': r['title'], 'movie_id': r['movie_id'], 'poster_url': r.get('poster_url')})
    return results

@st.cache_data(show_spinner=False, ttl=30)
def get_watchlist_titles(user_id):
    """Return set of titles in user's watchlist for fast lookup."""
    if not user_id:
        return set()
    rows = db.get_watchlist(int(user_id))
    return {str(r.get('title', '')).strip().lower() for r in rows}

def render_card_html(row):
    title = row.get('title', 'Untitled')
    mid = row.get('movie_id', '')
    tags = row.get('tags', '')
    genre = str(row.get('tags_preview') or '').strip() or (tags.split()[0].title() if tags else 'Drama')
    rating = score_from_id(mid)
    img = row.get('poster_url')
    if not img or img is None or not isinstance(img, str):
        img = get_movie_poster_url(mid, title)
    if not img or img is None or not isinstance(img, str):
        img = ''
    safe_title = html.escape(title)
    safe_genre = html.escape(genre)
    title_initials = ''.join([w[0] for w in str(title).split()[:2] if w]).upper()
    title_initials = title_initials or 'MV'
    detail_href = '?detail=' + quote_plus(title)

    trailer_movie_id = str(row.get('movie_id') or '').strip()
    if trailer_movie_id and trailer_movie_id != 'None':
        trailer_url = get_tmdb_trailer_url(trailer_movie_id, title)
    else:
        trailer_url = get_trailer_url(title)

    lang = str(row.get('language') or 'en').upper()
    lang_badge = ''
    if lang in ('HI', 'MR'):
        lang_label = '🇮🇳 Hindi' if lang == 'HI' else '🇮🇳 Marathi'
        lang_badge = (
            '<div style="position:absolute;top:8px;left:8px;background:rgba(229,9,20,0.85);'
            'color:#fff;font-size:9px;padding:2px 6px;border-radius:4px;font-weight:700;z-index:2">'
            + lang_label + '</div>'
        )

    html_str = '<div class="card">'
    html_str += '<a href="' + detail_href + '" target="_self" style="position:absolute;inset:0;z-index:2;"></a>'
    html_str += '<div class="card-img-container">'
    if img:
        html_str += (
            f'<a href="{trailer_url}" target="_blank" '
            f'rel="noopener noreferrer" class="card-poster-link">'
            f'<img class="card-poster" src="{img}" '
            f'alt="{html.escape(title)}" loading="lazy" '
            f'onerror="this.onerror=null;this.src=\'\';this.style.display=\'none\';">'
            f'{lang_badge}'
            f'<div class="card-play-overlay">'
            f'<div class="card-play-icon">▶</div>'
            f'</div>'
            f'</a>'
        )
    else:
        html_str += (
            '<div style="width:100%;height:100%;background:#1a1a2e;display:flex;'
            'align-items:center;justify-content:center;color:#9aa4b2;letter-spacing:1px;'
            'font-weight:800;font-size:22px;">' + title_initials + '</div>'
        )
    html_str += '<div class="badge">' + str(rating) + '⭐</div>'
    current_view = str(st.session_state.get('current_view', 'home')).strip().lower()
    view_param = current_view if current_view in {'home', 'my_list', 'movies', 'new_popular'} else 'home'
    add_href = '?add_title=' + quote_plus(title) + '&view=' + view_param
    heart_href = add_href + '&heart=1'
    user_id = st.session_state.get('user_id')
    watchlist_titles = get_watchlist_titles(user_id) if user_id else set()
    is_in_watchlist = str(title).strip().lower() in watchlist_titles
    heart_icon = '❤️' if is_in_watchlist else '♡'
    heart_style = 'background:rgba(229,9,20,0.75);' if is_in_watchlist else ''
    html_str += (
        '<a class="heart" href="' + heart_href + '" target="_self" title="Add to favourites" '
        'style="' + heart_style + '">' + heart_icon + '</a>'
    )
    html_str += (
        f'<a class="card-trailer" href="{trailer_url}" '
        f'target="_blank" rel="noopener noreferrer" '
        f'title="Watch Trailer">▶ Trailer</a>'
    )
    recommend_href = '?detail=' + quote_plus(title)
    html_str += (
        '<a class="card-recommend" href="' + recommend_href + '" '
        'target="_self" title="View recommendations">Recommend</a>'
    )
    html_str += '<a class="card-add" href="' + add_href + '" target="_self">+ My List</a>'
    html_str += '</div><div class="meta"><div class="title">' + safe_title + '</div><div class="sub">' + safe_genre + '</div></div></div>'
    return html_str

def render_carousel(section_title, df_rows):
    cards_html = ''.join([render_card_html(r) for _, r in df_rows.iterrows()])
    return '<div class="cm-section"><div class="section-header"><div class="title">' + section_title + '</div><div style="color:var(--muted);font-weight:700;cursor:pointer">See All →</div></div><div class="cm-carousel">' + cards_html + '</div></div>'


def render_new_popular_page(df_local):
    """Render New & Popular page with trending, top rated, and most watched sections."""
    st.markdown(
        '<div style="padding:32px 0 18px 0">'
        '<h2 style="color:#fff;font-size:32px;font-weight:900;margin:0 0 6px 0">'
        '🔥 New &amp; Popular</h2>'
        '<p style="color:#bdbdbd;font-size:14px;margin:0">'
        "What everyone's watching right now</p>"
        '</div>',
        unsafe_allow_html=True,
    )

    tab_labels = ['🔥 Trending', '⭐ Top Rated', '👁️ Most Watched', '🆕 Recently Added']
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        trending_df = df_local.sample(n=min(len(df_local), 40), random_state=42).reset_index(drop=True)
        st.markdown(
            '<div style="color:#bdbdbd;font-size:13px;margin:12px 0 4px 0">'
            f'<strong style="color:#fff">{len(trending_df)}</strong> trending movies right now</div>',
            unsafe_allow_html=True,
        )
        for index in range(0, len(trending_df), 8):
            chunk = trending_df.iloc[index:index + 8]
            st.markdown(
                render_carousel(f'🔥 Trending #{index + 1}–{min(index + 8, len(trending_df))}', chunk),
                unsafe_allow_html=True,
            )

    with tabs[1]:
        rated_df = df_local.copy()
        rated_df['_score'] = rated_df['movie_id'].apply(score_from_id)
        rated_df = rated_df.sort_values('_score', ascending=False).drop(columns=['_score']).head(40).reset_index(drop=True)
        st.markdown(
            '<div style="color:#bdbdbd;font-size:13px;margin:12px 0 4px 0">'
            f'<strong style="color:#fff">{len(rated_df)}</strong> highest rated movies</div>',
            unsafe_allow_html=True,
        )
        for index in range(0, len(rated_df), 8):
            chunk = rated_df.iloc[index:index + 8]
            st.markdown(
                render_carousel(f'⭐ Top Rated #{index + 1}–{min(index + 8, len(rated_df))}', chunk),
                unsafe_allow_html=True,
            )

    with tabs[2]:
        watched_df = df_local.sample(n=min(len(df_local), 40), random_state=99).reset_index(drop=True)
        st.markdown(
            '<div style="color:#bdbdbd;font-size:13px;margin:12px 0 4px 0">'
            f'<strong style="color:#fff">{len(watched_df)}</strong> most watched this week</div>',
            unsafe_allow_html=True,
        )
        for index in range(0, len(watched_df), 8):
            chunk = watched_df.iloc[index:index + 8]
            st.markdown(
                render_carousel(f'👁️ Most Watched #{index + 1}–{min(index + 8, len(watched_df))}', chunk),
                unsafe_allow_html=True,
            )

    with tabs[3]:
        if 'id' in df_local.columns:
            recent_df = df_local.sort_values('id', ascending=False).head(40).reset_index(drop=True)
        else:
            recent_df = df_local.tail(40).reset_index(drop=True)
        st.markdown(
            '<div style="color:#bdbdbd;font-size:13px;margin:12px 0 4px 0">'
            f'<strong style="color:#fff">{len(recent_df)}</strong> recently added to MoodFlix</div>',
            unsafe_allow_html=True,
        )
        for index in range(0, len(recent_df), 8):
            chunk = recent_df.iloc[index:index + 8]
            st.markdown(
                render_carousel(f'🆕 Recently Added #{index + 1}–{min(index + 8, len(recent_df))}', chunk),
                unsafe_allow_html=True,
            )


def render_mood_section(df):
    """Render mood picker UI and matching movie carousel inline on home page."""

    selected_mood = st.session_state.get('selected_mood', None)

    st.markdown(
        '<div class="cm-mood-header">'
        '<h3 class="cm-section-title">🎭 What\'s Your Mood?</h3>'
        '<p class="cm-mood-sub">Pick a mood and we\'ll find the perfect movie for you</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    moods = list(MOOD_MAP.keys())
    row1 = moods[:4]
    row2 = moods[4:]

    for mood_row in [row1, row2]:
        cols = st.columns(len(mood_row), gap="small")
        for i, mood_key in enumerate(mood_row):
            mood = MOOD_MAP[mood_key]
            is_active = selected_mood == mood_key
            with cols[i]:
                if st.button(
                    f"{mood['emoji']} {mood_key}",
                    key=f'mood_btn_{mood_key}',
                    use_container_width=True,
                ):
                    if selected_mood == mood_key:
                        st.session_state['selected_mood'] = None
                    else:
                        st.session_state['selected_mood'] = mood_key
                    st.rerun()

    if selected_mood and selected_mood in MOOD_MAP:
        mood = MOOD_MAP[selected_mood]
        mood_key_css = selected_mood
        st.markdown(f'''
        <style>
        div.st-key-mood_btn_{mood_key_css} button {{
            background: {mood["bg"]} !important;
            border: 1.5px solid {mood["border"]} !important;
            color: {mood["color"]} !important;
            font-weight: 800 !important;
            box-shadow: 0 4px 18px {mood["bg"]} !important;
            transform: translateY(-2px) !important;
        }}
        </style>
        ''', unsafe_allow_html=True)

    if selected_mood and selected_mood in MOOD_MAP:
        mood = MOOD_MAP[selected_mood]
        mood_movies = get_movies_by_mood(df, selected_mood, limit=20)

        st.markdown(
            f'<div class="cm-mood-result" style="border-left:3px solid {mood["color"]}">'
            f'<span style="font-size:28px">{mood["emoji"]}</span>'
            f'<div>'
            f'<div style="color:{mood["color"]};font-weight:800;font-size:16px">'
            f'{mood_key_css} Mood</div>'
            f'<div style="color:#bdbdbd;font-size:13px">{mood["description"]}</div>'
            f'</div>'
            f'<div style="margin-left:auto;color:{mood["color"]};font-weight:700;font-size:13px">'
            f'{len(mood_movies)} movies found</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if not mood_movies.empty:
            st.markdown(
                render_carousel(
                    f'{mood["emoji"]} {selected_mood} Picks',
                    mood_movies
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="text-align:center;padding:40px;color:#bdbdbd">'
                f'No movies found for {selected_mood} mood. Try another!</div>',
                unsafe_allow_html=True,
            )


def render_profile_page(df):
    """Render user profile page."""

    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username', '')

    if not user_id or not username:
        st.markdown(
            '<div style="text-align:center;padding:80px 0">'
            '<div style="font-size:48px;margin-bottom:16px">🔐</div>'
            '<h3 style="color:#fff">Please sign in to view your profile</h3>'
            '<p style="color:#bdbdbd">Sign in using the account icon in the top right</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    stats = get_user_stats(user_id, df)
    initials = ''.join([w[0].upper() for w in username.split()[:2]]) or username[0].upper()

    # Profile header
    st.markdown(
        f'<div class="cm-profile-page-header">'
        f'  <div class="cm-profile-page-avatar">{initials}</div>'
        f'  <div class="cm-profile-page-info">'
        f'    <h2 class="cm-profile-page-name">{username}</h2>'
        f'    <p class="cm-profile-page-sub">MoodFlix Member</p>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Stats cards
    col1, col2, col3 = st.columns(3, gap="small")

    with col1:
        st.markdown(
            f'<div class="cm-stat-card">'
            f'  <div class="cm-stat-icon">🎬</div>'
            f'  <div class="cm-stat-value">{stats.get("total_watched", 0)}</div>'
            f'  <div class="cm-stat-label">Movies in Watchlist</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col2:
        top_genres = stats.get('top_genres', [])
        top_genre = top_genres[0][0] if top_genres else 'None yet'
        st.markdown(
            f'<div class="cm-stat-card">'
            f'  <div class="cm-stat-icon">🏆</div>'
            f'  <div class="cm-stat-value" style="font-size:22px">{top_genre}</div>'
            f'  <div class="cm-stat-label">Favourite Genre</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div class="cm-stat-card">'
            f'  <div class="cm-stat-icon">⭐</div>'
            f'  <div class="cm-stat-value">{len(stats.get("top_genres", []))}</div>'
            f'  <div class="cm-stat-label">Genres Explored</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    # Favourite genres bar
    top_genres = stats.get('top_genres', [])
    if top_genres:
        st.markdown(
            '<h3 class="cm-section-title" style="margin:0 0 14px 0">'
            '🎭 Favourite Genres</h3>',
            unsafe_allow_html=True,
        )

        max_count = top_genres[0][1] if top_genres else 1
        GENRE_COLORS = {
            'Action':'#E50914','Horror':'#9b59b6','Comedy':'#f7c948',
            'Romance':'#ff6b9d','Drama':'#5b8dee','Thriller':'#1abc9c',
            'Adventure':'#e67e22','Fantasy':'#2ecc71','Animation':'#3498db',
            'Sci-Fi':'#00bcd4','Biography':'#ff9800','Mystery':'#607d8b',
            'War':'#795548','Sports':'#4caf50','Family':'#ffeb3b',
            'Crime':'#f44336','Magic':'#ab47bc','Space':'#29b6f6',
            'Musical':'#ec407a',
        }

        genre_html = '<div class="cm-genre-bars">'
        for genre, count in top_genres:
            pct = int((count / max_count) * 100)
            color = GENRE_COLORS.get(genre, '#E50914')
            genre_html += (
                f'<div class="cm-genre-bar-row">'
                f'  <div class="cm-genre-bar-label">{genre}</div>'
                f'  <div class="cm-genre-bar-track">'
                f'    <div class="cm-genre-bar-fill" '
                f'         style="width:{pct}%;background:{color}"></div>'
                f'  </div>'
                f'  <div class="cm-genre-bar-count">{count}</div>'
                f'</div>'
            )
        genre_html += '</div>'
        st.markdown(genre_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="color:#bdbdbd;padding:20px 0">'
            'Add movies to your watchlist to see your genre preferences!</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    # Watchlist preview
    watchlist = stats.get('watchlist', [])
    if watchlist:
        st.markdown(
            '<h3 class="cm-section-title" style="margin:0 0 14px 0">'
            '❤️ My Watchlist</h3>',
            unsafe_allow_html=True,
        )
        watchlist_df = pd.DataFrame(watchlist)
        st.markdown(
            render_carousel('', watchlist_df.reset_index(drop=True)),
            unsafe_allow_html=True,
        )


def render_movie_detail_page(df):
    """Render full movie detail page when a card is clicked."""

    title = st.session_state.get('detail_movie', '')
    if not title:
        st.session_state['current_view'] = 'home'
        st.rerun()
        return

    # Look up movie row
    row = df[df['title'].str.strip().str.lower() == title.strip().lower()]
    if row.empty:
        st.warning("Movie not found.")
        return

    movie = row.iloc[0]
    movie_title = str(movie.get('title', '')).strip()
    poster_url = str(movie.get('poster_url') or '').strip()
    tags = str(movie.get('tags') or '').lower()
    movie_id_val = movie.get('movie_id', '')

    # Validate poster URL
    if not poster_url.startswith('http'):
        poster_url = get_movie_poster_url(movie_id_val, movie_title) or ''

    # -- BACK BUTTON ------------------------------------------------------
    if st.button('← Back', key='detail_back'):
        st.session_state['current_view'] = st.session_state.get('_prev_view', 'home')
        st.session_state['detail_movie'] = ''
        st.rerun()

    # -- HERO BACKDROP + POSTER -------------------------------------------
    backdrop_html = '<div class="cm-detail-hero">'
    if poster_url:
        backdrop_html += (
            f'<div class="cm-detail-backdrop" '
            f'style="background-image:url(\'{poster_url}\')"></div>'
        )
    backdrop_html += '<div class="cm-detail-backdrop-overlay"></div>'
    backdrop_html += '<div class="cm-detail-hero-content">'

    # Poster
    if poster_url:
        backdrop_html += (
            f'<img class="cm-detail-poster" src="{poster_url}" '
            f'alt="{movie_title}" '
            f'onerror="this.style.display=\'none\'">'
        )
    else:
        backdrop_html += (
            f'<div class="cm-detail-poster cm-detail-poster-fallback">🎬</div>'
        )

    # Info panel
    backdrop_html += '<div class="cm-detail-info">'
    backdrop_html += f'<h1 class="cm-detail-title">{movie_title}</h1>'

    # Genre pills from tags
    GENRE_STEMS = {
        'action': 'Action', 'horror': 'Horror', 'comedy': 'Comedy',
        'romance': 'Romance', 'drama': 'Drama', 'thriller': 'Thriller',
        'adventur': 'Adventure', 'fantasy': 'Fantasy', 'animat': 'Animation',
        'scifi': 'Sci-Fi', 'biographi': 'Biography', 'mysteri': 'Mystery',
        'war': 'War', 'sport': 'Sports', 'famili': 'Family', 'crime': 'Crime',
        'space': 'Space', 'magic': 'Magic', 'music': 'Musical',
    }
    GENRE_COLORS = {
        'Action': '#E50914', 'Horror': '#9b59b6', 'Comedy': '#f7c948',
        'Romance': '#ff6b9d', 'Drama': '#5b8dee', 'Thriller': '#1abc9c',
        'Adventure': '#e67e22', 'Fantasy': '#2ecc71', 'Animation': '#3498db',
        'Sci-Fi': '#00bcd4', 'Biography': '#ff9800', 'Mystery': '#607d8b',
        'War': '#795548', 'Sports': '#4caf50', 'Family': '#ffeb3b',
        'Crime': '#f44336', 'Magic': '#ab47bc', 'Space': '#29b6f6',
        'Musical': '#ec407a',
    }
    tag_words = tags.split()
    genres_found = []
    seen_genres = set()
    for word in tag_words:
        for stem, label in GENRE_STEMS.items():
            if word.startswith(stem) and label not in seen_genres:
                genres_found.append(label)
                seen_genres.add(label)
                break
        if len(genres_found) >= 4:
            break

    if genres_found:
        pills_html = '<div class="cm-detail-pills">'
        for g in genres_found:
            color = GENRE_COLORS.get(g, '#E50914')
            pills_html += (
                f'<span class="cm-detail-pill" '
                f'style="background:rgba(0,0,0,0.3);'
                f'border-color:{color};color:{color}">{g}</span>'
            )
        pills_html += '</div>'
        backdrop_html += pills_html

    # Overview from tags (first 20 meaningful words)
    stop = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'have',
            'been', 'they', 'their', 'when', 'will', 'into', 'about'}
    overview_words = [
        w.title() for w in tag_words[:40]
        if len(w) > 4 and w not in stop and w.isalpha()
    ][:18]
    overview = ' '.join(overview_words) if overview_words else 'A must-watch cinematic experience.'
    backdrop_html += f'<p class="cm-detail-overview">{overview}.</p>'

    # Add to Watchlist button (uses existing query param)
    add_href = '?add_title=' + quote_plus(movie_title)
    backdrop_html += (
        f'<div class="cm-detail-actions">'
        f'<a class="cm-detail-btn-add" href="{add_href}" target="_self">+ Add to Watchlist</a>'
        f'</div>'
    )

    backdrop_html += '</div>'  # cm-detail-info
    backdrop_html += '</div>'  # cm-detail-hero-content
    backdrop_html += '</div>'  # cm-detail-hero

    st.markdown(backdrop_html, unsafe_allow_html=True)

    st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)

    # -- CAST INFO ---------------------------------------------------------
    # Extract likely person names from tags (capitalized multi-char words)
    cast_candidates = []
    seen_cast = set()
    for word in tag_words:
        w = word.strip()
        if (len(w) >= 5 and w.isalpha()
                and w not in seen_cast
                and w not in GENRE_STEMS):
            cast_candidates.append(w.title())
            seen_cast.add(w)
        if len(cast_candidates) >= 5:
            break

    if cast_candidates:
        st.markdown(
            '<h3 class="cm-section-title" style="margin:0 0 14px 0">🎭 Cast & Crew</h3>',
            unsafe_allow_html=True,
        )
        cast_html = '<div class="cm-detail-cast">'
        for name in cast_candidates[:5]:
            initials = name[0].upper()
            cast_html += (
                f'<div class="cm-cast-card">'
                f'  <div class="cm-cast-avatar">{initials}</div>'
                f'  <div class="cm-cast-name">{name}</div>'
                f'</div>'
            )
        cast_html += '</div>'
        st.markdown(cast_html, unsafe_allow_html=True)

    st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)

    # -- SIMILAR MOVIES CAROUSEL ------------------------------------------
    try:
        recs = recommend(movie_title, df, topn=8)
        if recs:
            rec_df = pd.DataFrame(recs)
            st.markdown(
                '<h3 class="cm-section-title" style="margin:0 0 14px 0">'
                '🎬 Similar Movies</h3>',
                unsafe_allow_html=True,
            )
            st.markdown(
                render_carousel('', rec_df.reset_index(drop=True)),
                unsafe_allow_html=True,
            )
    except Exception:
        pass


def render_because_you_watched(df):
    """
    Render 'Because You Watched' carousels on home page.
    Only shown when user is logged in and has watchlist items.
    """
    user_id = st.session_state.get('user_id')
    if not user_id:
        return

    sections = get_because_you_watched(df, user_id, topn=8)

    if not sections:
        return

    st.markdown(
        '<div class="cm-byw-header">'
        '<h3 class="cm-section-title">🎬 Because You Watched</h3>'
        '<p class="cm-byw-sub">Recommendations based on your watchlist</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    for section in sections:
        source = section['source_title']
        movies = section['movies']

        if movies.empty:
            continue

        st.markdown(
            f'<div class="cm-byw-source">'
            f'<span class="cm-byw-dot"></span>'
            f'<span class="cm-byw-label">Because you watched</span>'
            f'<span class="cm-byw-title">"{source}"</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            render_carousel(f'Similar to {source}', movies),
            unsafe_allow_html=True,
        )


def md_to_html(text):
    """Convert markdown-like text to safe HTML with a fallback."""
    safe_text = '' if text is None else str(text)
    try:
        markdown = importlib.import_module('markdown')
        return markdown.markdown(safe_text, extensions=['extra', 'sane_lists'])
    except Exception:
        escaped = html.escape(safe_text).replace('\n', '<br>')
        return f'<p>{escaped}</p>'


def extract_titles_from_response(response, df_local, limit=5):
    """Extract movie titles from AI responses and map to posters."""
    if not response or df_local is None or df_local.empty:
        return []

    text = str(response)
    text_lower = text.lower()

    title_col = 'title'
    poster_col = 'poster_url' if 'poster_url' in df_local.columns else None
    movie_col = 'movie_id' if 'movie_id' in df_local.columns else None

    lookup = {}
    cols = [title_col]
    if poster_col:
        cols.append(poster_col)
    if movie_col:
        cols.append(movie_col)

    for _, row in df_local[cols].dropna(subset=[title_col]).iterrows():
        title = str(row[title_col]).strip()
        if title:
            lookup[title.lower()] = {
                'title': title,
                'poster': str(row.get(poster_col, '')) if poster_col else '',
                'movie_id': str(row.get(movie_col, '')) if movie_col else '',
            }

    def _normalize_poster(value):
        val = str(value or '').strip()
        if not val:
            return ''
        if val.startswith('http'):
            return val
        if val.startswith('/'):
            return f"{TMDB_IMAGE_BASE}{val}"
        return ''

    def _tmdb_search(title):
        try:
            resp = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params={
                    "api_key": TMDB_API_KEY,
                    "query": title,
                },
                timeout=6,
            )
            data = resp.json()
            results = data.get('results', [])
            if results:
                item = results[0]
                poster_path = item.get('poster_path')
                return {
                    'movie_id': str(item.get('id', '')),
                    'poster': f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else '',
                }
        except Exception:
            return {}
        return {}

    hits = []
    seen = set()

    # Pass 1: scan known DB titles in the response
    for key, row_data in lookup.items():
        if len(key) < 3:
            continue
        if key in text_lower and key not in seen:
            hits.append({
                'title': row_data['title'],
                'poster': _normalize_poster(row_data.get('poster', '')),
                'movie_id': row_data.get('movie_id', ''),
            })
            seen.add(key)
        if len(hits) >= limit:
            return hits

    # Pass 2: extract explicit titles from quotes or bold markup
    candidates = []
    candidates += re.findall(r'"([^"]{2,80})"\s*\(\d{4}\)', text)
    candidates += re.findall(r'\*\*([^*]{2,80})\*\*', text)
    quoted = re.findall(r'"([^"]{2,80})"|\'([^\']{2,80})\'', text)
    candidates += [q[0] or q[1] for q in quoted if (q[0] or q[1])]

    for cand in candidates:
        if len(hits) >= limit:
            break
        title = cand.strip()
        key = title.lower()
        if not title or key in seen:
            continue
        if key in lookup:
            row_data = lookup[key]
            hits.append({
                'title': row_data['title'],
                'poster': _normalize_poster(row_data.get('poster', '')),
                'movie_id': row_data.get('movie_id', ''),
            })
            seen.add(key)
            continue

        tmdb_data = _tmdb_search(title)
        hits.append({
            'title': title,
            'poster': tmdb_data.get('poster', ''),
            'movie_id': tmdb_data.get('movie_id', ''),
        })
        seen.add(key)

    return hits[:limit]


def render_chatbot_page(df):

    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if 'last_user_message' not in st.session_state:
        st.session_state['last_user_message'] = ''
    if 'chat_mood' not in st.session_state:
        st.session_state['chat_mood'] = None
    if 'genre_filter' in st.session_state:
        del st.session_state['genre_filter']
    if 'mood_filter' in st.session_state:
        del st.session_state['mood_filter']
    if 'active_filter' in st.session_state:
        del st.session_state['active_filter']

    YOUR_OPENROUTER_KEY = "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"


    # ── HEADER ──
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f0f1a 0%,#1a0a0a 50%,#0a0a1a 100%);border:1px solid rgba(229,9,20,0.2);border-radius:20px;padding:40px;margin-bottom:24px;position:relative;overflow:hidden;">
    <div style="position:absolute;top:20px;right:20px;background:rgba(46,204,113,0.15);border:1px solid rgba(46,204,113,0.4);border-radius:20px;padding:6px 14px;font-size:12px;color:#2ecc71;font-weight:600;">● AI POWERED</div>
    <h1 style="font-size:42px;font-weight:800;margin:0 0 8px 0;color:white;">MoodFlix <span style="color:#E50914">AI</span></h1>
    <p style="color:rgba(255,255,255,0.5);font-size:15px;margin:0 0 32px 0;">Your personal movie guide — <strong style="color:white">4,800+ films</strong> at your fingertips</p>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px;"><div style="font-size:22px">⭐</div><div style="font-size:22px;font-weight:800;color:white">4,800+</div><div style="font-size:12px;color:rgba(255,255,255,0.4)">Movies</div></div>
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px;"><div style="font-size:22px">🎭</div><div style="font-size:22px;font-weight:800;color:white">8</div><div style="font-size:12px;color:rgba(255,255,255,0.4)">Moods</div></div>
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px;"><div style="font-size:22px">⚡</div><div style="font-size:22px;font-weight:800;color:white">Instant</div><div style="font-size:12px;color:rgba(255,255,255,0.4)">Results</div></div>
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px;"><div style="font-size:22px">🆓</div><div style="font-size:22px;font-weight:800;color:white">Free</div><div style="font-size:12px;color:rgba(255,255,255,0.4)">Always</div></div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # ── MOOD FILTER ROW ──
    st.markdown(
        '<div class="cm-ai-mood-label">🎯 Filter by mood first:</div>',
        unsafe_allow_html=True,
    )

    MOODS = [
        ('All', '🎬', ''),
        ('Action', '🤩', '#E50914'),
        ('Comedy', '😄', '#f7c948'),
        ('Horror', '😱', '#9b59b6'),
        ('Romance', '💕', '#ff6b9d'),
        ('Sci-Fi', '🚀', '#1abc9c'),
        ('Drama', '😢', '#3498db'),
        ('Thriller', '🔍', '#e67e22'),
        ('Adventure', '🌍', '#2ecc71'),
    ]

    mood_cols = st.columns(len(MOODS), gap="small")
    selected_mood = st.session_state.get('chat_mood', 'All')

    for i, (mood, emoji, color) in enumerate(MOODS):
        with mood_cols[i]:
            is_active = selected_mood == mood
            active_css = (
                f'div.st-key-mood_filter_{i} button {{'
                f'background:{color}22 !important;'
                f'border:1.5px solid {color}66 !important;'
                f'color:#fff !important;'
                f'}}' if is_active and color else
                f'div.st-key-mood_filter_{i} button {{'
                f'background:rgba(255,255,255,0.06) !important;'
                f'border:1.5px solid rgba(255,255,255,0.15) !important;'
                f'color:#fff !important;'
                f'}}' if is_active else ''
            )
            if active_css:
                st.markdown(
                    f'<style>{active_css}</style>',
                    unsafe_allow_html=True,
                )
            if st.button(
                f'{emoji} {mood}',
                key=f'mood_filter_{i}',
                use_container_width=True,
            ):
                st.session_state['chat_mood'] = mood
                st.rerun()

    st.markdown(
        '<div style="height:16px"></div>',
        unsafe_allow_html=True,
    )

    # ── SUGGESTION CHIPS (shown only when chat empty) ──
    if not st.session_state.chat_history:

        st.markdown(
            '<div style="color:rgba(255,255,255,0.45);font-size:12.5px;'
            'margin:6px 0 12px 0">✨ Try asking me:</div>',
            unsafe_allow_html=True,
        )

        SUGGESTIONS = [
            {'t': '🎬 What is Inception about?', 'c': '#E50914'},
            {'t': '⭐ Is Oppenheimer worth watching?', 'c': '#f39c12'},
            {'t': '😂 Suggest funny movies for tonight', 'c': '#f7c948'},
            {'t': '💕 Best romantic movies', 'c': '#ff6b9d'},
            {'t': '🌍 Good Hindi movies to watch', 'c': '#2ecc71'},
            {'t': '🔚 Explain the ending of Interstellar', 'c': '#3498db'},
        ]

        sc = st.columns(3, gap="small")
        for i, s in enumerate(SUGGESTIONS):
            with sc[i % 3]:
                st.markdown(
                    f'<style>'
                    f'div.st-key-sug_{i} button{{'
                    f'background:rgba(229,9,20,0.08) !important;'
                    f'border:1px solid rgba(229,9,20,0.25) !important;'
                    f'color:#ffffff !important;'
                    f'border-radius:25px !important;'
                    f'font-size:13px !important;'
                    f'font-weight:600 !important;'
                    f'padding:10px 18px !important;'
                    f'text-align:center !important;'
                    f'min-height:46px !important;'
                    f'line-height:1.35 !important;'
                    f'transition:all 0.2s ease !important;'
                    f'}}'
                    f'div.st-key-sug_{i} button:hover{{'
                    f'background:rgba(229,9,20,0.16) !important;'
                    f'border-color:rgba(229,9,20,0.45) !important;'
                    f'color:#fff !important;'
                    f'transform:translateY(-2px) !important;'
                    f'box-shadow:0 6px 18px rgba(229,9,20,0.18) !important;'
                    f'}}'
                    f'</style>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    s['t'],
                    key=f'sug_{i}',
                    use_container_width=True,
                ):
                    st.session_state['last_user_message'] = s['t']
                    st.session_state.chat_history.append(
                        {'role': 'user', 'content': s['t']}
                    )
                    system_prompt = """You are MoodFlix AI.

MOST IMPORTANT RULE:
The LAST message in the conversation with role "user"
is what the user just typed RIGHT NOW.
Always answer ONLY that last user message.
Ignore all previous messages except for context.
Never repeat or re-answer any previous question.

You are MoodFlix AI, a smart movie expert
assistant like ChatGPT. You understand any question the user
types in any language and reply correctly and helpfully.

Always answer EXACTLY what was asked:

- "SAD MOVIES IN MARATHI" → List actual Marathi sad movies
  like Natsamrat, Sairat, Gosht Chhoti Dongraevadhi etc.

- "What is Inception about?" → Explain Inception plot clearly

- "is xyz worth watching" → Give honest yes/no review

- "suggest hindi comedy movies" → List Hindi comedy movies

- Any language question → Reply in that same language

NEVER show unrelated movies.
NEVER ignore what was asked.
NEVER give generic responses.
Always end with one helpful follow up question."""

                    headers = {
                        "Authorization": f"Bearer {YOUR_OPENROUTER_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8501",
                        "X-Title": "MoodFlix"
                    }

                    recent_history = st.session_state.chat_history[-6:]
                    messages_to_send = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in recent_history
                    ]
                    payload = {
                        "model": "openai/gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": system_prompt}
                        ] + messages_to_send,
                        "max_tokens": 1000
                    }

                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload
                    )

                    reply = response.json()["choices"][0]["message"]["content"]

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": reply
                    })

        st.markdown(
            '<div style="height:20px"></div>',
            unsafe_allow_html=True,
        )

    # ── CHAT HISTORY ──
    for msg in st.session_state.chat_history:
        role = msg['role']
        content = msg['content']

        if role == 'user':
            st.markdown(
                f'<div style="display:flex;align-items:flex-end;'
                f'justify-content:flex-end;gap:10px;margin:10px 0">'
                f'<div style="background:rgba(229,9,20,0.20);'
                f'border:1px solid rgba(229,9,20,0.40);'
                f'border-radius:18px 18px 4px 18px;'
                f'padding:12px 18px;color:#fff;font-size:13.5px;'
                f'font-weight:500;line-height:1.55;max-width:65%;'
                f'font-family:Poppins,sans-serif;word-wrap:break-word">'
                f'{html.escape(content)}</div>'
                f'<div style="width:34px;height:34px;border-radius:50%;'
                f'background:rgba(229,9,20,0.55);'
                f'border:1px solid rgba(229,9,20,0.5);'
                f'display:flex;align-items:center;'
                f'justify-content:center;font-size:14px;flex-shrink:0">'
                f'👤</div></div>',
                unsafe_allow_html=True,
            )

        else:
            ac, mc = st.columns([0.06, 0.94], gap="small")
            with ac:
                st.markdown(
                    '<div style="width:34px;height:34px;border-radius:50%;'
                    'background:linear-gradient(135deg,'
                    'rgba(26,188,156,0.3),rgba(52,152,219,0.2));'
                    'border:1.5px solid rgba(26,188,156,0.3);'
                    'display:flex;align-items:center;'
                    'justify-content:center;font-size:16px;'
                    'margin-top:4px">🤖</div>',
                    unsafe_allow_html=True,
                )
            with mc:
                st.markdown(
                    f'<div style="color:#E50914;font-size:11px;'
                    f'font-weight:700;letter-spacing:0.6px;'
                    f'margin:2px 0 6px 2px">MoodFlix AI</div>'
                    f'<div style="background:rgba(255,255,255,0.04);'
                    f'border:1px solid rgba(255,255,255,0.08);'
                    f'border-radius:18px 18px 18px 4px;'
                    f'padding:14px 18px;color:#e9edf2;'
                    f'font-size:13.5px;line-height:1.65;'
                    f'font-family:Poppins,sans-serif;margin-bottom:10px">'
                    f'{md_to_html(content)}</div>',
                    unsafe_allow_html=True,
                )

                # Mini movie poster cards
                movie_hits = extract_titles_from_response(content, df)
                if movie_hits:
                    st.markdown(
                        """
                        <style>
                        .cm-mini-card.cm-mini-card--ai {
                            border: 1px solid rgba(229,9,20,0.25);
                            transition: transform 0.2s ease, box-shadow 0.2s ease, border 0.2s ease;
                        }
                        .cm-mini-card.cm-mini-card--ai:hover {
                            border: 1px solid rgba(229,9,20,0.8);
                            box-shadow: 0 0 18px rgba(229,9,20,0.35);
                            transform: translateY(-3px);
                        }
                        .cm-mini-poster-wrap {
                            position: relative;
                            width: 100%;
                            height: 200px;
                            overflow: hidden;
                        }
                        .cm-mini-poster-wrap img {
                            width: 100%;
                            height: 200px;
                            object-fit: cover;
                            display: block;
                        }
                        .cm-mini-overlay {
                            position: absolute;
                            left: 0;
                            right: 0;
                            bottom: 0;
                            padding: 28px 10px 10px;
                            background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(5,6,10,0.88) 80%);
                        }
                        .cm-mini-overlay-title {
                            color: #fff;
                            font-size: 12px;
                            font-weight: 700;
                            line-height: 1.3;
                        }
                        .cm-mini-cta {
                            padding: 8px 10px 10px;
                            color: #ff6b6b;
                            font-size: 11px;
                            font-weight: 700;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                    card_cols = st.columns(
                        len(movie_hits), gap="small"
                    )
                    placeholder_svg = (
                        "data:image/svg+xml;utf8,"
                        "<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22600%22>"
                        "<rect width=%22100%25%22 height=%22100%25%22 fill=%22%230b0f1a%22/>"
                        "<text x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 "
                        "text-anchor=%22middle%22 font-size=%2264%22>🎬</text>"
                        "</svg>"
                    )
                    for ci, hit in enumerate(movie_hits):
                        with card_cols[ci]:
                            trailer = get_tmdb_trailer_url(
                                hit.get('movie_id', ''),
                                hit['title'],
                            )
                            poster = hit.get('poster', '')
                            poster_src = (
                                poster if poster and poster.startswith('http')
                                else placeholder_svg
                            )
                            st.markdown(
                                f'<a href="{trailer}" target="_blank" '
                                f'style="text-decoration:none">'
                                f'<div class="cm-mini-card cm-mini-card--ai">'
                                f'<div class="cm-mini-poster-wrap">'
                                f'<img src="{poster_src}" '
                                f'onerror="this.onerror=null;this.src=\'{placeholder_svg}\'">'
                                f'<div class="cm-mini-overlay">'
                                f'<div class="cm-mini-overlay-title">'
                                f'{html.escape(hit["title"])}</div></div></div>'
                                f'<div class="cm-mini-cta">'
                                f'▶ Watch Trailer</div>'
                                f'</div></a>',
                                unsafe_allow_html=True,
                            )

    # ── CLEAR BUTTON ──
    if st.session_state.chat_history:
        _, cc = st.columns([5, 1])
        with cc:
            if st.button('🗑️ Clear', key='clear_chat',
                         use_container_width=True):
                st.session_state.chat_history = []
                st.session_state['last_user_message'] = ''
                st.rerun()

    # ── CHAT INPUT ──
    st.markdown(
        '<div style="height:12px"></div>',
        unsafe_allow_html=True,
    )

    # Show active mood filter above input
    active_m = st.session_state.get('chat_mood', 'All')
    if active_m and active_m != 'All':
        mood_obj = next(
            (m for m in MOODS if m[0] == active_m), None
        )
        if mood_obj:
            st.markdown(
                f'<div class="cm-active-mood-pill">'
                f'{mood_obj[1]} Filtering: '
                f'<strong>{active_m}</strong> movies'
                f' &nbsp;·&nbsp; '
                f'<span style="opacity:0.6;font-size:10px">'
                f'Click "All" above to reset</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div style="margin:4px 0 10px 0;color:rgba(255,255,255,0.45);font-size:12.5px">'
        '💬 Ask me anything about any movie...'
        '</div>',
        unsafe_allow_html=True,
    )

    user_input = st.chat_input("Ask me anything about any movie...")

    if user_input:
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })

        system_prompt = """You are MoodFlix AI.

    MOST IMPORTANT RULE:
    The LAST message in the conversation with role "user"
    is what the user just typed RIGHT NOW.
    Always answer ONLY that last user message.
    Ignore all previous messages except for context.
    Never repeat or re-answer any previous question.

    You are MoodFlix AI, a smart movie expert
assistant like ChatGPT. You understand any question the user
types in any language and reply correctly and helpfully.

Always answer EXACTLY what was asked:

- "SAD MOVIES IN MARATHI" → List actual Marathi sad movies
  like Natsamrat, Sairat, Gosht Chhoti Dongraevadhi etc.

- "What is Inception about?" → Explain Inception plot clearly

- "is xyz worth watching" → Give honest yes/no review

- "suggest hindi comedy movies" → List Hindi comedy movies

- Any language question → Reply in that same language

NEVER show unrelated movies.
NEVER ignore what was asked.
NEVER give generic responses.
Always end with one helpful follow up question."""

        headers = {
            "Authorization": f"Bearer {YOUR_OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "MoodFlix"
        }

        recent_history = st.session_state.chat_history[-6:]
        messages_to_send = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in recent_history
        ]
        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt}
            ] + messages_to_send,
            "max_tokens": 1000
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        reply = response.json()["choices"][0]["message"]["content"]

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": reply
        })


def _get_spin_candidates(df_local, genre, min_score, avoid_watchlist, user_id):
    working = get_movies_by_genre(df_local, genre=genre, limit=None)
    if working.empty:
        return working

    working = working.copy()
    working['_score'] = working['movie_id'].apply(score_from_id)
    try:
        min_score_val = float(min_score)
    except (TypeError, ValueError):
        min_score_val = 0.0

    if min_score_val > 0:
        working = working[working['_score'] >= min_score_val]

    if avoid_watchlist and user_id:
        watchlist_titles = get_watchlist_titles(user_id)
        if watchlist_titles:
            working = working[
                ~working['title'].str.strip().str.lower().isin(watchlist_titles)
            ]

    return working.drop(columns=['_score'], errors='ignore').reset_index(drop=True)


def render_spin_wheel_page(df_local):
    """Render the Spin game page."""

    st.markdown(
        '<div class="cm-spin-shell">'
        '<div class="cm-spin-hero">'
        '<h2 class="cm-spin-title">Spin the <span style="color:#ff6b6b">Wheel</span></h2>'
        '<p class="cm-spin-sub">Can\'t decide what to watch? Let fate choose your perfect movie!</p>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if df_local is None or df_local.empty:
        st.info('No movies available to spin right now.')
        return

    user_id = st.session_state.get('user_id')

    wheel_labels = [
        ('Action', '🤩'), ('Horror', '😱'), ('Romance', '💕'),
        ('Comedy', '😂'), ('Sci-Fi', '🚀'), ('Thriller', '🔪'),
        ('Drama', '🎭'), ('Adventure', '🧭'), ('Animation', '🐣'),
        ('Biography', '💪')
    ]

    angle_per = 360 / len(wheel_labels)
    wheel_angle = float(st.session_state.get('spin_angle', 0.0))

    left_col, right_col = st.columns([1.3, 1], gap="large")

    lang_map = {
        "🌍 All": None,
        "🇬🇧 English": "en",
        "🇮🇳 Hindi": "hi",
        "🎭 Marathi": "mr",
    }
    badge_map = {"en": "🇬🇧 English", "hi": "🇮🇳 Hindi", "mr": "🎭 Marathi"}

    with left_col:
        label_html = ''
        for i, (label, icon) in enumerate(wheel_labels):
            angle = -90 + (i * angle_per)
            label_html += (
                f'<div class="cm-wheel-label" '
                f'style="transform:rotate({angle}deg) translate(0,-140px) rotate({-angle}deg);">'
                f'<span>{icon}</span><span>{label}</span>'
                f'</div>'
            )

        st.markdown(
            f'<div class="cm-wheel-wrap">'
            f'  <div class="cm-wheel-pointer"></div>'
            f'  <div class="cm-wheel" style="--spin-angle:{wheel_angle}deg">'
            f'    {label_html}'
            f'    <div class="cm-wheel-center">🎬</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <style>
            div[data-testid="stRadio"] label {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 999px;
                padding: 6px 14px;
                color: #bdbdbd;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.18s ease;
            }
            div[data-testid="stRadio"] label[data-selected="true"],
            div[data-testid="stRadio"] input:checked + div {
                background: rgba(229,9,20,0.18) !important;
                border-color: rgba(229,9,20,0.45) !important;
                color: #fff !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.radio(
            "🌐 Movie Language",
            ["🌍 All", "🇬🇧 English", "🇮🇳 Hindi", "🎭 Marathi"],
            horizontal=True,
            key='wheel_language',
        )

        spin_now = st.button('🎡 SPIN THE WHEEL!', key='spin_now', use_container_width=True)

    with right_col:
        st.markdown(
            '<div style="text-align:center">'
            '<div style="font-size:34px">🎯</div>'
            '<div class="cm-spin-right-title">Ready to be surprised?</div>'
            '<div class="cm-spin-right-sub">Hit SPIN to let fate choose<br>your perfect movie tonight!</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        chip_labels = ['Action', 'Horror', 'Romance', 'Comedy', 'Sci-Fi', 'Adventure']
        chip_cols = st.columns(3, gap="small")
        for i, label in enumerate(chip_labels):
            with chip_cols[i % 3]:
                if st.button(
                    label,
                    key=f'spin_chip_{label}',
                    use_container_width=True,
                ):
                    st.session_state['spin_genre'] = label

        selected_chip = st.session_state.get('spin_genre')
        if selected_chip in chip_labels:
            st.markdown(
                f'''<style>
                div.st-key-spin_chip_{selected_chip} button {{
                    background: rgba(229,9,20,0.18) !important;
                    border-color: rgba(229,9,20,0.45) !important;
                    color: #fff !important;
                    box-shadow: 0 6px 18px rgba(229,9,20,0.3) !important;
                }}
                </style>''',
                unsafe_allow_html=True,
            )

    selected_lang_label = st.session_state.get('wheel_language', '🌍 All')
    lang_code = lang_map.get(selected_lang_label)
    lang_badge = badge_map.get(lang_code, "🌍 All") if lang_code else "🌍 All"

    if spin_now:
        candidates = _get_spin_candidates(
            df_local,
            st.session_state.get('spin_genre', 'All'),
            st.session_state.get('spin_min_rating', 0),
            st.session_state.get('spin_avoid_watchlist', False),
            user_id,
        )

        if lang_code and not candidates.empty and 'language' in candidates.columns:
            candidates = candidates.copy()
            candidates['language'] = candidates['language'].fillna('').astype(str).str.lower()
            lang_df = candidates[candidates['language'] == lang_code]
            if not lang_df.empty:
                candidates = lang_df

        if candidates.empty:
            mood_name = st.session_state.get('spin_genre', 'All')
            st.markdown(
                f'<div style="text-align:center;padding:28px;'
                f'background:rgba(229,9,20,0.06);border:1px solid rgba(229,9,20,0.15);'
                f'border-radius:12px;color:#bdbdbd;font-size:13px">'
                f'😕 No <strong style="color:#fff">{html.escape(str(mood_name))}</strong> movies found in '
                f'<strong style="color:#fff">{lang_badge}</strong>.<br>'
                f'<span style="color:#E50914;font-size:12px">Try "🌍 All" or spin again!</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            pick = candidates.sample(n=1).iloc[0]
            st.session_state['spin_last_pick'] = {
                'title': pick.get('title'),
                'movie_id': pick.get('movie_id'),
                'poster_url': pick.get('poster_url'),
                'tags': pick.get('tags', ''),
            }
            history = st.session_state.get('spin_history', [])
            title = str(pick.get('title', '')).strip()
            if title:
                history = [t for t in history if t.lower() != title.lower()]
                history.insert(0, title)
                st.session_state['spin_history'] = history[:8]

            chosen_tags = str(pick.get('tags', '')).lower()
            picked_label = None
            for label, _ in wheel_labels:
                if label.lower().replace('-', '') in chosen_tags.replace('-', ''):
                    picked_label = label
                    break
            if not picked_label:
                picked_label = random.choice([label for label, _ in wheel_labels])

            picked_index = [i for i, (label, _) in enumerate(wheel_labels) if label == picked_label]
            picked_index = picked_index[0] if picked_index else 0
            target_offset = (360 - (picked_index * angle_per)) % 360
            st.session_state['spin_angle'] = wheel_angle + 720 + target_offset

    last_pick = st.session_state.get('spin_last_pick')
    if last_pick:
        st.markdown(
            '<div style="margin:16px 0 6px 0;color:#bdbdbd;font-size:12px">'
            'Your spin result</div>'
            f'<div style="display:inline-block;background:rgba(255,255,255,0.07);'
            f'border:1px solid rgba(255,255,255,0.12);border-radius:999px;'
            f'padding:3px 10px;font-size:11px;color:#bdbdbd;margin-top:4px">'
            f'{lang_badge}</div>',
            unsafe_allow_html=True,
        )
        last_df = pd.DataFrame([last_pick])
        st.markdown(render_carousel('', last_df), unsafe_allow_html=True)

        recs = recommend(last_pick.get('title'), df_local, topn=6)
        if recs:
            st.markdown(
                '<div style="margin:22px 0 6px 0;color:#bdbdbd;font-size:12px">'
                'If you like this, try these</div>',
                unsafe_allow_html=True,
            )
            rec_df = pd.DataFrame(recs)
            st.markdown(render_carousel('', rec_df), unsafe_allow_html=True)

    history = st.session_state.get('spin_history', [])
    if history:
        st.markdown(
            '<div style="margin-top:8px;color:#bdbdbd;font-size:12px">Recent spins</div>',
            unsafe_allow_html=True,
        )
        pills = ''.join([f'<span class="cm-spin-pill">{html.escape(h)}</span>' for h in history])
        st.markdown(f'<div class="cm-spin-history">{pills}</div>', unsafe_allow_html=True)


def render_movies_page(df_local):
    """Render the full Movies page with genre filters."""
    genres = [
        'All', 'Action', 'Adventure', 'Animation', 'Comedy',
        'Crime', 'Documentary', 'Drama', 'Fantasy', 'Horror',
        'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War'
    ]

    genre_param = str(get_query_param('genre', 'All')).strip()
    if genre_param:
        st.session_state['movies_genre_filter'] = genre_param

    st.markdown(
        '<div style="padding:32px 0 18px 0">'
        '<h2 style="color:#fff;font-size:32px;font-weight:900;margin:0 0 6px 0">'
        '🎬 All Movies</h2>'
        '<p style="color:#bdbdbd;font-size:14px;margin:0">'
        'Browse our full collection from the database</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if "movies_adv_enabled" not in st.session_state:
        st.session_state["movies_adv_enabled"] = False
    if "movies_adv_genres" not in st.session_state:
        st.session_state["movies_adv_genres"] = ["Horror", "Action", "Comedy"]
    if "movies_adv_years" not in st.session_state:
        st.session_state["movies_adv_years"] = (2020, 2024)
    if "movies_adv_page" not in st.session_state:
        st.session_state["movies_adv_page"] = 1

    st.session_state["movies_adv_enabled"] = st.toggle(
        "Advanced filters",
        value=st.session_state["movies_adv_enabled"],
        key="movies_adv_toggle",
    )

    if st.session_state["movies_adv_enabled"]:
        filter_cols = st.columns([2, 1, 2], gap="small")
        with filter_cols[0]:
            st.session_state["movies_adv_genres"] = st.multiselect(
                "Genres",
                ["Horror", "Action", "Comedy"],
                default=st.session_state["movies_adv_genres"],
                key="movies_adv_genre_select",
            )
        with filter_cols[1]:
            st.number_input(
                "Min rating",
                min_value=5.0,
                max_value=5.0,
                value=5.0,
                step=0.1,
                key="movies_adv_min_rating",
                disabled=True,
            )
        with filter_cols[2]:
            st.session_state["movies_adv_years"] = st.slider(
                "Year range",
                min_value=2020,
                max_value=2024,
                value=st.session_state["movies_adv_years"],
                step=1,
                key="movies_adv_year_range",
            )

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    selected_genre = st.session_state.get('movies_genre_filter', 'All')

    genre_pills_html = '<div class="cm-genre-pills">'
    for genre in genres:
        is_active = selected_genre == genre
        active_class = 'cm-genre-pill-active' if is_active else ''
        href = f'?view=movies&genre={quote_plus(genre)}'
        genre_pills_html += f'<a href="{href}" target="_self" class="cm-genre-pill {active_class}">{genre}</a>'
    genre_pills_html += '</div>'

    st.markdown(genre_pills_html, unsafe_allow_html=True)

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    selected_genre = st.session_state.get('movies_genre_filter', 'All')
    filtered = get_movies_by_genre(
        df_local,
        genre=None if selected_genre == 'All' else selected_genre,
        limit=200,
    )

    advanced_results = None
    if st.session_state.get("movies_adv_enabled"):
        advanced_results = advanced_search_movies(
            df_local,
            genres=st.session_state.get("movies_adv_genres") or ["Horror", "Action", "Comedy"],
            min_rating=5.0,
            year_range=st.session_state.get("movies_adv_years", (2020, 2024)),
            page=st.session_state.get("movies_adv_page", 1),
            per_page=10,
        )

    total = len(filtered)
    st.markdown(
        '<div style="color:#bdbdbd;font-size:13px;margin-bottom:16px">'
        f'Showing <strong style="color:#fff">{total}</strong> movies'
        + (f' in <strong style="color:#E50914">{selected_genre}</strong>' if selected_genre != 'All' else '')
        + '</div>',
        unsafe_allow_html=True,
    )

    if advanced_results is not None:
        adv_total = advanced_results.get("total_results", 0)
        adv_page = advanced_results.get("page", 1)
        adv_pages = advanced_results.get("total_pages", 0)
        st.markdown(
            '<div style="color:#bdbdbd;font-size:13px;margin:6px 0 12px 0">'
            f'Advanced results: <strong style="color:#fff">{adv_total}</strong> movies'
            '</div>',
            unsafe_allow_html=True,
        )

        nav_cols = st.columns([1, 2, 1], gap="small")
        with nav_cols[0]:
            if st.button("← Prev", disabled=adv_page <= 1, key="movies_adv_prev"):
                st.session_state["movies_adv_page"] = max(1, adv_page - 1)
                st.rerun()
        with nav_cols[1]:
            st.markdown(
                f'<div style="text-align:center;color:#bdbdbd;font-size:12px;padding-top:6px">'
                f'Page <strong style="color:#fff">{adv_page}</strong> of {adv_pages or 1}</div>',
                unsafe_allow_html=True,
            )
        with nav_cols[2]:
            if st.button("Next →", disabled=adv_page >= adv_pages, key="movies_adv_next"):
                st.session_state["movies_adv_page"] = min(adv_pages, adv_page + 1)
                st.rerun()

        adv_df = advanced_results.get("results", pd.DataFrame())
        if adv_df is None or adv_df.empty:
            st.info("No movies found for the advanced filters.")
        else:
            st.markdown(
                render_carousel("🎯 Advanced Picks", adv_df.reset_index(drop=True)),
                unsafe_allow_html=True,
            )
        return

    if "language" in df_local.columns:
        lang_df = df_local.copy()
        lang_df["language"] = lang_df["language"].fillna("").astype(str)
        hindi_df = lang_df[lang_df["language"].str.lower() == "hindi"].head(20)
        marathi_df = lang_df[lang_df["language"].str.lower() == "marathi"].head(20)

        if not hindi_df.empty or not marathi_df.empty:
            st.markdown(
                '<div style="margin:10px 0 8px 0;color:#bdbdbd;font-size:12px">'
                'Indian spotlight</div>',
                unsafe_allow_html=True,
            )
        if not hindi_df.empty:
            st.markdown(render_carousel('🇮🇳 Hindi Hits', hindi_df), unsafe_allow_html=True)
        if not marathi_df.empty:
            st.markdown(render_carousel('🇮🇳 Marathi Gems', marathi_df), unsafe_allow_html=True)

    if selected_genre == 'All':
        for genre in ['Action', 'Comedy', 'Drama', 'Thriller', 'Horror', 'Sci-Fi', 'Romance']:
            genre_df = get_movies_by_genre(df_local, genre=genre, limit=10)
            if not genre_df.empty:
                st.markdown(
                    render_carousel(f'🎬 {genre}', genre_df),
                    unsafe_allow_html=True,
                )
    else:
        if not filtered.empty:
            st.markdown(
                render_carousel(f'🎬 {selected_genre} Movies', filtered),
                unsafe_allow_html=True,
            )
        else:
            st.info(f'No movies found for genre: {selected_genre}')

# Load data
df = load_movies()


def get_lang_df(lang_code, n=30):
    if df is None or df.empty or 'language' not in df.columns:
        return pd.DataFrame()
    result = df[df['language'] == lang_code].reset_index(drop=True)
    return result if not result.empty else pd.DataFrame()

if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'home'
if 'auth_open' not in st.session_state:
    st.session_state['auth_open'] = False
if 'notifications' not in st.session_state:
    st.session_state['notifications'] = ['New trending movies available']
elif not st.session_state['notifications']:
    st.session_state['notifications'] = ['New trending movies available']
if 'last_processed_add_title' not in st.session_state:
    st.session_state['last_processed_add_title'] = ''
if 'pending_watchlist_title' not in st.session_state:
    st.session_state['pending_watchlist_title'] = ''
if 'selected_mood' not in st.session_state:
    st.session_state['selected_mood'] = None
if 'watchlist_updated' not in st.session_state:
    st.session_state['watchlist_updated'] = False
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'search_select' not in st.session_state:
    st.session_state['search_select'] = ''
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if '_pending_search' not in st.session_state:
    st.session_state['_pending_search'] = ''
if '_search_submit' not in st.session_state:
    st.session_state['_search_submit'] = False
if '_featured_movie' not in st.session_state:
    st.session_state['_featured_movie'] = ''
 # ══ NL SEARCH: HISTORY STATE START ══
if 'nl_search_history' not in st.session_state:
    st.session_state['nl_search_history'] = []
if 'nl_ai_disabled' not in st.session_state:
    st.session_state['nl_ai_disabled'] = False
# ══ NL SEARCH: HISTORY STATE END ══
if 'detail_movie' not in st.session_state:
    st.session_state['detail_movie'] = ''
if '_prev_view' not in st.session_state:
    st.session_state['_prev_view'] = 'home'
if 'spin_genre' not in st.session_state:
    st.session_state['spin_genre'] = 'All'
if 'spin_min_rating' not in st.session_state:
    st.session_state['spin_min_rating'] = 0.0
if 'spin_avoid_watchlist' not in st.session_state:
    st.session_state['spin_avoid_watchlist'] = False
if 'spin_last_pick' not in st.session_state:
    st.session_state['spin_last_pick'] = None
if 'spin_history' not in st.session_state:
    st.session_state['spin_history'] = []
if 'spin_angle' not in st.session_state:
    st.session_state['spin_angle'] = 0.0

# No URL-based view routing — all navigation via st.session_state only
_view_param  = str(get_query_param('view',  '')).strip()
_genre_param = str(get_query_param('genre', '')).strip()
if _genre_param:
    st.session_state['movies_genre_filter'] = _genre_param
    st.session_state['show_movies_inline']  = True
    st.session_state['show_popular_inline'] = False
    st.session_state['show_ai_inline']      = False
    try:
        if 'genre' in st.query_params:
            del st.query_params['genre']
        if 'view' in st.query_params:
            del st.query_params['view']
    except Exception:
        pass

current_user = sync_current_user()
current_view = st.session_state.get('current_view', 'home')
current_username = current_user.get('username') if current_user else st.session_state.get('username')
auth_status_text = '✅ Currently Signed In: ' + str(current_username) if current_username else 'Not Signed In'
unread_count = len(st.session_state.get('notifications', []))
unread_count = min(max(unread_count, 0), 6)
unread_opacity = 1 if unread_count > 0 else 0
st.markdown(
    f"<style>:root{{--cm-unread-count:'{unread_count}';--cm-unread-opacity:{unread_opacity};}}</style>",
    unsafe_allow_html=True,
)

def clear_login_state():
    for key in ['user_id', 'username', '_auth_user_id', '_auth_username']:
        if key in st.session_state:
            del st.session_state[key]

def set_view(view_name):
    st.session_state['current_view'] = view_name

def open_auth_panel():
    st.session_state['auth_open'] = True

def close_auth_panel():
    st.session_state['auth_open'] = False


def mark_search_submit():
    st.session_state['_search_submit'] = True

# ══ NL SEARCH: QUERY PARAM HANDLING START ══
# Autocomplete/History selection handler (must run before any widget renders)
_search_select = str(get_query_param('search_select', '')).strip()
_search_q = str(get_query_param('q', '')).strip()
_pending_query = _search_select or _search_q
if _pending_query:
    # Store in a staging key to avoid setting widget state post-render
    st.session_state['_pending_search'] = _pending_query
    st.session_state['current_view'] = 'home'
    try:
        if 'search_select' in st.query_params:
            del st.query_params['search_select']
        if 'q' in st.query_params:
            del st.query_params['q']
    except Exception:
        pass
    st.rerun()
# ══ NL SEARCH: QUERY PARAM HANDLING END ══

# Handle featured movie selection from autocomplete click
_featured = str(get_query_param('featured', '')).strip()
if _featured:
    st.session_state['_featured_movie'] = _featured
    try:
        if 'featured' in st.query_params:
            del st.query_params['featured']
    except Exception:
        pass

_detail = str(get_query_param('detail', '')).strip()
if _detail:
    st.session_state['detail_movie'] = _detail
    st.session_state['_prev_view'] = st.session_state.get('current_view', 'home')
    st.session_state['current_view'] = 'movie_detail'
    try:
        if 'detail' in st.query_params:
            del st.query_params['detail']
    except Exception:
        pass
    st.rerun()

params = st.query_params
if "selected_movie" in params:
    selected = params["selected_movie"]
    if isinstance(selected, list):
        selected = selected[0] if selected else ""
    if selected:
        st.session_state['detail_movie'] = selected
        st.session_state['_prev_view'] = st.session_state.get('current_view', 'home')
        st.session_state['current_view'] = 'movie_detail'
    st.query_params.clear()
    st.rerun()

# Premium Navbar
current_view = st.session_state.get('current_view', 'home')
current_username = st.session_state.get('username', '')
user_initials = current_username[0].upper() if current_username else '👤'
notif_count = len([n for n in st.session_state.get('notifications', []) if n])
notif_dot = '<span style="position:absolute;top:3px;right:3px;width:8px;height:8px;border-radius:50%;background:#E50914;border:1.5px solid #05060a;font-size:0"></span>' if notif_count > 0 else ''

home_active   = 'background:linear-gradient(90deg,rgba(229,9,20,0.2),rgba(255,95,109,0.12));border-color:rgba(229,9,20,0.3);color:#fff;' if current_view=='home'        else ''
movie_active  = 'background:linear-gradient(90deg,rgba(229,9,20,0.2),rgba(255,95,109,0.12));border-color:rgba(229,9,20,0.3);color:#fff;' if current_view=='movies'      else ''
pop_active    = 'background:linear-gradient(90deg,rgba(229,9,20,0.2),rgba(255,95,109,0.12));border-color:rgba(229,9,20,0.3);color:#fff;' if current_view=='new_popular'  else ''
spin_active   = 'border-color:rgba(247,201,72,0.5);color:#fff;'                                                                          if current_view=='spin_wheel'  else ''
ai_active     = 'border-color:rgba(26,188,156,0.5);color:#fff;'                                                                          if current_view=='ai_chat'     else ''

new_df = df

titles_json = json.dumps(
    df['title'].dropna().astype(str).tolist()[:800]
)

st.markdown(f"""
<style>
#cm-nb{{
    position:sticky;top:0;left:0;right:0;z-index:99999;
    height:62px;
    background:rgba(9,12,20,0.97);
    backdrop-filter:blur(16px);
    border-bottom:1px solid rgba(255,255,255,0.07);
    display:flex;align-items:center;
    padding:0 28px;
    gap:18px;
    box-sizing:border-box;
    width:100%;
    font-family:'Poppins',sans-serif;
    position:relative;
    overflow:visible;
}}
#cm-nb::after{{
    content:'';
    position:absolute;
    left:0;right:0;bottom:0;height:1px;
    background:linear-gradient(90deg,transparent,rgba(229,9,20,0.4),transparent);
    pointer-events:none;
}}
#cm-nb *{{box-sizing:border-box;}}
.nb-logo{{
    font-size:22px;font-weight:900;font-family:Georgia,serif;
    flex-shrink:0;cursor:pointer;text-decoration:none;
    display:flex;align-items:center;line-height:1;
    white-space:nowrap;
}}
.nb-logo b{{
    color:#E50914;
    font-style:normal;
    position:relative;
}}
.nb-logo b::after{{
    content:'';
    position:absolute;
    left:0; bottom:-3px;
    width:40%; height:2px;
    border-radius:2px;
    background:linear-gradient(90deg,#E50914,#ff6b35);
}}
.nb-logo span{{color:#fff}}
.nb-nav{{display:flex;align-items:center;gap:2px;flex-shrink:0}}
.nb-btn{{
    display:inline-flex;align-items:center;gap:5px;
    padding:7px 13px;border-radius:999px;
    font-size:12.5px;font-weight:600;
    color:#bdbdbd;cursor:pointer;
    white-space:nowrap;text-decoration:none;
    border:1px solid transparent;
    transition:all 0.18s;
    font-family:'Poppins',sans-serif;
    line-height:1;
    text-decoration:none;
}}
.nb-btn:hover{{
    background:rgba(255,255,255,0.07) !important;
    color:#fff !important;
    transform:translateY(-1px);
}}
.nb-btn, .nb-btn:hover, .nb-btn:visited, .nb-btn:active,
.nb-logo, .nb-logo:hover, .nb-logo:visited,
.nb-icon, .nb-icon:hover, .nb-icon:visited,
#cm-nb a, #cm-nb a:hover, #cm-nb a:visited, #cm-nb a:active {{
    text-decoration: none !important;
    -webkit-text-decoration: none !important;
}}
.nb-spin{{
    background:rgba(247,201,72,0.10);
    border:1px solid rgba(247,201,72,0.22);
    color:#f7c948;
}}
.nb-ai{{
    background:rgba(26,188,156,0.12);
    border:1px solid rgba(26,188,156,0.28);
    color:#1abc9c;
}}
.nb-search{{
    flex:1;min-width:0;
    position:relative;
    display:flex;align-items:center;
    height:38px;
}}
.nb-search-icon{{
    position:absolute;left:13px;top:50%;
    transform:translateY(-50%);
    color:rgba(255,255,255,0.35);
    font-size:14px;pointer-events:none;line-height:1;
    z-index:1;
}}
.nb-search input{{
    width:100%;height:38px;
    background:rgba(255,255,255,0.05) !important;
    border:1px solid rgba(255,255,255,0.09) !important;
    border-radius:999px;
    color:#eef0f3 !important;
    font-size:12.5px;
    font-family:'Poppins',sans-serif;
    padding:0 16px 0 38px;
    outline:none;
    -webkit-appearance:none;
    appearance:none;
    line-height:38px;
    caret-color:#E50914;
    display:block;
}}
.nb-search input::placeholder{{color:rgba(255,255,255,0.28);font-size:12px}}
.nb-search input:focus{{
    border-color:rgba(229,9,20,0.5) !important;
    background:rgba(255,255,255,0.09) !important;
    box-shadow:0 0 0 3px rgba(229,9,20,0.10);
}}
.nb-actions{{
    display:flex;align-items:center;
    gap:10px;flex-shrink:0;
}}
.nb-sep{{
    width:1px;height:26px;
    background:rgba(255,255,255,0.08);
    flex-shrink:0;
}}
.nb-icon{{
    width:38px;height:38px;
    border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    cursor:pointer;flex-shrink:0;
    font-size:17px;line-height:1;
    text-decoration:none;position:relative;
    transition:all 0.18s;
}}
.nb-bell{{
    background:rgba(255,255,255,0.05);
    border:1px solid rgba(255,255,255,0.10);
    color:#fff;
}}
.nb-bell:hover{{background:rgba(255,255,255,0.10)}}
.nb-avatar{{
    background:linear-gradient(135deg,rgba(229,9,20,0.3),rgba(255,95,109,0.2));
    border:2px solid rgba(229,9,20,0.5);
    color:#fff;font-size:15px;font-weight:800;
}}
.nb-avatar:hover{{border-color:#E50914;transform:scale(1.05)}}
</style>

<div id="cm-nb">
<a class="nb-logo" href="?view=home" target="_self" style="cursor:pointer" onclick="setView('home')">
<span style="color:#eef0f3;font-weight:900;font-size:32px;font-family:Poppins,sans-serif;letter-spacing:-1px;line-height:1">Mood</span>
<span style="background:linear-gradient(135deg,#E50914,#ff6b6b);-webkit-background-clip:text;background-clip:text;color:transparent;font-weight:900;font-size:32px;font-family:Poppins,sans-serif;letter-spacing:-1px;line-height:1">Flix</span>
</a>

<nav class="nb-nav">
<a class="nb-btn" href="?view=home" target="_self" style="{home_active};cursor:pointer" onclick="setView('home')">🏠 Home</a>
<a class="nb-btn" href="?view=movies" target="_self" style="{movie_active};cursor:pointer" onclick="setView('movies')">🎬 Movies</a>
<a class="nb-btn" href="?view=new_popular" target="_self" style="{pop_active};cursor:pointer" onclick="setView('new_popular')">🔥 Popular</a>
<a class="nb-btn nb-spin" href="?view=spin_wheel" target="_self" style="{spin_active};cursor:pointer" onclick="setView('spin_wheel')">🎰 Spin</a>
<a class="nb-btn nb-ai" href="?view=ai_chat" target="_self" style="{ai_active};cursor:pointer" onclick="setView('ai_chat')">🤖 AI</a>
</nav>

<div style="position:relative;display:flex;align-items:center;">
    <input 
        type="text" 
        id="moodflix-search"
        placeholder='🔍  Try: "sad movie jisme ladki..."'
        oninput="handleSearch(this.value)"
        style="
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 20px;
            padding: 7px 18px;
            font-size: 12px;
            color: white;
            width: 220px;
            outline: none;
        "
    />
    <button
        type="button"
        onclick="commitSearch(document.getElementById('moodflix-search').value)"
        style="
            margin-left: 10px;
            height: 34px;
            padding: 0 14px;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.06);
            color: #eef0f3;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            outline: none;
        "
    >Search</button>
    
</div>

<div class="nb-actions">
<div class="nb-sep"></div>
<a class="nb-icon nb-bell" href="?view=notifications" target="_self" style="cursor:pointer" onclick="setView('notifications')" title="Notifications">
🔔{notif_dot}
</a>
<a class="nb-icon nb-avatar" href="?view=profile" target="_self" style="cursor:pointer" onclick="setView('profile')" title="Profile">
{user_initials}
</a>
</div>

<script>
var movieTitles = {titles_json};

function setView(view) {{
        var url = new URL(window.parent.location.href);
        url.searchParams.set('view', view);
        window.parent.location.href = url.toString();
}}

function commitSearch(value) {{
    var q = (value || '').trim();
    var url = new URL(window.parent.location.href);
    if (q) {{
        url.searchParams.set('q', q);
    }} else {{
        url.searchParams.delete('q');
    }}
    url.searchParams.set('view', 'home');
    window.parent.location.href = url.toString();
}}

function handleSearch(query) {{
    var box = document.getElementById('search-dropdown');
    if (!box) {{
        box = document.createElement('div');
        box.id = 'search-dropdown';
        box.style.cssText = 'position:absolute;top:44px;left:0;background:#111118;border:1px solid rgba(229,9,20,0.4);border-radius:12px;padding:6px;z-index:999999;width:320px;max-height:360px;overflow-y:auto;box-shadow:0 12px 40px rgba(0,0,0,0.8);';
        var inp = document.getElementById('moodflix-search');
        if (inp) inp.parentNode.appendChild(box);
    }}
    if (!query || query.length < 2) {{
        box.style.display = 'none';
        return;
    }}
    var q = query.toLowerCase();
    var matches = movieTitles.filter(function(t) {{
        return t.toLowerCase().indexOf(q) !== -1;
    }}).slice(0, 8);
    if (matches.length === 0) {{
        box.innerHTML = '<div style="padding:14px;text-align:center;color:rgba(255,255,255,0.4);font-size:13px;">😕 No results for <b style="color:white">' + query + '</b></div>';
        box.style.display = 'block';
        return;
    }}
    box.innerHTML = matches.map(function(title) {{
        var idx = title.toLowerCase().indexOf(q);
        var hl = title.slice(0,idx) +
            '<span style="color:#E50914;font-weight:800">' +
            title.slice(idx, idx+query.length) +
            '</span>' + title.slice(idx+query.length);
        return '<div onclick="selectMovie(\'' +
            title.replace(/\\/g,'\\\\').replace(/'/g,"\\'") +
            '\')" style="padding:10px 14px;border-radius:8px;cursor:pointer;' +
            'color:white;font-size:13px;" ' +
            'onmouseover="this.style.background=\'rgba(229,9,20,0.15)\'" ' +
            'onmouseout="this.style.background=\'transparent\'">🎬 ' + hl + '</div>';
    }}).join('');
    box.style.display = 'block';
}}

function selectMovie(title) {{
    var box = document.getElementById('search-dropdown');
    if (box) box.style.display = 'none';
    window.location.href = window.location.pathname +
        '?selected_movie=' + encodeURIComponent(title);
}}

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {{
    var box = document.getElementById('search-dropdown');
    var inp = document.getElementById('moodflix-search');
    if (box && inp && !box.contains(e.target) && e.target !== inp) {{
        box.style.display = 'none';
    }}
}});

var searchInput = document.getElementById('moodflix-search');
if (searchInput) {{
    searchInput.addEventListener('keydown', function(e) {{
        if (e.key === 'Enter') {{
            e.preventDefault();
            commitSearch(this.value);
        }}
    }});

    var q = new URL(window.parent.location.href).searchParams.get('q');
    if (q && searchInput && !searchInput.value) {{ searchInput.value = q; }}
}}
</script>

</div>
""", unsafe_allow_html=True)

_np = str(st.query_params.get('view', '')).strip()
if _np in ['home','movies','new_popular','spin_wheel','ai_chat','profile','my_list','notifications']:
    st.session_state['current_view'] = _np if _np != 'notifications' else 'home'
    try:
        del st.query_params['view']
    except:
        pass
    st.rerun()

_sq = str(st.query_params.get('q', '')).strip()
if _sq:
    st.session_state['_pending_search'] = _sq
    st.session_state['current_view'] = 'home'
    try:
        del st.query_params['q']
    except:
        pass
    st.rerun()

# Process add-to-watchlist actions from query params
add_title = str(get_query_param('add_title', '')).strip()
if add_title and st.session_state.get('last_processed_add_title') != add_title:
    user_id = st.session_state.get('user_id')

    if not user_id:
        saved_username = st.session_state.get('username', '')
        if saved_username:
            recovered = db.get_user_by_username(saved_username)
            if recovered:
                user_id = recovered.get('id')
                st.session_state['user_id'] = user_id

    if not user_id:
        st.session_state['pending_watchlist_title'] = add_title
        push_notification('Please sign in first')
        st.toast('⚠️ Please sign in first')
    else:
        result = process_watchlist_add(add_title, user_id)
        if result.get('message'):
            push_notification(result['message'])
            st.toast(('✅ ' if result.get('success') else '⚠️ ') + result['message'])

        if result.get('success'):
            try:
                get_watchlist_titles.clear()
            except Exception:
                pass
            st.session_state['watchlist_updated'] = True

    st.session_state['last_processed_add_title'] = add_title
    try:
        if 'add_title' in st.query_params:
            del st.query_params['add_title']
    except Exception:
        pass
elif not add_title:
    st.session_state['last_processed_add_title'] = ''

# Handle heart param — same logic as add_title but triggered by heart click
heart_param = str(get_query_param('heart', '')).strip()
heart_title = str(get_query_param('add_title', '')).strip()

if heart_param == '1' and heart_title:
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.session_state['pending_watchlist_title'] = heart_title
        push_notification('Please sign in to save favourites')
        st.toast('⚠️ Please sign in to save favourites')
    else:
        result = process_watchlist_add(heart_title, user_id)
        if result.get('success'):
            push_notification(f"❤️ {heart_title} added to favourites")
            st.toast('❤️ Added to favourites!')
        else:
            push_notification(result.get('message', 'Already in favourites'))
            st.toast('⚠️ ' + result.get('message', 'Already in favourites'))

    try:
        if 'heart' in st.query_params:
            del st.query_params['heart']
    except Exception:
        pass

current_view = st.session_state.get('current_view', 'home')

if current_view == 'my_list':
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.info('Please sign in to view your watchlist')
    else:
        watchlist_rows = db.get_watchlist(int(user_id))
        if watchlist_rows:
            watchlist_df = pd.DataFrame(watchlist_rows)
            st.markdown(render_carousel('❤️ My List', watchlist_df.reset_index(drop=True)), unsafe_allow_html=True)
        else:
            st.info('Your watchlist is empty. Start adding movies!')
elif current_view == 'movies':
    render_movies_page(df)
elif current_view == 'new_popular':
    render_new_popular_page(df)
elif current_view == 'spin_wheel':
    render_spin_wheel_page(df)
elif current_view == 'ai_chat':
    render_chatbot_page(df)
elif current_view == 'profile':
    render_profile_page(df)
elif current_view == 'movie_detail':
    render_movie_detail_page(df)
else:
    # Hero section
    if len(df) > 0:
        _feat_title = st.session_state.get('_featured_movie', '')
        if _feat_title:
            feat_row = df[df['title'].str.strip().str.lower() == _feat_title.strip().lower()]
            featured = feat_row.iloc[0] if not feat_row.empty else df.iloc[0]
        else:
            featured = df.iloc[0]
        featured_title = featured.get('title', 'Featured')
        featured_back = featured.get('poster_url') or get_movie_poster_url(featured.get('movie_id', ''), featured_title) or ''
        featured_back = str(featured_back) if featured_back and str(featured_back) != 'nan' else ''

        hero_add_href = '?add_title=' + quote_plus(featured_title)

        hero_html = '<div class="cm-hero">'
        if featured_back:
            hero_html += '<div class="backdrop" style="background-image:url(\'' + featured_back + '\');"></div>'
        hero_html += '<img class="hero-poster" src="' + (featured_back or '') + '" alt="' + featured_title + '" onerror="this.style.display=\'none\'">'
        hero_html += '<div class="overlay"></div>'
        hero_html += '<div class="hero-content">'
        is_user_selected = bool(st.session_state.get('_featured_movie', ''))
        if is_user_selected:
            hero_html += (
                '<div class="cm-hero-selected-badge">'
                '🔍 Selected from search'
                '</div>'
            )
        hero_html += '<h1>' + featured_title + '</h1>'
        hero_html += '<p class="tag">A cinematic AI-curated recommendation just for you.</p>'
        hero_trailer_url = get_tmdb_trailer_url(
            str(featured.get('movie_id', '')), featured_title
        )
        hero_html += '<div class="hero-cta">'
        hero_html += (
            f'<a class="btn-play" href="{hero_trailer_url}" '
            f'target="_blank" rel="noopener noreferrer">'
            f'▶ Watch Trailer</a>'
        )
        hero_html += '<a class="btn-list" href="' + hero_add_href + '" target="_self">+ My List</a>'
        hero_html += '</div></div></div>'
        st.markdown(hero_html, unsafe_allow_html=True)

    # Search results render after the hero banner
    search_query = str(st.session_state.pop('_pending_search', '')).strip()

    if search_query:
        st.session_state['search_query'] = search_query
        search_results_df, match_type = search_movies(search_query, df)
        render_search_results(search_query, search_results_df, match_type)
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    render_mood_section(df)
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    render_because_you_watched(df)
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    selected_lang = str(get_query_param('lang', 'all')).strip().lower()
    if selected_lang not in {'all', 'en', 'hi', 'mr'}:
        selected_lang = 'all'
    st.session_state['home_lang'] = selected_lang

    def _render_lang_tab(label, lang, color):
        is_active = st.session_state.get('home_lang', 'all') == lang
        bg = color if is_active else 'transparent'
        fg = '#fff' if is_active else 'rgba(255,255,255,0.65)'
        border = f'1px solid {color}' if is_active else '1px solid rgba(255,255,255,0.12)'
        return (
            f'<a href="?lang={lang}" target="_self" style="text-decoration:none">'
            f'<div style="padding:8px 22px;border-radius:50px;'
            f'background:{bg};color:{fg};font-size:13px;font-weight:700;'
            f'cursor:pointer;border:{border}">{label}</div>'
            f'</a>'
        )

    st.markdown(
        f"""
        <div style="
            position:sticky;
            top:72px;
            z-index:6;
            display:flex;
            gap:10px;
            margin: 16px 0 24px 0;
            padding: 6px;
            background:rgba(255,255,255,0.04);
            border-radius:50px;
            width:fit-content;
            backdrop-filter:blur(6px);
        ">
            {_render_lang_tab("🌐 All", "all", "#E50914")}
            {_render_lang_tab("🌍 English", "en", "#E50914")}
            {_render_lang_tab("🇮🇳 Hindi", "hi", "#FF9933")}
            {_render_lang_tab("🟠 Marathi", "mr", "#138808")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    en_df = get_lang_df('en')
    hi_df = get_lang_df('hi')
    mr_df = get_lang_df('mr')

    def render_language_section_header(flag, label, color, count):
        st.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                gap:14px;
                margin: 32px 0 4px 0;
                padding: 18px 28px;
                background: linear-gradient(135deg, {color}18, transparent);
                border-left: 4px solid {color};
                border-radius: 0 12px 12px 0;
            ">
                <span style="font-size:36px">{flag}</span>
                <div>
                    <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:0.5px">{label}</div>
                    <div style="font-size:13px;color:rgba(255,255,255,0.45);margin-top:2px">{count} movies available</div>
                </div>
                <div style="
                    margin-left:auto;
                    background:{color}22;
                    border:1px solid {color}55;
                    color:{color};
                    font-size:11px;
                    font-weight:700;
                    padding:4px 14px;
                    border-radius:20px;
                    letter-spacing:1px;
                ">EXPLORE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    show_all = st.session_state.get('home_lang', 'all') == 'all'

    if (show_all or st.session_state['home_lang'] == 'en') and not en_df.empty:
        render_language_section_header("🌍", "Hollywood & English Cinema", "#E50914", len(en_df))

        trending_en = en_df.sample(n=min(len(en_df), 12), random_state=2).reset_index(drop=True)
        st.markdown(render_carousel("🔥 Trending Now", trending_en), unsafe_allow_html=True)
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        toprated_en = en_df.sample(n=min(len(en_df), 12), random_state=7).reset_index(drop=True)
        st.markdown(render_carousel("⭐ Top Rated English", toprated_en), unsafe_allow_html=True)
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        recommended_en = en_df.sample(n=min(len(en_df), 12), random_state=11).reset_index(drop=True)
        st.markdown(render_carousel("🎬 Recommended For You", recommended_en), unsafe_allow_html=True)

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    if (show_all or st.session_state['home_lang'] == 'hi') and not hi_df.empty:
        render_language_section_header("🇮🇳", "Bollywood & Hindi Cinema", "#FF9933", len(hi_df))

        trending_hi = hi_df.sample(n=min(len(hi_df), 12), random_state=3).reset_index(drop=True)
        st.markdown(render_carousel("🎵 Trending Bollywood", trending_hi), unsafe_allow_html=True)
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        popular_hi = hi_df.sample(n=min(len(hi_df), 12), random_state=8).reset_index(drop=True)
        st.markdown(render_carousel("🏆 Most Popular Hindi", popular_hi), unsafe_allow_html=True)
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        classic_hi = hi_df.sample(n=min(len(hi_df), 12), random_state=13).reset_index(drop=True)
        st.markdown(render_carousel("💫 Hindi Must Watch", classic_hi), unsafe_allow_html=True)

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    if (show_all or st.session_state['home_lang'] == 'mr') and not mr_df.empty:
        render_language_section_header("🟠", "Marathi Cinema", "#138808", len(mr_df))

        trending_mr = mr_df.sample(n=min(len(mr_df), 12), random_state=4).reset_index(drop=True)
        st.markdown(render_carousel("🎭 Trending Marathi", trending_mr), unsafe_allow_html=True)
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        popular_mr = mr_df.sample(n=min(len(mr_df), 12), random_state=9).reset_index(drop=True)
        st.markdown(render_carousel("🌟 Popular Marathi Films", popular_mr), unsafe_allow_html=True)

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
