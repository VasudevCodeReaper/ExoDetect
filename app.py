"""ExoDetect Mission Control. Run: python -m streamlit run app.py"""
from __future__ import annotations
import base64
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from exodetect.core import analyse
from exodetect.tess import fetch_tess_lightcurve

st.set_page_config(page_title="ExoDetect | Mission Control", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;600;700&display=swap');
.stApp{background:radial-gradient(circle at 85% 6%,rgba(62,109,158,.22),transparent 25%),radial-gradient(circle at 7% 35%,rgba(47,222,197,.10),transparent 23%),#050913;color:#edf9ff;font-family:'Space Grotesk',sans-serif}#MainMenu,footer,header{visibility:hidden}.block-container{max-width:1420px;padding:1.5rem 2.7rem 3rem}h1{font-size:4.1rem!important;line-height:.92!important;letter-spacing:-.075em!important;margin:0!important}.eyebrow,.panel{font:500 .7rem 'DM Mono',monospace;letter-spacing:.15em;text-transform:uppercase;color:#80b1c4}.copy{font-size:1.05rem;line-height:1.55;color:#9bb6c5;max-width:650px}.status{font:.7rem 'DM Mono',monospace;color:#9ab3c1;letter-spacing:.07em}.dot{color:#43e6d1;font-size:1rem}div[data-testid="stMetric"]{border:1px solid rgba(130,207,232,.16);background:linear-gradient(135deg,rgba(17,38,57,.82),rgba(7,16,31,.55));padding:1.05rem;border-radius:14px}div[data-testid="stMetricLabel"]{font:.65rem 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.12em;color:#8ca8b8}div[data-testid="stMetricValue"]{font-size:1.65rem;color:#effcff}.stButton>button{border:1px solid rgba(74,240,210,.65)!important;background:linear-gradient(115deg,#29cabc,#158ab9)!important;color:#031016!important;font:600 .75rem 'DM Mono',monospace!important;letter-spacing:.08em;text-transform:uppercase;border-radius:9px!important;padding:.7rem 1.1rem!important}.stTextInput input,.stNumberInput input{background:#091522!important;border:1px solid rgba(130,207,232,.16)!important;color:#eafcff!important;border-radius:8px!important}div[data-testid="stFileUploader"]{border:1px dashed rgba(79,207,211,.35)!important;background:rgba(13,29,43,.6)!important;border-radius:14px!important}.stTabs [data-baseweb="tab-list"]{gap:2rem;border-bottom:1px solid rgba(130,207,232,.16)}.stTabs [data-baseweb="tab"]{font:.7rem 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.09em;color:#93adbb}.stTabs [aria-selected="true"]{color:#4be6d3!important}.stTabs [data-baseweb="tab-highlight"]{background:#4be6d3}@media(max-width:700px){.block-container{padding:1rem}h1{font-size:2.8rem!important}}
</style>""",unsafe_allow_html=True)
st.markdown("""<style>
div[data-testid="stFileUploader"]{padding:.72rem 1rem!important}
div[data-testid="stFileUploader"] label{margin:0 0 .42rem!important}
</style>""", unsafe_allow_html=True)

def space_scene():
    components.html("""<style>.sun{transform:rotateX(-63deg) rotateZ(14deg) scaleY(2.25)!important}</style><style>
    *{box-sizing:border-box}body{margin:0;background:transparent;overflow:hidden}.scene{height:294px;position:relative;isolation:isolate;background:radial-gradient(circle at 48% 48%,rgba(24,126,150,.23),transparent 28%),radial-gradient(circle at 65% 39%,rgba(104,61,161,.12),transparent 34%);font:10px ui-monospace,monospace;color:#88aeba}.stars,.stars:before{position:absolute;inset:0;content:'';background-image:radial-gradient(#7ee7ee 1px,transparent 1.5px),radial-gradient(#789ad7 1px,transparent 1.5px),radial-gradient(#fff 1px,transparent 1.2px);background-size:44px 44px,77px 77px,129px 129px;background-position:0 0,21px 17px,39px 42px;opacity:.45}.stars:before{animation:drift 18s linear infinite;opacity:.5}.grid{position:absolute;inset:0;background:linear-gradient(90deg,transparent 49.7%,rgba(77,222,211,.1) 50%,transparent 50.3%),linear-gradient(transparent 49.7%,rgba(77,222,211,.08) 50%,transparent 50.3%);background-size:80px 80px;mask-image:radial-gradient(ellipse at 50% 50%,black,transparent 70%);opacity:.42}.system{position:absolute;left:50%;top:51%;width:320px;height:320px;transform:translate(-50%,-50%) rotateX(63deg) rotateZ(-14deg)}.orbit{position:absolute;left:50%;top:50%;border:1px solid rgba(103,223,226,.37);border-radius:50%;transform:translate(-50%,-50%)}.o1{width:128px;height:128px}.o2{width:210px;height:210px}.o3{width:302px;height:302px}.orbit:after{content:'';position:absolute;top:50%;left:-3px;width:6px;height:6px;border-radius:50%;background:#5cf4dc;box-shadow:0 0 12px #5cf4dc}.sun{position:absolute;left:117px;top:117px;width:86px;height:86px;border-radius:50%;background:radial-gradient(circle at 34% 31%,#fffce4 0 7%,#8df4e1 15%,#28bfc3 38%,#106b96 63%,#06263d 100%);box-shadow:0 0 18px #56ebdf,0 0 52px rgba(61,233,213,.6),0 0 116px rgba(44,135,219,.25);transform:rotateX(-63deg) rotateZ(14deg)}.sun:after{content:'';position:absolute;inset:-18px;border:1px solid rgba(99,250,231,.35);border-radius:50%;filter:blur(2px)}.planet{position:absolute;border-radius:50%;box-shadow:0 0 15px currentColor}.p1{width:13px;height:13px;left:217px;top:150px;background:#bf9bff;color:#bf9bff;animation:orbit1 5s linear infinite}.p2{width:19px;height:19px;left:243px;top:145px;background:#44f0db;color:#44f0db;animation:orbit2 9s linear infinite}.p3{width:10px;height:10px;left:282px;top:155px;background:#ffcf67;color:#ffcf67;animation:orbit3 13s linear infinite}.beam{position:absolute;left:50%;top:50%;width:1px;height:132px;background:linear-gradient(#60f2dc,transparent);transform-origin:bottom;transform:translate(-50%,-100%) rotate(72deg);opacity:.72;filter:drop-shadow(0 0 7px #42e5d3);animation:sweep 5s ease-in-out infinite}.scope{position:absolute;left:50%;top:50%;width:370px;height:370px;border:1px solid rgba(72,207,207,.15);border-radius:50%;transform:translate(-50%,-50%);animation:pulse 3s ease-out infinite}.trace{position:absolute;right:4%;bottom:17px;width:156px;height:45px;border-left:1px solid rgba(101,198,211,.25);border-bottom:1px solid rgba(101,198,211,.25);opacity:.85}.trace svg{width:100%;height:100%}.telemetry{position:absolute;right:4%;top:18px;text-align:right;line-height:1.75;letter-spacing:1px}.telemetry b,.steps b{color:#4bf1d8}.steps{position:absolute;left:3%;bottom:19px;line-height:1.8;letter-spacing:1.15px}.tag{position:absolute;left:50%;top:15px;transform:translateX(-50%);color:#c8fdf8;letter-spacing:2.2px;font-size:9px;text-shadow:0 0 12px #36e9d6}.tag:before,.tag:after{content:'';display:inline-block;width:25px;border-top:1px solid #48dcca;vertical-align:middle;margin:0 9px}@keyframes orbit1{to{transform:rotate(360deg);transform-origin:-123px 10px}}@keyframes orbit2{to{transform:rotate(360deg);transform-origin:-151px 15px}}@keyframes orbit3{to{transform:rotate(360deg);transform-origin:-165px 5px}}@keyframes sweep{50%{transform:translate(-50%,-100%) rotate(288deg);opacity:1}}@keyframes pulse{0%{transform:translate(-50%,-50%) scale(.7);opacity:.8}100%{transform:translate(-50%,-50%) scale(1.12);opacity:0}}@keyframes drift{to{transform:translate(44px,-44px)}}@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style><div class=scene><div class=stars></div><div class=grid></div><div class=tag>CANDIDATE ACQUISITION</div><div class=telemetry>SURVEY MODE <b>ACTIVE</b><br>TELESCOPE / TESS<br>MODEL / EXODETECT-01<br>UPLINK / NOMINAL</div><div class=system><i class='orbit o1'></i><i class='orbit o2'></i><i class='orbit o3'></i><i class=scope></i><i class=beam></i><i class=sun></i><i class='planet p1'></i><i class='planet p2'></i><i class='planet p3'></i></div><div class=steps><b>01</b> ACQUIRE TESS SIGNAL<br><b>02</b> FIND PERIODIC DIMMING<br><b>03</b> REVIEW EVIDENCE</div><div class=trace><svg viewBox='0 0 156 45' preserveAspectRatio='none'><path d='M0,18 L13,18 20,16 28,18 37,17 46,18 55,17 63,18 70,35 76,38 82,18 91,16 100,18 110,17 121,18 132,16 145,18 156,18' fill='none' stroke='#4ce8d5' stroke-width='1.5'/><path d='M0,18H156' stroke='#73aabd' stroke-opacity='.25'/></svg></div></div>""",height=294,scrolling=False)

def space_scene_v2():
    """Cinematic, local hero with animated scan and depth layers."""
    encoded = base64.b64encode(Path("assets/exoplanet-transit-hero.png").read_bytes()).decode("ascii")
    components.html(f'''<style>
      *{{box-sizing:border-box}}body{{margin:0;background:#050913;overflow:hidden}}.hero{{height:302px;position:relative;overflow:hidden;border-radius:18px;background:#050913}}.hero:before{{content:'';position:absolute;inset:-9%;background:url("data:image/png;base64,{encoded}") center/cover no-repeat;animation:float 14s ease-in-out infinite alternate}}.hero:after{{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(5,9,19,.1),transparent 42%,rgba(5,9,19,.36)),linear-gradient(0deg,rgba(5,9,19,.55),transparent 35%);pointer-events:none}}.scan{{position:absolute;z-index:2;top:-40%;bottom:-40%;width:28%;left:-35%;background:linear-gradient(90deg,transparent,rgba(78,244,223,.05),rgba(171,255,250,.28),rgba(78,244,223,.05),transparent);transform:skewX(-16deg);filter:blur(1px);animation:scan 5.8s ease-in-out infinite}}.pulse{{position:absolute;z-index:3;width:18px;height:18px;left:43%;top:56%;border:1px solid #6ff7e5;border-radius:50%;box-shadow:0 0 18px #44ead6;animation:pulse 3s ease-out infinite}}.hud{{position:absolute;z-index:4;right:5%;bottom:6%;text-align:right;font:10px ui-monospace,monospace;line-height:1.8;letter-spacing:1.3px;color:#c3f9f4;text-shadow:0 0 8px #0cbfaf}}.hud b{{color:#50efd9}}.label{{position:absolute;z-index:4;left:5%;top:7%;font:10px ui-monospace,monospace;letter-spacing:2px;color:#dcffff;text-shadow:0 0 9px #27cfbf}}.label:before{{content:'●';color:#46ebd4;margin-right:8px;animation:blink 1.2s infinite}}@keyframes float{{to{{transform:scale(1.07) translate(-1.2%,-1%)}}}}@keyframes scan{{0%,12%{{left:-35%;opacity:0}}35%,72%{{opacity:1}}100%{{left:112%;opacity:0}}}}@keyframes pulse{{0%{{transform:scale(.2);opacity:1}}100%{{transform:scale(16);opacity:0}}}}@keyframes blink{{50%{{opacity:.2}}}}@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style><div class=hero><div class=scan></div><div class=pulse></div><div class=label>EXOPLANET TRANSIT SCAN</div><div class=hud>SURVEY MODE <b>ACTIVE</b><br>SCAN / TESS PDCSAP<br>MODEL / EXODETECT-01</div></div>''', height=302, scrolling=False)


def plot(df,x,y,title,color):
    fig=go.Figure(go.Scattergl(x=df[x],y=df[y],mode="markers",marker={"size":3,"color":color,"opacity":.55}))
    fig.update_layout(title={"text":title,"font":{"size":15,"color":"#dff7ff"}},height=380,margin={"l":30,"r":20,"t":48,"b":35},paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(7,20,34,.72)",font={"color":"#b9d1dc"},xaxis={"gridcolor":"rgba(105,163,184,.12)"},yaxis={"gridcolor":"rgba(105,163,184,.12)"})
    return fig

left,right=st.columns([1.1,.9],vertical_alignment="center")
with left:
    st.markdown('<div class=eyebrow>Exoplanet signal intelligence platform</div>',unsafe_allow_html=True)
    st.title("Find the faint\nworlds.")
    st.markdown('<p class=copy>Upload a light curve or retrieve a public TESS target. ExoDetect searches for periodic dimmings, quantifies the event, and ranks the candidate with an auditable ML decision.</p><p class=status><span class=dot>●</span> MODEL READY &nbsp;&nbsp; NASA TESS COMPATIBLE &nbsp;&nbsp; TARGET-DISJOINT EVALUATION</p>',unsafe_allow_html=True)
with right: space_scene_v2()

st.markdown('<p class=panel>Acquire observation</p>',unsafe_allow_html=True)
input_col,model_col=st.columns([2.08,1.17])
with input_col:
    mode=st.radio("Input",["Upload light-curve CSV","Retrieve public TESS target"],horizontal=True,label_visibility="collapsed")
    if mode.startswith("Upload"):
        upload=st.file_uploader("Light-curve CSV",type="csv",help="Requires time and flux; flux_err is optional.")
        if upload: st.session_state["frame"]=pd.read_csv(upload);st.session_state["name"]=upload.name
    else:
        a,b,c,d=st.columns([1.35,.62,.95,.78],vertical_alignment="bottom")
        with a: target=st.text_input("TIC identifier",placeholder="TIC 307210830")
        with b: sector=st.number_input("Sector",min_value=0,step=1,help="0 selects one available sector automatically")
        with c: all_sectors=st.checkbox("All sectors",help="Slow: downloads and stitches every SPOC sector for this TIC")
        with d:
            if st.button("Retrieve target",type="primary",use_container_width=True):
                try:
                    message = "Downloading all available sectors from MAST..." if all_sectors else "Downloading one SPOC sector from MAST..."
                    with st.spinner(message): st.session_state["frame"]=fetch_tess_lightcurve(target,int(sector) or None,all_sectors);st.session_state["name"]=target
                except Exception as exc: st.error(str(exc))
with model_col:
    has_model=Path("models/triage.joblib").exists()
    st.markdown(f'<p class=panel style="margin-top:0">Model status</p><b style="color:{"#40e0d0" if has_model else "#f7c35c"}">{"TRAINED MODEL LOADED" if has_model else "BASELINE MODEL"}</b><br><span style="font-size:.82rem;color:#8ca8b8">{"TIC-disjoint pilot model" if has_model else "Train to activate ML"}</span>',unsafe_allow_html=True)

frame=st.session_state.get("frame")
if frame is not None:
    st.success(f'Observation staged: {st.session_state.get("name","uploaded file")} · {len(frame):,} cadence samples')
    if st.button("Run candidate analysis",type="primary"):
        try:
            with st.spinner("Detrending · BLS period search · ML classification..."):st.session_state["result"]=analyse(frame,"models/triage.joblib" if has_model else None)
        except Exception as exc: st.exception(exc)
if "result" in st.session_state:
    clean,candidate=st.session_state["result"]
    st.markdown('<p class=panel>Candidate readout</p>',unsafe_allow_html=True)
    x1,x2,x3,x4=st.columns(4);x1.metric("Classification",candidate.predicted_class.replace("_"," ").title());x2.metric("ML confidence",f"{candidate.confidence:.0%}");x3.metric("Signal to noise",f"{candidate.snr:.1f}");x4.metric("Orbital period",f"{candidate.period_days:.4f} d")
    signal,fold,evidence=st.tabs(["Signal view","Orbital fold","Evidence report"])
    with signal: st.plotly_chart(plot(clean,"time","flux_clean","Detrended stellar brightness","#43d9ce"),use_container_width=True)
    with fold:
        phase=((clean.time-candidate.epoch+.5*candidate.period_days)%candidate.period_days)-.5*candidate.period_days;fd=pd.DataFrame({"phase":phase,"flux":clean.flux_clean});fig=plot(fd,"phase","flux","Phase-folded transit candidate","#a78bfa");fig.add_vrect(x0=-candidate.duration_hours/48,x1=candidate.duration_hours/48,fillcolor="#45e2cf",opacity=.13,line_width=0);st.plotly_chart(fig,use_container_width=True)
    with evidence:
        l,r=st.columns([1.15,.85])
        with l: st.dataframe(pd.DataFrame([{"Transit depth":f"{candidate.depth_ppm:.1f} ppm","Duration":f"{candidate.duration_hours:.2f} h","Epoch":f"{candidate.epoch:.5f}","BLS FAP proxy":f"{candidate.fap:.3g}","Odd/even difference":f"{candidate.odd_even_sigma:.2f}σ","Secondary SNR":f"{candidate.secondary_snr:.2f}"}]),hide_index=True,use_container_width=True)
        with r: st.bar_chart(pd.Series(candidate.class_probabilities,name="probability"))
        if candidate.quality_flags:st.warning("Review flags: "+", ".join(candidate.quality_flags))
        st.download_button("Export decision record",json.dumps(candidate.__dict__,indent=2),"exodetect_candidate_result.json","application/json")
    st.caption("Candidate triage only. Review contamination, odd/even events, secondary eclipses and follow-up evidence before claiming an exoplanet.")
else:
    a,b,c=st.columns(3);a.metric("Input","CSV / MAST");b.metric("Detection","BLS period search");c.metric("Decision","Explainable ML")
