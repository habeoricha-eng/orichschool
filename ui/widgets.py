"""Composants réutilisés par l'app et par les salons."""
import html, json
import streamlit as st
import streamlit.components.v1 as components
from core.i18n import tr

def render_summary(s, lang):
    st.subheader(s.get("title", ""))
    with st.container(border=True):
        st.markdown(f"**{tr(lang, 'key_points')}**")
        for p in s.get("key_points", []):
            st.markdown(f"- {p}")
    if s.get("definitions"):
        with st.container(border=True):
            st.markdown(f"**{tr(lang, 'definitions')}**")
            for d in s["definitions"]:
                st.markdown(f"**{d.get('term','')}** — {d.get('definition','')}")
    if s.get("formulas"):
        with st.container(border=True):
            st.markdown(f"**{tr(lang, 'formulas')}**")
            for f in s["formulas"]:
                st.caption(f.get("name", ""))
                st.latex(f.get("latex", ""))

def render_quiz(questions, key, lang):
    """QCM avec correction immédiate dès qu'une réponse est choisie."""
    for i, q in enumerate(questions):
        with st.container(border=True):
            st.markdown(f"**{i + 1}. {q['question']}**")
            choice = st.radio("r", q["options"], index=None, key=f"{key}_{i}",
                              label_visibility="collapsed")
            if choice is not None:
                if q["options"].index(choice) == q["answer"]:
                    st.success(tr(lang, "right"))
                else:
                    st.error(tr(lang, "wrong") + " " + tr(lang, "answer_is", a=q["options"][q["answer"]]))
                st.caption(q.get("explanation", ""))

def render_flashcards(cards, key, lang):
    """Cartes recto/verso : retourner, précédente, suivante."""
    i_key, f_key = f"{key}_i", f"{key}_f"
    st.session_state.setdefault(i_key, 0)
    st.session_state.setdefault(f_key, False)
    i = st.session_state[i_key] % len(cards)
    side = "back" if st.session_state[f_key] else "front"
    text = html.escape(cards[i][side])
    st.markdown(f'<div class="flash {side}">{text}</div>', unsafe_allow_html=True)
    st.caption(f"{i + 1} / {len(cards)}")
    c1, c2, c3 = st.columns(3)
    if c1.button(tr(lang, "prev"), key=f"{key}_p", use_container_width=True):
        st.session_state[i_key] -= 1; st.session_state[f_key] = False; st.rerun()
    if c2.button(tr(lang, "flip"), key=f"{key}_x", type="primary", use_container_width=True):
        st.session_state[f_key] = not st.session_state[f_key]; st.rerun()
    if c3.button(tr(lang, "next"), key=f"{key}_n", use_container_width=True):
        st.session_state[i_key] += 1; st.session_state[f_key] = False; st.rerun()

def render_graph(g, height=460):
    """Réseau interactif (vis-network) : glisser, zoomer, survoler."""
    nodes = [{"id": n["id"], "label": n["label"]} for n in g.get("nodes", [])]
    edges = [{"from": e["from"], "to": e["to"], "label": e.get("label", ""), "arrows": "to"}
             for e in g.get("edges", [])]
    data = json.dumps({"nodes": nodes, "edges": edges}).replace("</", "<\\/")
    components.html(f"""
    <div id="g" style="height:{height - 10}px;border-radius:18px;background:rgba(255,255,255,.04);
         border:1px solid rgba(255,255,255,.12)"></div>
    <script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
    <script>
    const d = {data};
    new vis.Network(document.getElementById('g'), d, {{
      nodes: {{shape:'box', margin:10, color:{{background:'#26295a', border:'#8B8CFF',
               highlight:{{background:'#3b3f8f', border:'#FFB020'}}}},
               font:{{color:'#EDEFFB', face:'Inter', size:15}}, borderWidth:1.5}},
      edges: {{color:'#6c6fd6', font:{{color:'#aab', size:11, strokeWidth:0}}, smooth:true}},
      physics: {{stabilization:true, barnesHut:{{springLength:150}}}},
      interaction: {{hover:true, tooltipDelay:100}}
    }});
    </script>""", height=height)