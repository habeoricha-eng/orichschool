"""Design : CSS Glassmorphism + enregistrement PWA. Tout le style vit ici."""
import streamlit as st
import streamlit.components.v1 as components

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 16px; }
h1, h2, h3 { font-family: 'Plus Jakarta Sans', sans-serif; letter-spacing: -0.02em; }
.stApp {
  background:
    radial-gradient(60% 40% at 10% 0%, rgba(139,140,255,.28), transparent 70%),
    radial-gradient(50% 40% at 100% 10%, rgba(94,234,212,.16), transparent 70%),
    radial-gradient(50% 50% at 50% 100%, rgba(255,176,32,.10), transparent 70%),
    #0F1226;
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.4rem; max-width: 880px; }

/* Cartes en verre */
[data-testid="stVerticalBlockBorderWrapper"], .glass {
  background: rgba(255,255,255,.055);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,.12) !important; border-radius: 18px;
  box-shadow: 0 8px 30px rgba(0,0,0,.25);
  transition: transform .2s ease, border-color .2s ease;
  animation: rise .35s ease both;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: rgba(139,140,255,.45) !important; }
@keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

/* Boutons faciles à toucher */
.stButton > button, .stFormSubmitButton > button {
  min-height: 48px; border-radius: 14px; font-weight: 600;
  background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.16);
  transition: transform .15s ease, background .2s ease;
}
.stButton > button:hover { transform: translateY(-2px); background: rgba(139,140,255,.25); border-color: #8B8CFF; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg,#7C7DFF,#5B5BF0); border: none; }

/* Onglets */
.stTabs [data-baseweb="tab-list"] { gap: 4px; overflow-x: auto; }
.stTabs [data-baseweb="tab"] { height: 46px; border-radius: 12px; padding: 0 14px; }
.stTabs [aria-selected="true"] { background: rgba(139,140,255,.2); }

/* Carte mémoire */
.flash { padding: 2.2rem 1.4rem; min-height: 190px; display: flex; align-items: center;
  justify-content: center; text-align: center; font-size: 1.25rem; line-height: 1.5;
  border-radius: 20px; background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.14);
  backdrop-filter: blur(14px); animation: rise .3s ease both; }
.flash.back { background: rgba(139,140,255,.14); border-color: rgba(139,140,255,.45); }
.chat-msg { padding: .55rem .8rem; margin: .3rem 0; border-radius: 14px; background: rgba(255,255,255,.06); }
.chat-msg b { color: #A9AAFF; }
.muted { color: rgba(237,239,251,.6); font-size: .9rem; }
#MainMenu, footer { visibility: hidden; }
</style>
"""

# Injecte manifest + méta mobiles dans le <head> de la page parente
PWA = """
<script>
const d = window.parent.document;
if (!d.querySelector('link[rel="manifest"]')) {
  const add = (tag, attrs) => { const e = d.createElement(tag); Object.assign(e, attrs); d.head.appendChild(e); };
  add('link', {rel: 'manifest', href: '/app/static/manifest.json'});
  add('link', {rel: 'apple-touch-icon', href: '/app/static/icon-192.png'});
  add('meta', {name: 'theme-color', content: '#0F1226'});
  add('meta', {name: 'apple-mobile-web-app-capable', content: 'yes'});
}
</script>
"""

def apply():
    st.markdown(CSS, unsafe_allow_html=True)
    components.html(PWA, height=0)