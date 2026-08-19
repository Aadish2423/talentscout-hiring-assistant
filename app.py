"""
TalentScout Hiring Assistant
AI-powered interactive chatbot for candidate screening
"""
import streamlit as st
import os
import json
import re
import time
from datetime import datetime
from uuid import uuid4
from groq import Groq
from dotenv import load_dotenv
import streamlit.components.v1 as components
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
MODEL_TOOL_LABEL = f"{MODEL_NAME} (Groq API)"
MAX_API_RETRIES = 2
API_RETRY_DELAY_SECONDS = 1.5
CANDIDATES_LOG_FILE = "candidates_log.json"
AUDIT_LOG_FILE = "audit_log.json"
REVIEW_PENDING = "Pending Human Review"
REVIEW_APPROVED = "Approved"
REVIEW_REJECTED = "Rejected"
REVIEWER_TOOL_LABEL = "Human Reviewer (Reviewer Panel)"

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="TalentScout · Hiring Assistant",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# Custom CSS — dark editorial aesthetic (enhanced)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg:       #0d0f11;
    --surface:  #141719;
    --border:   #232628;
    --accent:   #c8f060;
    --accent2:  #60c8f0;
    --muted:    #5a6370;
    --text:     #e8eaed;
    --user-bg:  #1a2a0f;
    --bot-bg:   #141719;
    --danger:   #f06060;
    --success:  #60f0a0;
    --warn:     #f0c860;
    --ease-smooth: cubic-bezier(0.25, 0.46, 0.45, 0.94);
    --ease-out-soft: cubic-bezier(0.22, 0.61, 0.36, 1);
    --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* ── global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text);
    scroll-behavior: smooth;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

* { transition-timing-function: var(--ease-smooth); }

.stApp {
    background-color: var(--bg) !important;
    transition: none;
}

/* ── hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 2rem 1.5rem 4rem !important;
    max-width: 820px !important;
    transition: none;
}

/* ── header ── */
.ts-header {
    display: flex; align-items: center; gap: 1rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem; margin-bottom: 0.5rem;
    animation: headerSlide 0.6s var(--ease-out-soft);
}
@keyframes headerSlide {
    from { opacity: 0; transform: translateY(-12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.ts-logo {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem; color: var(--accent);
    letter-spacing: -0.02em; line-height: 1;
}
.ts-tagline {
    font-size: 0.75rem; color: var(--muted);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.12em; text-transform: uppercase;
}
.ts-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent); margin-left: auto;
    box-shadow: 0 0 8px var(--accent);
    animation: pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 8px var(--accent); }
    50%      { opacity: 0.5; transform: scale(0.85); box-shadow: 0 0 16px var(--accent); }
}

/* ── privacy bar ── */
.ts-privacy {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.5rem 0.75rem; margin-bottom: 0.75rem;
    font-size: 0.7rem; color: var(--muted);
    font-family: 'DM Mono', monospace;
    border: 1px solid #1a1d20; border-radius: 6px;
    background: #0f1114;
    transition: border-color 0.4s, background 0.4s;
}
.ts-privacy:hover {
    border-color: #252830;
    background: #101316;
}

/* ── phase banner ── */
.ts-phase-banner {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.6rem 1rem; margin-bottom: 1rem;
    border-radius: 8px; border: 1px solid var(--border);
    background: linear-gradient(135deg, #111315, #181b1f);
    animation: fadeUp 0.5s var(--ease-out-soft);
    transition: border-color 0.3s, box-shadow 0.3s;
}
.ts-phase-banner:hover {
    border-color: #2a3040;
    box-shadow: 0 2px 16px rgba(0,0,0,0.2);
}
.ts-phase-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--accent2);
}
.ts-phase-detail {
    font-size: 0.72rem; color: var(--muted);
    font-family: 'DM Mono', monospace;
}

/* ── progress bar ── */
.ts-progress {
    display: flex; gap: 4px; margin-bottom: 1.5rem;
}
.ts-step {
    height: 3px; flex: 1; border-radius: 2px;
    background: var(--border);
    transition: all 0.8s var(--ease-out-soft);
}
.ts-step.done {
    background: var(--accent);
    box-shadow: 0 0 6px rgba(200,240,96,0.3);
}
.ts-step.active {
    background: var(--accent2);
    box-shadow: 0 0 8px rgba(96,200,240,0.4);
    animation: stepPulse 2s ease-in-out infinite;
}
@keyframes stepPulse {
    0%, 100% { box-shadow: 0 0 8px rgba(96,200,240,0.4); }
    50%      { box-shadow: 0 0 14px rgba(96,200,240,0.6); }
}
.ts-step-labels {
    display: flex; justify-content: space-between;
    margin-top: 4px; margin-bottom: 1.5rem;
}
.ts-step-label {
    font-size: 0.6rem; color: var(--muted);
    font-family: 'DM Mono', monospace;
    text-transform: uppercase; letter-spacing: 0.05em;
    transition: color 0.5s var(--ease-out-soft);
}
.ts-step-label.active { color: var(--accent2); }
.ts-step-label.done { color: var(--accent); }

/* ── chat messages ── */
.ts-message {
    display: flex; gap: 12px;
    margin-bottom: 1.25rem;
    animation: messageIn 0.5s var(--ease-out-soft) backwards;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes messageIn {
    from { opacity: 0; transform: translateY(14px) scale(0.98); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
.ts-avatar {
    width: 32px; height: 32px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; flex-shrink: 0; margin-top: 2px;
    font-family: 'DM Mono', monospace;
    transition: transform 0.3s var(--ease-spring), box-shadow 0.3s;
}
.ts-avatar:hover {
    transform: scale(1.12);
    box-shadow: 0 0 14px rgba(200,240,96,0.2);
}
.ts-avatar.bot  { background: var(--border); color: var(--accent); }
.ts-avatar.user { background: var(--user-bg); color: var(--accent); }
.ts-bubble {
    background: var(--bot-bg);
    border: 1px solid var(--border);
    border-radius: 2px 12px 12px 12px;
    padding: 0.85rem 1rem;
    font-size: 0.92rem; line-height: 1.7;
    max-width: 100%;
    transition: border-color 0.35s, box-shadow 0.35s, transform 0.25s;
}
.ts-bubble:hover {
    border-color: #2a2d30;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    transform: translateY(-1px);
}
.ts-bubble.user-bubble {
    background: var(--user-bg);
    border-color: #2a4020;
    border-radius: 12px 2px 12px 12px;
    color: #d4efb4;
}
.ts-bubble.user-bubble:hover {
    border-color: #3a5030;
    box-shadow: 0 4px 20px rgba(26,42,15,0.3);
}
.ts-bubble code {
    font-family: 'DM Mono', monospace;
    background: #1e2226; padding: 2px 6px;
    border-radius: 4px; font-size: 0.85em;
    color: var(--accent2);
    transition: background 0.2s;
}
.ts-bubble code:hover { background: #252930; }
.ts-time {
    font-size: 0.68rem; color: var(--muted);
    font-family: 'DM Mono', monospace;
    margin-top: 6px;
    opacity: 0.7;
    transition: opacity 0.3s;
}
.ts-message:hover .ts-time { opacity: 1; }

/* ── assessment question block ── */
.ts-question-block {
    background: linear-gradient(135deg, #111315, #161a1e);
    border: 1px solid #2a3040;
    border-left: 3px solid var(--accent2);
    border-radius: 2px 10px 10px 10px;
    padding: 1rem 1.15rem;
    font-size: 0.92rem; line-height: 1.7;
    max-width: 100%;
    animation: questionSlide 0.55s var(--ease-out-soft);
    transition: border-color 0.3s, box-shadow 0.3s;
}
.ts-question-block:hover {
    border-color: #354060;
    box-shadow: 0 4px 24px rgba(96,200,240,0.08);
}
@keyframes questionSlide {
    from { opacity: 0; transform: translateX(-8px) translateY(6px); }
    to   { opacity: 1; transform: translateX(0) translateY(0); }
}
.ts-question-badge {
    display: inline-block; font-family: 'DM Mono', monospace;
    font-size: 0.65rem; letter-spacing: 0.08em;
    text-transform: uppercase; padding: 2px 8px;
    border-radius: 4px; margin-bottom: 0.5rem;
    transition: transform 0.2s var(--ease-spring);
}
.ts-question-badge:hover { transform: scale(1.05); }
.ts-question-badge.beginner { background: #0f2a1a; color: var(--success); border: 1px solid #1a3a2a; }
.ts-question-badge.intermediate { background: #2a2a0f; color: var(--warn); border: 1px solid #3a3a1a; }
.ts-question-badge.advanced { background: #2a0f0f; color: var(--danger); border: 1px solid #3a1a1a; }

/* ── assessment banner ── */
.ts-assess-banner {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.85rem 1.15rem; margin: 1rem 0;
    border-radius: 8px;
    background: linear-gradient(135deg, #0f1a2a, #141f30);
    border: 1px solid #1a2a40;
    animation: bannerEnter 0.6s var(--ease-out-soft);
    transition: border-color 0.3s, box-shadow 0.3s;
}
.ts-assess-banner:hover {
    border-color: #253a55;
    box-shadow: 0 2px 16px rgba(96,200,240,0.08);
}
@keyframes bannerEnter {
    from { opacity: 0; transform: scaleX(0.95); }
    to   { opacity: 1; transform: scaleX(1); }
}
.ts-assess-banner-icon {
    font-size: 1.3rem;
    animation: iconBreathe 3s ease-in-out infinite;
}
@keyframes iconBreathe {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.1); }
}
.ts-assess-banner-text {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem; color: var(--accent2);
    letter-spacing: 0.06em;
}
.ts-assess-progress {
    margin-left: auto; font-family: 'DM Mono', monospace;
    font-size: 0.7rem; color: var(--muted);
}

/* ── info card (enhanced) ── */
.ts-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.25rem;
    margin-bottom: 1.5rem;
    transition: border-color 0.4s, box-shadow 0.4s, transform 0.3s;
    animation: cardReveal 0.5s var(--ease-out-soft);
}
@keyframes cardReveal {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.ts-card:hover {
    border-color: #2a3a20;
    box-shadow: 0 4px 24px rgba(200,240,96,0.04);
    transform: translateY(-1px);
}
.ts-card-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem; color: var(--accent);
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 0.75rem;
    display: flex; align-items: center; justify-content: space-between;
}
.ts-completion {
    font-size: 0.65rem; color: var(--accent2);
    font-family: 'DM Mono', monospace;
}
.ts-review-badge {
    display: inline-block; font-family: 'DM Mono', monospace;
    font-size: 0.62rem; letter-spacing: 0.06em;
    text-transform: uppercase; padding: 3px 9px;
    border-radius: 20px; margin-bottom: 0.75rem;
}
.ts-review-badge.pending { background: #2a2a0f; color: var(--warn); border: 1px solid #3a3a1a; }
.ts-review-badge.approved { background: #0f2a1a; color: var(--success); border: 1px solid #1a3a2a; }
.ts-review-badge.rejected { background: #2a0f0f; color: var(--danger); border: 1px solid #3a1a1a; }
.ts-completion-bar {
    height: 3px; background: var(--border); border-radius: 2px;
    margin-bottom: 0.75rem; overflow: hidden;
}
.ts-completion-fill {
    height: 100%; border-radius: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    transition: width 0.8s var(--ease-out-soft);
}
.ts-field {
    display: flex; gap: 0.5rem; margin-bottom: 0.35rem; font-size: 0.85rem;
    transition: background 0.2s;
    padding: 2px 4px; border-radius: 4px;
}
.ts-field:hover { background: rgba(255,255,255,0.02); }
.ts-field-label { color: var(--muted); min-width: 110px; }
.ts-field-value { color: var(--text); transition: color 0.3s; }
.ts-field-value.filled { color: var(--accent); }
.ts-tag {
    display: inline-block;
    background: #1a2a0f; color: var(--accent);
    border: 1px solid #2a4020;
    border-radius: 4px; padding: 2px 8px;
    font-size: 0.75rem; font-family: 'DM Mono', monospace;
    margin: 2px;
    transition: transform 0.25s var(--ease-spring), box-shadow 0.3s, background 0.3s;
}
.ts-tag:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(200,240,96,0.15);
    background: #1f3012;
}

/* ── context memory chip ── */
.ts-context {
    display: flex; flex-wrap: wrap; gap: 0.4rem;
    padding: 0.5rem 0; margin-bottom: 0.5rem;
    animation: fadeUp 0.4s var(--ease-out-soft);
}
.ts-context-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: #111418; border: 1px solid var(--border);
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.68rem; color: var(--muted);
    font-family: 'DM Mono', monospace;
    transition: border-color 0.3s, transform 0.2s var(--ease-spring), background 0.3s;
}
.ts-context-chip:hover {
    border-color: #333840;
    transform: translateY(-1px);
    background: #151920;
}
.ts-context-chip .dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--accent2);
    animation: dotPulse 2s ease-in-out infinite;
}
@keyframes dotPulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.4; }
}

/* ── toast / micro-feedback ── */
.ts-toast {
    position: fixed; top: 1rem; right: 1rem;
    background: rgba(26,42,15,0.95); color: var(--accent);
    border: 1px solid #2a4020; border-radius: 10px;
    padding: 0.65rem 1.1rem; font-size: 0.78rem;
    font-family: 'DM Mono', monospace;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    animation: toastIn 0.4s var(--ease-out-soft), toastOut 0.4s var(--ease-smooth) 2.5s forwards;
    z-index: 9999;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
@keyframes toastIn {
    from { opacity: 0; transform: translateY(-16px) scale(0.95); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes toastOut {
    from { opacity: 1; transform: translateY(0) scale(1); }
    to   { opacity: 0; transform: translateY(-12px) scale(0.95); }
}

/* ── chat input override ── */
.stChatInput {
    transition: none;
}
.stChatInput textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.35s, box-shadow 0.35s !important;
}
.stChatInput textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(200,240,96,0.08), 0 4px 20px rgba(0,0,0,0.2) !important;
}
.stChatInput textarea::placeholder {
    color: var(--muted) !important;
    opacity: 0.6 !important;
    transition: opacity 0.3s !important;
}
.stChatInput textarea:focus::placeholder {
    opacity: 0.3 !important;
}

/* ── typing indicator ── */
.ts-typing { display: flex; gap: 5px; align-items: center; padding: 6px 0; }
.ts-typing span {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--muted); display: inline-block;
    transition: background 0.3s;
}
.ts-typing span:nth-child(1) { animation: typingBounce 1.4s 0s infinite; }
.ts-typing span:nth-child(2) { animation: typingBounce 1.4s 0.15s infinite; }
.ts-typing span:nth-child(3) { animation: typingBounce 1.4s 0.3s infinite; }
@keyframes typingBounce {
    0%, 80%, 100% { transform: translateY(0); background: var(--muted); }
    40% { transform: translateY(-6px); background: var(--accent); }
}

/* ── end screen & summary ── */
.ts-end {
    text-align: center; padding: 2.25rem;
    border: 1px solid var(--border); border-radius: 14px;
    background: var(--surface);
    animation: endReveal 0.7s var(--ease-out-soft);
    box-shadow: 0 8px 40px rgba(0,0,0,0.15);
}
@keyframes endReveal {
    from { opacity: 0; transform: translateY(16px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
.ts-end-icon {
    font-size: 2.5rem; margin-bottom: 1rem;
    animation: endIconPop 0.6s 0.3s var(--ease-spring) backwards;
}
@keyframes endIconPop {
    from { opacity: 0; transform: scale(0.5); }
    to   { opacity: 1; transform: scale(1); }
}
.ts-end h2 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem; color: var(--accent); margin-bottom: 0.5rem;
}
.ts-end p { color: var(--muted); font-size: 0.9rem; line-height: 1.6; }

.ts-summary-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 0.75rem; margin-top: 1.25rem; text-align: left;
}
.ts-summary-item {
    background: #0f1114; border: 1px solid var(--border);
    border-radius: 8px; padding: 0.85rem;
    transition: border-color 0.3s, transform 0.25s var(--ease-spring), box-shadow 0.3s;
    animation: summaryItemIn 0.5s var(--ease-out-soft) backwards;
}
.ts-summary-item:nth-child(1) { animation-delay: 0.1s; }
.ts-summary-item:nth-child(2) { animation-delay: 0.15s; }
.ts-summary-item:nth-child(3) { animation-delay: 0.2s; }
.ts-summary-item:nth-child(4) { animation-delay: 0.25s; }
.ts-summary-item:nth-child(5) { animation-delay: 0.3s; }
.ts-summary-item:nth-child(6) { animation-delay: 0.35s; }
@keyframes summaryItemIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.ts-summary-item:hover {
    border-color: #333840;
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}
.ts-summary-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem; color: var(--muted);
    letter-spacing: 0.1em; text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.ts-summary-value {
    font-size: 0.88rem; color: var(--text);
}

/* ── quick action buttons ── */
.ts-actions {
    display: flex; gap: 0.5rem; margin-top: 0.5rem;
    flex-wrap: wrap;
}
.ts-action-btn {
    background: #111418; border: 1px solid var(--border);
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.72rem; color: var(--muted);
    font-family: 'DM Mono', monospace;
    cursor: pointer;
    transition: all 0.3s var(--ease-smooth);
}
.ts-action-btn:hover {
    border-color: var(--accent); color: var(--accent);
    background: #151a10;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(200,240,96,0.1);
}

/* ── Streamlit button polish ── */
.stButton > button {
    transition: all 0.3s var(--ease-smooth) !important;
    border-radius: 8px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
}
.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}
.stDownloadButton > button {
    transition: all 0.3s var(--ease-smooth) !important;
    border-radius: 8px !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
}

/* ── scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: var(--border); border-radius: 10px;
    transition: background 0.3s;
}
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ── selection ── */
::selection {
    background: rgba(200,240,96,0.2);
    color: var(--text);
}

/* ── reduce Streamlit layout jank ── */
.stMarkdown, .stEmpty, [data-testid="stVerticalBlock"] {
    transition: none !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Auto-scroll JS
# ─────────────────────────────────────────────
st.markdown("""
<script>
(function() {
    function smoothScroll() {
        window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
    }
    // Scroll on load
    window.addEventListener('load', function() { setTimeout(smoothScroll, 200); });
    // Scroll when new content is added (chat messages)
    var observer = new MutationObserver(function(mutations) {
        var hasNew = mutations.some(function(m) { return m.addedNodes.length > 0; });
        if (hasNew) setTimeout(smoothScroll, 100);
    });
    var target = document.querySelector('[data-testid="stVerticalBlock"]') || document.body;
    observer.observe(target, {childList: true, subtree: true});
})();
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# System prompt (enhanced)
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a professional hiring assistant for TalentScout, a technology recruitment agency. Your ONLY purpose is to screen candidates for technical roles. Do not deviate from this purpose.

## Your Workflow (follow this order strictly)

### Phase 1 — Welcome
Greet the candidate warmly. Introduce yourself as TalentScout's AI hiring assistant. Explain the process takes ~5 minutes.

### Phase 2 — Information Gathering
Collect ALL of the following, one or two at a time (don't overwhelm):
- Full Name
- Email Address
- Phone Number
- Years of Experience (total)
- Desired Position(s)
- Current Location (City, Country)
- Tech Stack (programming languages, frameworks, databases, tools)

After collecting tech stack, confirm the full list back to the candidate.

### Phase 3 — Technical Assessment
For EACH technology in their stack (up to 5 technologies), ask 3-5 well-crafted technical questions per technology, one at a time. Questions should:
- Match seniority level (less than 2 years → conceptual/beginner; 2–5 years → practical/intermediate; 5+ years → design/architecture/advanced)
- Be specific and practical, not trivial
- Wait for the answer before asking the next question
- Label each question as **Question [n]/[total]:** where total = (number of technologies × 4)
- After the label, include a difficulty tag on the same line: `[Beginner]`, `[Intermediate]`, or `[Advanced]`
- Cover different aspects: e.g., for Python ask one about core language and one about a common library/pattern

### Phase 4 — Closing
ONLY after ALL technical questions have been asked and answered: thank the candidate, summarize what was collected, inform them a recruiter will reach out within 2-3 business days, and wish them well.
DO NOT say "reach out within 2-3 business days" or "recruiter will reach out" during Phase 2 or Phase 3.

## Rules
- Stay strictly on topic. If user asks unrelated questions, politely redirect.
- Be professional but warm — not robotic.
- If user says "exit", "quit", "bye", "stop", or "end" → gracefully conclude the session.
- Never ask for sensitive info like SSN, passport, or financial details.
- If input is unclear, ask for clarification once; don't repeat.
- Format technical questions clearly with a "**Question [n]/[total]:**" label.
- When you have collected all candidate info, output a JSON block ONLY once, wrapped in ```json ... ``` with this structure:
  {"name":"","email":"","phone":"","experience_years":"","desired_positions":[],"location":"","tech_stack":[]}

## Tone
Professional, encouraging, concise. Use line breaks for readability."""

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],
        "candidate": {},
        "ended": False,
        "phase": 0,              # 0=welcome, 1=gathering, 2=assessment, 3=done
        "question_count": 0,
        "total_questions": 0,
        "feedback": {},          # msg_index -> "up"/"down"
        "toast": None,
        "assessment_started": False,
        "session_id": f"session-{uuid4().hex[:10]}",
        "candidate_id": f"candidate-{uuid4().hex[:10]}",
        "record_saved": False,
        "saved_record_id": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
END_KEYWORDS = {"exit", "quit", "bye", "goodbye", "stop", "end", "thanks bye", "that's all"}

def is_exit(text: str) -> bool:
    return any(kw in text.lower() for kw in END_KEYWORDS)

def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def validate_phone(phone: str) -> bool:
    digits = re.sub(r'[\s\-\(\)\+]', '', phone)
    return len(digits) >= 7 and digits.isdigit()


def redact_email(email: str) -> str:
    """Mask the local part of an email, keeping the domain for triage (e.g. j***n@gmail.com)."""
    if not email or "@" not in email:
        return email
    user, _, domain = email.partition("@")
    if len(user) <= 2:
        masked = user[0] + "*"
    else:
        masked = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked}@{domain}"


def redact_phone(phone: str) -> str:
    """Mask all but the last 4 digits of a phone number."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) <= 4:
        return "*" * len(digits)
    return "*" * (len(digits) - 4) + digits[-4:]


def redact_candidate(candidate: dict) -> dict:
    """Mask directly-identifying contact fields (email, phone) before writing to disk at rest."""
    if not candidate:
        return candidate
    redacted = dict(candidate)
    if redacted.get("email"):
        redacted["email"] = redact_email(redacted["email"])
    if redacted.get("phone"):
        redacted["phone"] = redact_phone(redacted["phone"])
    return redacted


def read_json_list(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def write_json_list(filepath: str, entries: list):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def has_candidate_profile(candidate: dict | None) -> bool:
    if not candidate:
        return False
    return any([
        candidate.get("name"),
        candidate.get("email"),
        candidate.get("phone"),
        candidate.get("experience_years"),
        candidate.get("location"),
        candidate.get("desired_positions"),
        candidate.get("tech_stack"),
    ])


def current_workflow_step() -> str:
    phase = smart_phase_detect()
    return {
        0: "Welcome",
        1: "Information Gathering",
        2: "Technical Assessment",
        3: "Closing",
    }.get(phase, "Conversation")


def attach_tracking_fields(candidate: dict | None) -> dict:
    tracked = dict(candidate or {})
    tracked.setdefault("session_id", st.session_state.session_id)
    tracked.setdefault("candidate_id", st.session_state.candidate_id)
    tracked.setdefault("review_status", REVIEW_PENDING)
    tracked.setdefault("reviewed_by", "")
    tracked.setdefault("reviewed_at", "")
    tracked.setdefault("review_notes", "")
    if st.session_state.saved_record_id:
        tracked.setdefault("record_id", st.session_state.saved_record_id)
    return tracked


def update_audit_entries(session_id: str, candidate_id: str, updates: dict):
    if not session_id or not candidate_id:
        return
    entries = read_json_list(AUDIT_LOG_FILE)
    changed = False
    for entry in entries:
        if entry.get("session_id") == session_id and entry.get("candidate_id") == candidate_id:
            entry.update(updates)
            changed = True
    if changed:
        write_json_list(AUDIT_LOG_FILE, entries)


def log_interaction(
    prompt: str,
    output: str,
    reviewer_status: str = REVIEW_PENDING,
    workflow_step: str | None = None,
    event_type: str = "ai_processing",
    model_tool: str = MODEL_TOOL_LABEL,
    extra: dict | None = None,
):
    """Append one workflow step to the audit trail with shared session/candidate identifiers."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "session_id": st.session_state.get("session_id", ""),
        "candidate_id": st.session_state.get("candidate_id", ""),
        "record_id": st.session_state.get("saved_record_id") or st.session_state.get("candidate", {}).get("record_id", ""),
        "workflow_step": workflow_step or current_workflow_step(),
        "model_tool": model_tool,
        "prompt": prompt,
        "output": output,
        "reviewer_status": reviewer_status,
    }
    if extra:
        entry.update(extra)
    existing = read_json_list(AUDIT_LOG_FILE)
    existing.append(entry)
    write_json_list(AUDIT_LOG_FILE, existing)


def fallback_response():
    return "I'm here to help with your interview process. Could you please clarify your response?"    


def extract_candidate_json(text: str) -> dict | None:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None

def detect_question_info(text: str) -> tuple[int, int, str]:
    """Extract question number, total, and difficulty from response text."""
    q_match = re.search(r'Question\s+(\d+)\s*/\s*(\d+)', text, re.IGNORECASE)
    q_num = int(q_match.group(1)) if q_match else 0
    q_total = int(q_match.group(2)) if q_match else 0

    difficulty = "intermediate"
    if re.search(r'\[Beginner\]', text, re.IGNORECASE):
        difficulty = "beginner"
    elif re.search(r'\[Advanced\]', text, re.IGNORECASE):
        difficulty = "advanced"

    return q_num, q_total, difficulty

def smart_phase_detect() -> int:
    """Intelligent phase detection from conversation content."""
    msgs = st.session_state.messages
    n = len(msgs)
    if n == 0:
        return 0
    if st.session_state.ended:
        return 3

    # Check for assessment indicators in recent messages
    for msg in reversed(msgs[-6:]):
        if msg["role"] == "assistant":
            if re.search(r'Question\s+\d+\s*/\s*\d+', msg["content"], re.IGNORECASE):
                return 2

    if st.session_state.candidate:
        return 2
    if n < 4:
        return 1
    return 1

def get_completion_pct() -> int:
    """Calculate profile completion percentage."""
    c = st.session_state.candidate
    if not has_candidate_profile(c):
        return 0
    fields = ["name", "email", "phone", "experience_years", "location"]
    filled = sum(1 for f in fields if c.get(f))
    if c.get("desired_positions"):
        filled += 1
    if c.get("tech_stack"):
        filled += 1
    return int((filled / 7) * 100)

def get_context_chips() -> list:
    """Build context awareness chips from collected data."""
    chips = []
    c = st.session_state.candidate
    if not c:
        return chips
    if c.get("name"):
        chips.append(c["name"])
    if c.get("experience_years"):
        chips.append(f"{c['experience_years']} yrs exp")
    for tech in (c.get("tech_stack") or [])[:4]:
        chips.append(tech)
    return chips

def save_candidate_record(candidate: dict, messages: list):
    """Append session data to candidates_log.json (simulated backend, GDPR-aware).

    Contact fields (email, phone) are redacted at rest — the full record with
    a resolvable review status lives in the reviewer-facing PDF, generated on demand.
    """
    tracked_candidate = attach_tracking_fields(candidate)
    record_id = tracked_candidate.get("record_id") or f"record-{uuid4().hex[:10]}"
    tracked_candidate["record_id"] = record_id
    candidate_payload = redact_candidate(tracked_candidate) if has_candidate_profile(tracked_candidate) else {}
    review_metadata = {
        "reviewed_by": tracked_candidate.get("reviewed_by", ""),
        "reviewed_at": tracked_candidate.get("reviewed_at", ""),
        "review_notes": tracked_candidate.get("review_notes", ""),
    }
    record = {
        "record_id": record_id,
        "timestamp": datetime.now().isoformat(),
        "session_id": tracked_candidate.get("session_id", st.session_state.session_id),
        "candidate_id": tracked_candidate.get("candidate_id", st.session_state.candidate_id),
        "model_tool": MODEL_TOOL_LABEL,
        "workflow_step": "Pending Human Review",
        "review_status": tracked_candidate.get("review_status", REVIEW_PENDING),
        "review_metadata": review_metadata,
        "workflow_snapshot": {
            "input": "Candidate free-text responses and technical answers",
            "ai_processing": f"{MODEL_TOOL_LABEL} with the system prompt and full conversation history",
            "output": "Structured candidate profile, technical screening questions, and downloadable report",
            "pending_human_review": tracked_candidate.get("review_status", REVIEW_PENDING),
        },
        "candidate": candidate_payload,
        "session_length": len(messages),
        "questions_answered": sum(
            1 for m in messages
            if m["role"] == "user" and any(
                re.search(r'Question\s+\d+\s*/\s*\d+', prev["content"], re.IGNORECASE)
                for prev in messages[:messages.index(m)]
                if prev["role"] == "assistant"
            )
        ),
    }
    filepath = CANDIDATES_LOG_FILE
    existing = read_json_list(filepath)
    existing.append(record)
    write_json_list(filepath, existing)
    update_audit_entries(
        record["session_id"],
        record["candidate_id"],
        {
            "record_id": record_id,
            "reviewer_status": record["review_status"],
        },
    )
    log_interaction(
        prompt="Candidate session finalized and queued for review.",
        output=f"Saved {record_id} to the reviewer queue with status {record['review_status']}.",
        reviewer_status=record["review_status"],
        workflow_step="Pending Human Review",
        event_type="candidate_record_created",
        model_tool="TalentScout Workflow",
        extra={
            "record_id": record_id,
            "session_length": record["session_length"],
            "questions_answered": record["questions_answered"],
            "workflow_snapshot": record["workflow_snapshot"],
        },
    )
    return record_id


def finalize_session_record():
    if st.session_state.record_saved:
        return st.session_state.saved_record_id
    candidate = attach_tracking_fields(st.session_state.candidate) if has_candidate_profile(st.session_state.candidate) else {}
    record_id = save_candidate_record(candidate, st.session_state.messages)
    st.session_state.saved_record_id = record_id
    st.session_state.record_saved = True
    if candidate:
        st.session_state.candidate = candidate
        st.session_state.candidate["record_id"] = record_id
    return record_id


def log_reviewer_action(record: dict, previous_status: str, new_status: str, reviewer_name: str, reviewer_notes: str):
    reviewed_at = record.get("review_metadata", {}).get("reviewed_at", "")
    log_interaction(
        prompt=reviewer_notes or "Reviewer decision submitted from the TalentScout sidebar.",
        output=f"Record {record.get('record_id', 'untracked')} moved from {previous_status} to {new_status}.",
        reviewer_status=new_status,
        workflow_step="Human Review",
        event_type="human_review_decision",
        model_tool=REVIEWER_TOOL_LABEL,
        extra={
            "session_id": record.get("session_id", ""),
            "candidate_id": record.get("candidate_id", ""),
            "record_id": record.get("record_id", ""),
            "reviewed_by": reviewer_name,
            "reviewed_at": reviewed_at,
            "review_notes": reviewer_notes,
            "previous_status": previous_status,
        },
    )


def apply_review_decision(records: list, idx: int, new_status: str, reviewer_name: str, reviewer_notes: str):
    reviewed_at = datetime.now().isoformat()
    previous_status = records[idx].get("review_status", REVIEW_PENDING)
    records[idx]["review_status"] = new_status
    records[idx]["review_metadata"] = {
        "reviewed_by": reviewer_name,
        "reviewed_at": reviewed_at,
        "review_notes": reviewer_notes,
    }

    candidate = records[idx].get("candidate") or {}
    if candidate:
        candidate["review_status"] = new_status
        candidate["reviewed_by"] = reviewer_name
        candidate["reviewed_at"] = reviewed_at
        candidate["review_notes"] = reviewer_notes
        records[idx]["candidate"] = candidate

    write_json_list(CANDIDATES_LOG_FILE, records)
    update_audit_entries(
        records[idx].get("session_id", ""),
        records[idx].get("candidate_id", ""),
        {
            "reviewer_status": new_status,
            "record_id": records[idx].get("record_id", ""),
            "reviewed_by": reviewer_name,
            "reviewed_at": reviewed_at,
            "review_notes": reviewer_notes,
        },
    )
    log_reviewer_action(records[idx], previous_status, new_status, reviewer_name, reviewer_notes)


def chat_with_llm(user_message: str) -> str:
    """Call Groq with the full conversation history and safe retry/error handling."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key or api_key in {"your_groq_api_key_here", "YOUR_GROQ_API_KEY_HERE"}:
        error_text = (
            "⚠️ **Configuration Error:** `GROQ_API_KEY` is missing or still set to the placeholder. "
            "Copy `.env.example` to `.env`, add a valid Groq API key, and restart Streamlit."
        )
        try:
            log_interaction(
                user_message, error_text, reviewer_status="N/A — configuration error",
                workflow_step=current_workflow_step(), event_type="configuration_error",
            )
        except Exception:
            pass
        return error_text

    client = Groq(api_key=api_key, timeout=45.0, max_retries=0)

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in st.session_state.messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
    api_messages.append({"role": "user", "content": user_message})

    last_error = None
    for attempt in range(MAX_API_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=api_messages,
                max_tokens=1024,
                temperature=0.7,
            )
            output_text = (response.choices[0].message.content or "").strip()
            if not output_text:
                raise RuntimeError("Groq returned an empty response.")
            try:
                log_interaction(user_message, output_text, workflow_step=current_workflow_step())
            except Exception:
                pass
            return output_text
        except Exception as e:
            last_error = e
            error_name = type(e).__name__
            if error_name in {"AuthenticationError", "PermissionDeniedError", "NotFoundError"}:
                break
            if attempt < MAX_API_RETRIES:
                time.sleep(API_RETRY_DELAY_SECONDS * (attempt + 1))

    error_name = type(last_error).__name__ if last_error else "UnknownError"
    if error_name == "AuthenticationError":
        message = (
            "⚠️ **Groq authentication failed.** Your API key is invalid or expired. "
            "Create a new key in the Groq Console, update `.env`, and restart the app."
        )
    elif error_name == "NotFoundError":
        message = (
            f"⚠️ **Model error.** Groq could not find `{MODEL_NAME}`. "
            "Check `GROQ_MODEL` in `.env` and use a currently supported Groq model."
        )
    elif error_name == "PermissionDeniedError":
        message = "⚠️ **Groq permission error.** Check that your API key has access to the selected model."
    else:
        message = (
            "⚠️ **AI service error.** Groq could not complete this request after the configured retries. "
            "Please try again shortly."
        )

    try:
        log_interaction(
            user_message, message, reviewer_status="N/A — system error",
            workflow_step=current_workflow_step(), event_type="ai_processing_error",
            extra={"error_type": error_name, "model_config": MODEL_NAME, "retry_attempts": MAX_API_RETRIES},
        )
    except Exception:
        pass
    return message


def generate_pdf(candidate: dict, filename="candidate_report.pdf"):
    candidate = attach_tracking_fields(candidate)
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(Paragraph("TalentScout Candidate Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("AI-assisted screening only. Final decisions require human review.", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Candidate Details
    def add_field(label, value):
        elements.append(Paragraph(f"<b>{label}:</b> {value}", styles["Normal"]))
        elements.append(Spacer(1, 8))

    add_field("Generated At", datetime.now().strftime("%Y-%m-%d %H:%M"))
    add_field("Review Status", candidate.get("review_status", REVIEW_PENDING))
    add_field("Record ID", candidate.get("record_id", st.session_state.saved_record_id or "Pending save"))
    add_field("Session ID", candidate.get("session_id", st.session_state.session_id))
    add_field("Candidate ID", candidate.get("candidate_id", st.session_state.candidate_id))
    add_field("Model / Tool Used", MODEL_TOOL_LABEL)
    add_field("Reviewer", candidate.get("reviewed_by") or "Pending human review")
    add_field("Reviewed At", candidate.get("reviewed_at") or "Pending human review")
    add_field("Review Notes", candidate.get("review_notes") or "No notes captured yet")
    add_field("Name", candidate.get("name", "N/A"))
    add_field("Email", candidate.get("email", "N/A"))
    add_field("Phone", candidate.get("phone", "N/A"))
    add_field("Experience", f"{candidate.get('experience_years', 'N/A')} years")
    add_field("Location", candidate.get("location", "N/A"))

    roles = ", ".join(candidate.get("desired_positions", []))
    tech = ", ".join(candidate.get("tech_stack", []))

    add_field("Desired Roles", roles or "N/A")
    add_field("Tech Stack", tech or "N/A")
    add_field("Questions Answered", st.session_state.question_count or 0)
    add_field("Input", "Candidate chat responses and technical answers")
    add_field("AI Processing", f"{MODEL_TOOL_LABEL} with the full conversation history and screening prompt")
    add_field("Output", "Structured profile, technical screening questions, and session summary")
    add_field("Pending Human Review Status", candidate.get("review_status", REVIEW_PENDING))

    doc.build(elements)

    return filename


# ─────────────────────────────────────────────
# Rendering
# ─────────────────────────────────────────────

def render_message(role: str, content: str, timestamp: str, msg_index: int = -1):
    avatar = "TS" if role == "assistant" else "ME"
    bubble_class = "user-bubble" if role == "user" else ""
    avatar_class = "bot" if role == "assistant" else "user"

    # Strip json blocks from display
    display_content = re.sub(r"```json.*?```", "", content, flags=re.DOTALL).strip()

    # Detect if this is an assessment question
    is_question = bool(re.search(r'Question\s+\d+\s*/\s*\d+', display_content, re.IGNORECASE))

    if is_question and role == "assistant":
        q_num, q_total, difficulty = detect_question_info(display_content)
        # Convert markdown
        display_content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", display_content)
        display_content = display_content.replace("\n", "<br>")

        st.markdown(f"""
        <div class="ts-message">
            <div class="ts-avatar {avatar_class}">{avatar}</div>
            <div style="width:100%">
                <div class="ts-question-block">
                    <div class="ts-question-badge {difficulty}">{difficulty}</div>
                    {display_content}
                </div>
                <div class="ts-time">{timestamp}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Convert **bold** to <b>
        display_content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", display_content)
        display_content = display_content.replace("\n", "<br>")

        st.markdown(f"""
        <div class="ts-message">
            <div class="ts-avatar {avatar_class}">{avatar}</div>
            <div>
                <div class="ts-bubble {bubble_class}">{display_content}</div>
                <div class="ts-time">{timestamp}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Feedback buttons (for assistant messages)
    if role == "assistant" and msg_index >= 0 and not st.session_state.ended:
        fb = st.session_state.feedback.get(msg_index)
        col1, col2, col3, _ = st.columns([0.06, 0.06, 0.12, 0.76])
        with col1:
            if st.button("👍", key=f"up_{msg_index}", help="Helpful",
                         type="secondary" if fb != "up" else "primary"):
                st.session_state.feedback[msg_index] = "up"
                st.rerun()
        with col2:
            if st.button("👎", key=f"dn_{msg_index}", help="Not helpful",
                         type="secondary" if fb != "down" else "primary"):
                st.session_state.feedback[msg_index] = "down"
                st.rerun()
        with col3:
            if st.button("🔄", key=f"regen_{msg_index}", help="Regenerate"):
                # Regenerate: remove last assistant message and get new response
                if msg_index == len(st.session_state.messages) - 1:
                    st.session_state.messages.pop()
                    # Find last user message content
                    if st.session_state.messages:
                        last_user = st.session_state.messages[-1]["content"]
                        new_resp = chat_with_llm(last_user)
                        ts = datetime.now().strftime("%H:%M")
                        st.session_state.messages.append({"role": "assistant", "content": new_resp, "time": ts})
                    st.rerun()


def render_candidate_card():
    c = st.session_state.candidate
    if not has_candidate_profile(c):
        return

    pct = get_completion_pct()
    tags = "".join([f'<span class="ts-tag">{t}</span>' for t in c.get("tech_stack", [])])
    positions = ", ".join(c.get("desired_positions", []))

    def val_class(v):
        return "filled" if v and v != "—" else ""

    review_status = c.get("review_status", REVIEW_PENDING)
    review_cls = {
        REVIEW_PENDING: "pending",
        REVIEW_APPROVED: "approved",
        REVIEW_REJECTED: "rejected",
    }.get(review_status, "pending")
    review_icon = {"pending": "🕒", "approved": "✅", "rejected": "❌"}[review_cls]

    st.markdown(f"""
    <div class="ts-card">
        <div class="ts-review-badge {review_cls}">{review_icon} {review_status}</div>
        <div class="ts-card-title">
            <span>📋 Candidate Profile</span>
            <span class="ts-completion">{pct}% complete</span>
        </div>
        <div class="ts-completion-bar"><div class="ts-completion-fill" style="width:{pct}%"></div></div>
        <div class="ts-field"><span class="ts-field-label">Name</span><span class="ts-field-value {val_class(c.get('name'))}">{c.get('name','—')}</span></div>
        <div class="ts-field"><span class="ts-field-label">Email</span><span class="ts-field-value {val_class(c.get('email'))}">{c.get('email','—')}</span></div>
        <div class="ts-field"><span class="ts-field-label">Phone</span><span class="ts-field-value {val_class(c.get('phone'))}">{c.get('phone','—')}</span></div>
        <div class="ts-field"><span class="ts-field-label">Experience</span><span class="ts-field-value {val_class(c.get('experience_years'))}">{c.get('experience_years','—')} yrs</span></div>
        <div class="ts-field"><span class="ts-field-label">Desired Role</span><span class="ts-field-value {val_class(positions)}">{positions or '—'}</span></div>
        <div class="ts-field"><span class="ts-field-label">Location</span><span class="ts-field-value {val_class(c.get('location'))}">{c.get('location','—')}</span></div>
        <div class="ts-field" style="flex-direction:column; gap:6px;">
            <span class="ts-field-label">Tech Stack</span>
            <div>{tags or '<span style="color:var(--muted)">—</span>'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_session_summary():
    """Render end-of-session summary dashboard."""
    c = st.session_state.candidate
    total_msgs = len(st.session_state.messages)
    user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
    q_answered = st.session_state.question_count if isinstance(st.session_state.question_count, int) else 0
    tech_list = ", ".join(c.get("tech_stack", [])) if c else "—"
    exp = c.get("experience_years", "—") if c else "—"
    name = c.get("name", "Candidate") if c else "Candidate"
    pos = ", ".join(c.get("desired_positions", [])) if c else "—"

    html = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400&family=DM+Sans:wght@400&display=swap');
    .ts-end {{
        text-align: center; padding: 2.25rem;
        border: 1px solid #232628; border-radius: 14px;
        background: #141719; font-family: 'DM Sans', sans-serif;
        color: #e8eaed;
    }}
    .ts-end-icon {{ font-size: 2.5rem; margin-bottom: 1rem; display:block; }}
    .ts-end h2 {{
        font-family: 'DM Serif Display', serif;
        font-size: 1.6rem; color: #c8f060; margin-bottom: 0.5rem;
    }}
    .ts-end p {{ color: #5a6370; font-size: 0.9rem; line-height: 1.6; }}
    .ts-summary-grid {{
        display: grid; grid-template-columns: 1fr 1fr;
        gap: 0.75rem; margin-top: 1.25rem; text-align: left;
    }}
    .ts-summary-item {{
        background: #0f1114; border: 1px solid #232628;
        border-radius: 8px; padding: 0.85rem;
    }}
    .ts-summary-label {{
        font-family: 'DM Mono', monospace;
        font-size: 0.62rem; color: #5a6370;
        letter-spacing: 0.1em; text-transform: uppercase;
        margin-bottom: 0.3rem;
    }}
    .ts-summary-value {{ font-size: 0.88rem; color: #e8eaed; }}
    </style>
    <div class="ts-end">
        <span class="ts-end-icon">✅</span>
        <h2>Session Complete</h2>
        <p>Thank you, <b>{name}</b>. Our team will review your responses and reach out within 2–3 business days.</p>
        <div class="ts-summary-grid">
            <div class="ts-summary-item">
                <div class="ts-summary-label">Experience</div>
                <div class="ts-summary-value">{exp} years</div>
            </div>
            <div class="ts-summary-item">
                <div class="ts-summary-label">Target Role</div>
                <div class="ts-summary-value">{pos}</div>
            </div>
            <div class="ts-summary-item">
                <div class="ts-summary-label">Tech Stack</div>
                <div class="ts-summary-value" style="font-size:0.8rem">{tech_list}</div>
            </div>
            <div class="ts-summary-item">
                <div class="ts-summary-label">Questions Answered</div>
                <div class="ts-summary-value">{q_answered} technical</div>
            </div>
            <div class="ts-summary-item">
                <div class="ts-summary-label">Messages Exchanged</div>
                <div class="ts-summary-value">{total_msgs} total</div>
            </div>
            <div class="ts-summary-item">
                <div class="ts-summary-label">Session Duration</div>
                <div class="ts-summary-value">{user_msgs} responses</div>
            </div>
        </div>
        <p style="margin-top:1.5rem; font-family:'DM Mono',monospace; font-size:0.72rem; color:#3a4350;">
            TalentScout · Powered by Groq · LLaMA 3.3
        </p>
    </div>
    """
    components.html(html, height=480, scrolling=False)


# ─────────────────────────────────────────────
# Progress steps
# ─────────────────────────────────────────────
STEPS = ["Welcome", "Info", "Tech Stack", "Assessment", "Complete"]
PHASE_LABELS = {
    0: ("Welcome", "Getting to know you"),
    1: ("Information Gathering", "Collecting your details"),
    2: ("Technical Assessment", "Evaluating your skills"),
    3: ("Complete", "Session finished"),
}

def render_progress(active_step: int):
    html = '<div class="ts-progress">'
    for i, _ in enumerate(STEPS):
        if i < active_step:
            cls = "done"
        elif i == active_step:
            cls = "active"
        else:
            cls = ""
        html += f'<div class="ts-step {cls}" title="{STEPS[i]}"></div>'
    html += "</div>"

    # Step labels
    html += '<div class="ts-step-labels">'
    for i, s in enumerate(STEPS):
        if i < active_step:
            lcls = "done"
        elif i == active_step:
            lcls = "active"
        else:
            lcls = ""
        html += f'<span class="ts-step-label {lcls}">{s}</span>'
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

def estimate_step() -> int:
    phase = smart_phase_detect()
    if phase == 0: return 0
    if phase == 3: return 4
    if phase == 2: return 3
    n = len(st.session_state.messages)
    if n < 4: return 1
    if n < 8: return 2
    return 3

def render_phase_banner():
    phase = smart_phase_detect()
    label, detail = PHASE_LABELS.get(phase, ("", ""))
    if not label or phase == 3:
        return

    extra = ""
    if phase == 2 and st.session_state.question_count > 0:
        extra = f'<span class="ts-assess-progress">Q {st.session_state.question_count}/{st.session_state.total_questions or "?"}</span>'

    st.markdown(f"""
    <div class="ts-phase-banner">
        <span class="ts-phase-label">📍 {label}</span>
        <span class="ts-phase-detail">{detail}</span>
        {extra}
    </div>
    """, unsafe_allow_html=True)

def render_context_chips():
    chips = get_context_chips()
    if not chips:
        return
    html = '<div class="ts-context">'
    html += '<span class="ts-context-chip"><span class="dot"></span> 🧠 Remembering</span>'
    for chip in chips:
        html += f'<span class="ts-context-chip">{chip}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_assessment_banner():
    """Show assessment start banner when entering Phase 2."""
    phase = smart_phase_detect()
    if phase == 2 and not st.session_state.assessment_started:
        st.session_state.assessment_started = True
        st.markdown("""
        <div class="ts-assess-banner">
            <span class="ts-assess-banner-icon">🧠</span>
            <span class="ts-assess-banner-text">Technical Assessment Started</span>
        </div>
        """, unsafe_allow_html=True)

def render_reviewer_panel():
    """Sidebar workflow for a human reviewer to approve/reject completed screenings.

    This is the human-in-the-loop gate the workflow requires: every AI-generated
    candidate record starts as 'Pending Human Review' and only becomes actionable
    once a reviewer explicitly approves or rejects it here.
    """
    with st.sidebar:
        st.markdown("### 🔍 Reviewer Panel")
        st.caption("Internal use — approve or reject AI-screened candidates before recruiter follow-up.")

        if not os.path.exists(CANDIDATES_LOG_FILE):
            st.info("No submissions logged yet.")
            return
        try:
            records = read_json_list(CANDIDATES_LOG_FILE)
        except Exception:
            st.warning("Could not read the candidate log.")
            return

        pending = [(i, r) for i, r in enumerate(records) if r.get("review_status") == REVIEW_PENDING and r.get("candidate")]
        if not pending:
            st.success("No pending reviews.")
            return

        for idx, rec in pending:
            cand = rec.get("candidate", {})
            name = cand.get("name", "Unknown")
            ts = rec.get("timestamp", "")[:16].replace("T", " ")
            with st.expander(f"🕒 {name} · {ts}"):
                st.markdown(f"**Record ID:** {rec.get('record_id', '—')}")
                st.markdown(f"**Email:** {cand.get('email', '—')}")
                st.markdown(f"**Phone:** {cand.get('phone', '—')}")
                st.markdown(f"**Role:** {', '.join(cand.get('desired_positions', [])) or '—'}")
                st.markdown(f"**Tech Stack:** {', '.join(cand.get('tech_stack', [])) or '—'}")
                reviewer_name = st.text_input(
                    "Reviewer name",
                    key=f"reviewer_name_{idx}",
                    placeholder="Required before approval or rejection",
                ).strip()
                reviewer_notes = st.text_area(
                    "Review notes",
                    key=f"reviewer_notes_{idx}",
                    height=90,
                    placeholder="Why are you approving or rejecting this screening?",
                ).strip()
                col1, col2 = st.columns(2)
                if col1.button("✅ Approve", key=f"sidebar_appr_{idx}", use_container_width=True):
                    if not reviewer_name:
                        st.warning("Please add the reviewer name before approving this candidate.")
                    else:
                        apply_review_decision(records, idx, REVIEW_APPROVED, reviewer_name, reviewer_notes)
                        st.rerun()
                if col2.button("❌ Reject", key=f"sidebar_rej_{idx}", use_container_width=True):
                    if not reviewer_name:
                        st.warning("Please add the reviewer name before rejecting this candidate.")
                    else:
                        apply_review_decision(records, idx, REVIEW_REJECTED, reviewer_name, reviewer_notes)
                        st.rerun()


def render_typing_indicator():
    st.markdown("""
    <div class="ts-message">
        <div class="ts-avatar bot">TS</div>
        <div>
            <div class="ts-bubble">
                <div class="ts-typing">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def get_input_placeholder() -> str:
    """Dynamic placeholder based on current phase."""
    phase = smart_phase_detect()
    placeholders = {
        0: "Say hello to get started…",
        1: "Type your response here…",
        2: "Type your answer to the technical question…",
        3: "Session complete.",
    }
    return placeholders.get(phase, "Type your response here…")


# ═════════════════════════════════════════════
# MAIN RENDER
# ═════════════════════════════════════════════

# Reviewer sidebar (human-in-the-loop approval workflow)
render_reviewer_panel()

# Header
st.markdown("""
<div class="ts-header">
    <div>
        <div class="ts-logo">TalentScout</div>
        <div class="ts-tagline">AI Candidate Screening Assistant · Tech Placements</div>
    </div>
    <div class="ts-dot"></div>
</div>
""", unsafe_allow_html=True)

# Privacy indicator
st.markdown("""
<div class="ts-privacy">
    🔒 Confidential screening workflow · Redacted queue data is stored and every final decision requires human review
</div>
""", unsafe_allow_html=True)

# Progress
render_progress(estimate_step())

# Phase banner
render_phase_banner()

# Context chips
render_context_chips()

# Candidate card (once info is collected)
render_candidate_card()

# Assessment banner
render_assessment_banner()

# Toast notification
if st.session_state.toast:
    st.markdown(f'<div class="ts-toast">{st.session_state.toast}</div>', unsafe_allow_html=True)
    st.session_state.toast = None

# Greeting bootstrap
if not st.session_state.messages and not st.session_state.ended:
    typing_placeholder = st.empty()
    typing_placeholder.markdown("""
    <div class="ts-message">
        <div class="ts-avatar bot">TS</div>
        <div><div class="ts-bubble">
            <div class="ts-typing"><span></span><span></span><span></span></div>
        </div></div>
    </div>
    """, unsafe_allow_html=True)
    greeting = chat_with_llm("Hello, I'm here to start the interview process.")
    typing_placeholder.empty()
    ts = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "assistant", "content": greeting, "time": ts})

# Render chat history
for idx, msg in enumerate(st.session_state.messages):
    render_message(msg["role"], msg["content"], msg.get("time", ""), msg_index=idx)

# End screen
if st.session_state.ended:
    render_session_summary()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Start New Session", type="primary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col2:
        if has_candidate_profile(st.session_state.candidate):
            pdf_file = generate_pdf(st.session_state.candidate)

            with open(pdf_file, "rb") as f:
                st.download_button(
                    "📄 Download PDF Report",
                    data=f,
                    file_name="candidate_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
else:
    # Chat input
    user_input = st.chat_input(get_input_placeholder())

    if user_input:
        user_input = user_input.strip()
        if not user_input:
            st.rerun()

        ts = datetime.now().strftime("%H:%M")

        # Check exit keywords BEFORE calling LLM
        if is_exit(user_input):
            st.session_state.messages.append({"role": "user", "content": user_input, "time": ts})
            farewell = "Thank you for speaking with TalentScout! 🎯 It was great learning about your background. Our team will be in touch if there's a suitable match. We'll reach out shortly — best wishes with your search! 👋"
            st.session_state.messages.append({"role": "assistant", "content": farewell, "time": ts})
            st.session_state.ended = True
            try:
                finalize_session_record()
            except Exception:
                pass
            st.rerun()

        # Input validation hints
        if smart_phase_detect() == 1:
            if "@" in user_input and not validate_email(user_input):
                st.session_state.toast = "⚠️ That doesn't look like a valid email address"
            if re.match(r'^[\d\s\-\+\(\)]+$', user_input) and not validate_phone(user_input):
                st.session_state.toast = "⚠️ Phone number seems too short"

        # Add user message to history FIRST so LLM sees it in context
        st.session_state.messages.append({"role": "user", "content": user_input, "time": ts})

        # Get ONE response from LLM
        response = chat_with_llm(user_input)

        ts2 = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "assistant", "content": response, "time": ts2})

        # Extract candidate info if present
        parsed = extract_candidate_json(response)
        if parsed:
            merged_candidate = dict(st.session_state.candidate or {})
            merged_candidate.update(parsed)
            st.session_state.candidate = attach_tracking_fields(merged_candidate)
            st.session_state.toast = "✔ Profile Updated — Pending Human Review"

        # Track assessment questions — increment counter properly
        q_num, q_total, _ = detect_question_info(response)
        if q_num > 0:
            st.session_state.question_count = q_num   # use actual question number
            if q_total > 0:
                st.session_state.total_questions = q_total

        # Check if assistant naturally concluded — only after all questions done
        # Use narrow phrases that only appear in a genuine closing, not mid-session
        end_phrases = [
            "recruiter will reach out within",
            "our team will reach out within",
            "reach out within 2-3 business days",
            "reach out within 2–3 business days",
        ]
        assessment_done = (
            st.session_state.total_questions > 0
            and st.session_state.question_count >= st.session_state.total_questions
        )
        if any(p in response.lower() for p in end_phrases) and assessment_done:
            st.session_state.ended = True
            try:
                finalize_session_record()
            except Exception:
                pass

        st.rerun()
