"""Feuille de style locale conforme au brief."""

CSS = r"""
<style>
@font-face { font-family:"IBM Plex Sans"; font-style:normal; font-weight:400; font-display:swap; src:url('/app/static/fonts/IBMPlexSans-400-latin.woff2') format('woff2'); unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD; }
@font-face { font-family:"IBM Plex Sans"; font-style:normal; font-weight:400; font-display:swap; src:url('/app/static/fonts/IBMPlexSans-400-latinext.woff2') format('woff2'); unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF; }
@font-face { font-family:"IBM Plex Sans"; font-style:normal; font-weight:500; font-display:swap; src:url('/app/static/fonts/IBMPlexSans-500-latin.woff2') format('woff2'); unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD; }
@font-face { font-family:"IBM Plex Sans"; font-style:normal; font-weight:500; font-display:swap; src:url('/app/static/fonts/IBMPlexSans-500-latinext.woff2') format('woff2'); unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF; }
@font-face { font-family:"IBM Plex Sans"; font-style:normal; font-weight:600; font-display:swap; src:url('/app/static/fonts/IBMPlexSans-600-latin.woff2') format('woff2'); unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD; }
@font-face { font-family:"IBM Plex Sans"; font-style:normal; font-weight:600; font-display:swap; src:url('/app/static/fonts/IBMPlexSans-600-latinext.woff2') format('woff2'); unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF; }
@font-face { font-family:"IBM Plex Serif"; font-style:normal; font-weight:600; font-display:swap; src:url('/app/static/fonts/IBMPlexSerif-600-latin.woff2') format('woff2'); unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD; }
@font-face { font-family:"IBM Plex Serif"; font-style:normal; font-weight:600; font-display:swap; src:url('/app/static/fonts/IBMPlexSerif-600-latinext.woff2') format('woff2'); unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF; }
@font-face { font-family:"IBM Plex Mono"; font-style:normal; font-weight:400; font-display:swap; src:url('/app/static/fonts/IBMPlexMono-400-latin.woff2') format('woff2'); unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD; }
@font-face { font-family:"IBM Plex Mono"; font-style:normal; font-weight:400; font-display:swap; src:url('/app/static/fonts/IBMPlexMono-400-latinext.woff2') format('woff2'); unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF; }
@font-face { font-family:"IBM Plex Mono"; font-style:normal; font-weight:500; font-display:swap; src:url('/app/static/fonts/IBMPlexMono-500-latin.woff2') format('woff2'); unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD; }
@font-face { font-family:"IBM Plex Mono"; font-style:normal; font-weight:500; font-display:swap; src:url('/app/static/fonts/IBMPlexMono-500-latinext.woff2') format('woff2'); unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF; }
:root {
  --papier:#F5F7F4; --encre:#1C2620; --craie:#E1E4DD; --eau:#2B6C8F;
  --sur:#3F7A5A; --vigilance:#C08A2E; --rupture:#A63D2F;
  --card:#FFFFFF; --radius:16px; --radius-sm:11px;
  --shadow:0 1px 2px rgba(15,23,20,.04), 0 8px 24px rgba(15,23,20,.06);
  --shadow-hover:0 2px 4px rgba(15,23,20,.05), 0 14px 32px rgba(15,23,20,.10);
  --tint-eau:rgba(43,108,143,.06); --tint-sur:rgba(63,122,90,.06);
  --sky-top:#4A90D9; --sky-mid:#8FB8D8; --sky-bottom:#FFD37A; --grass:#3F7A5A; --grass-dark:#2E5940;
}
html, body, [class*="st-"] { font-family: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, sans-serif; color:var(--encre); line-height:1.4; }
.stApp { background:var(--papier); }
h1, h2 { font-family:"IBM Plex Serif", Georgia, serif; font-weight:600; letter-spacing:-.01em; }
h1 { font-size:22px; }
h2 { font-size:17px; }
p, .stMarkdown p { line-height:1.45; }
code, pre, time, .mono, [data-testid="stMetricValue"], td { font-family:"IBM Plex Mono", ui-monospace, SFMono-Regular, Consolas, monospace !important; }
.block-container { max-width:1500px; padding:.8rem 1.6rem 1.1rem; }
[data-testid="stVerticalBlock"] { gap:.3rem; }
[data-testid^="stBaseButton"] { padding:.4rem .9rem !important; font-size:13.5px !important; font-weight:500 !important; transition:background .15s ease, border-color .15s ease, color .15s ease, transform .12s ease, box-shadow .15s ease; }
[data-testid^="stBaseButton"]:not([kind="primary"]) { background:var(--card) !important; border:1px solid var(--craie) !important; color:var(--encre) !important; }
[data-testid^="stBaseButton"]:not([kind="primary"]):hover { border-color:var(--eau) !important; color:var(--eau) !important; background:var(--tint-eau) !important; transform:translateY(-1px); }
[data-testid^="stBaseButton"]:active { transform:translateY(1px); }
[data-testid^="stBaseButton"]:disabled { opacity:.4; transform:none !important; }
[data-testid="stWidgetLabel"] p { font-size:13px !important; font-weight:600 !important; color:var(--encre) !important; opacity:.85; margin-bottom:.1rem !important; }
[data-baseweb="input"] input, [data-baseweb="select"] > div, [data-baseweb="datepicker"] input, textarea { padding:.35rem .6rem !important; font-size:14px !important; transition:border-color .15s ease, background .15s ease; }
[data-baseweb="select"] > div:hover { border-color:var(--eau) !important; }
[data-testid="stExpander"] { border:1px solid var(--craie) !important; border-radius:var(--radius-sm) !important; background:var(--card) !important; box-shadow:var(--shadow); margin:.3rem 0; transition:box-shadow .15s ease; }
[data-testid="stExpander"]:hover { box-shadow:var(--shadow-hover); }
[data-testid="stDataFrame"] { border:1px solid var(--craie); border-radius:var(--radius-sm); overflow:hidden; }
.confidence-banner { border:1px solid var(--craie); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.55rem .8rem; margin:.3rem 0 .6rem; }
.eyebrow { font-size:11px; letter-spacing:.09em; font-weight:600; opacity:.65; }
.final-warning { border-top:1px solid var(--craie); margin-top:.8rem; padding:.6rem 0; max-width:900px; }
.final-warning p { margin:.3rem 0; }
.section-kicker { font-size:12px; letter-spacing:.1em; font-weight:600; }
.section-kicker::before, .article-divider span::before, .expert-divider > span::before, .report-section-kicker::before { content:""; display:inline-block; width:6px; height:6px; border-radius:50%; background:currentColor; margin-right:.4em; opacity:.8; vertical-align:middle; }
.soil-compact,.parcel-line { display:flex; gap:1.2rem; row-gap:.3rem; flex-wrap:wrap; align-items:baseline; padding:.55rem 0; }.soil-compact span,.parcel-line span { padding-right:1.2rem; border-right:1px solid var(--craie); }.soil-compact span:last-child,.parcel-line span:last-child { border-right:none; padding-right:0; }.soil-compact b,.parcel-line span { font-family:ui-monospace,monospace; }
.soil-compact { border-top:1px solid var(--craie); margin:.5rem 0 0; color:var(--encre); opacity:.9; font-size:13.5px; }
.om-soil-card { border:1px solid var(--craie); border-left:3px solid var(--eau); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.85rem 1.05rem; margin:.6rem 0; }
.om-soil-kicker { font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--eau); margin-bottom:.6rem; }
.om-soil-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; }
.om-soil-grid span { display:block; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.03em; opacity:.55; margin-bottom:3px; }
.om-soil-grid strong { font-size:16px; font-weight:600; font-family:"IBM Plex Mono",monospace; }
.om-soil-grid strong.lvl-haute { color:var(--sur); }
.om-soil-grid strong.lvl-moyenne, .om-soil-grid strong.lvl-faible { color:var(--vigilance); }
.parcel-line { border-top:1px solid var(--craie); border-bottom:2px solid var(--encre); margin:.5rem 0 .7rem; font-size:15px; }
.datahub-banner { display:flex; gap:.7rem; align-items:flex-start; border:1px solid var(--craie); border-left:4px solid var(--sur); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.7rem .9rem; margin:.3rem 0 .8rem; }
.datahub-banner .datahub-dot { width:9px; height:9px; border-radius:50%; margin-top:.45rem; flex:none; background:var(--sur); }
.datahub-banner.datahub-off { border-left-color:var(--vigilance); }.datahub-banner.datahub-off .datahub-dot { background:var(--vigilance); }
.datahub-banner strong { font-size:13px; display:block; }
.datahub-banner p { font-size:12px; margin:2px 0 0; opacity:.78; }
.datahub-banner code { font-size:11px; }
.datahub-src { display:flex; flex-wrap:wrap; gap:.35rem .7rem; margin-top:.45rem; font-size:11.5px; opacity:.9; }.datahub-src > div { display:flex; gap:.35rem; }.datahub-src b { font-variant-numeric:tabular-nums; }
.waiting-story { min-height:110px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; border:1px solid var(--craie); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); margin-top:.6rem; padding:.6rem; }.waiting-story strong { font:600 18px "IBM Plex Serif",Georgia,serif; }.waiting-story p { max-width:560px; font-size:13.5px; }
.article-divider { border-top:2px solid var(--encre); margin:.7rem 0 .4rem; padding-top:.25rem; }.article-divider span { font-size:12px; letter-spacing:.12em; font-weight:600; }
.sentinel-box { border:1px solid var(--craie); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); margin-top:.7rem; padding:.7rem .9rem; }
.expert-heading { display:flex; align-items:center; gap:1.5rem; border:1px solid var(--craie); border-left:4px solid var(--eau); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.6rem .8rem; margin:.3rem 0 .6rem; }.expert-heading span { display:block; font-size:11px; letter-spacing:.08em; }.expert-heading strong { font:500 22px ui-monospace,monospace; }.expert-heading p { max-width:620px; margin:0; }
.expert-divider { border-top:2px solid var(--eau); margin:.8rem 0 .5rem; padding-top:.4rem; }.expert-divider > span { font-size:12px; letter-spacing:.1em; color:var(--eau); }.expert-divider h2 { margin:.1rem 0; }.expert-divider p { margin:.1rem 0; }
.failure-flow { display:flex; align-items:center; gap:.6rem; flex-wrap:wrap; margin:.5rem 0; }.failure-flow span { border:1px solid var(--craie); border-left:4px solid var(--rupture); border-radius:var(--radius-sm); background:var(--card); box-shadow:var(--shadow); padding:.5rem .65rem; }.failure-flow b { font-family:ui-monospace,monospace; }.failure-flow small { font-size:11px; }
.trust-banner { display:flex; align-items:center; justify-content:space-between; gap:1rem; border:1px solid var(--craie); border-left:5px solid var(--sur); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.6rem .9rem; margin:.3rem 0 .6rem; }.trust-banner span { display:block; font-size:12px; letter-spacing:.08em; }.trust-banner strong { font:600 16px "IBM Plex Serif",Georgia,serif; }.trust-banner p { margin:.2rem 0 0; }.trust-seal { min-width:80px; text-align:center; color:var(--sur); font:600 22px ui-monospace,monospace; }.trust-seal small { display:block; font:11px system-ui; }
.quality-list { display:grid; grid-template-columns:repeat(2,1fr); gap:.6rem; }.quality-list > div { border:1px solid var(--craie); border-left:4px solid; border-radius:var(--radius-sm); background:var(--card); box-shadow:var(--shadow); padding:.6rem .8rem; }.quality-list span,.quality-list b,.quality-list small { display:block; }.quality-list b { font-size:13px; }.quality-elevee{border-color:var(--sur)}.quality-moyenne{border-color:var(--vigilance)}.quality-faible,.quality-insuffisante{border-color:var(--rupture)}
.confidence-title { border:1px solid var(--craie); border-left:4px solid var(--eau); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.7rem 1rem; margin:.4rem 0 .8rem; }.confidence-title > span { display:block; font-size:12px; letter-spacing:.08em; }.confidence-title > strong { display:block; font:600 22px "IBM Plex Serif",Georgia,serif; }.confidence-title p { margin:.2rem 0; }
.confidence-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:.6rem; }.confidence-component { border-top:4px solid; border-radius:0 0 var(--radius-sm) var(--radius-sm); background:var(--card); box-shadow:var(--shadow); padding:.7rem .5rem; }.confidence-component span,.confidence-component strong,.confidence-component small { display:block; }.confidence-component strong { font-size:16px; margin:.2rem 0; }.confidence-component small { color:var(--encre); line-height:1.35; }
.level-élevée { color:var(--sur); border-color:var(--sur); }.level-moyenne { color:var(--vigilance); border-color:var(--vigilance); }.level-faible { color:var(--rupture); border-color:var(--rupture); }
.confidence-component span { color:var(--encre); }.confidence-actions { border:1px solid var(--craie); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.8rem 1rem; margin:.8rem 0; }.confidence-actions ol { margin:.5rem 0; padding-left:1.3rem; }.confidence-actions p { margin:.5rem 0 0; font-size:13px; }
.confidence-banner.degradee { border-left:4px solid var(--vigilance); }
.confidence-banner.insuffisante { border-left:4px solid var(--rupture); }
.stTabs [data-baseweb="tab-list"] { gap:.5rem; border-bottom:1px solid var(--craie); }
.stTabs [data-baseweb="tab"] { padding:.6rem .9rem; background:transparent; }
button, input, select, [data-baseweb="select"] > div { border-radius:var(--radius-sm) !important; box-shadow:none !important; }
*:focus-visible { outline:3px solid var(--eau) !important; outline-offset:2px; }
button[kind="primary"], [data-testid="stBaseButton-primary"] { background:var(--encre) !important; border-color:var(--encre) !important; color:var(--papier) !important; box-shadow:0 2px 10px rgba(31,42,36,.18); }
button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background:var(--eau) !important; border-color:var(--eau) !important; color:var(--papier) !important; transform:translateY(-1px); box-shadow:0 4px 14px rgba(46,111,142,.28); }
button[kind="primary"] p, [data-testid="stBaseButton-primary"] p { color:var(--papier) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"]:focus-within, [data-baseweb="datepicker"]:focus-within { outline:2px solid var(--eau); outline-offset:1px; }
.spine { border:1px solid var(--craie); border-left:3px solid var(--eau); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:1rem 1.1rem; position:sticky; top:1rem; }
.spine h2 { font:500 12px/1.4 ui-sans-serif,system-ui; letter-spacing:.08em; text-transform:uppercase; }
.spine-segment { border-bottom:1px solid var(--craie); padding:.5rem 0; animation:propagate .6s ease both; animation-delay:calc(var(--i) * 55ms); }
.spine-segment.risk { border-left:4px solid var(--rupture); padding-left:.55rem; color:var(--rupture); }
.dot { display:inline-block; width:.55rem; height:.55rem; border-radius:50%; margin-right:.35rem; background:var(--sur); }
.dot.vigilance { background:var(--vigilance); }.dot.rupture { background:var(--rupture); }
.urn { display:none; overflow-wrap:anywhere; font:11px/1.4 ui-monospace,monospace; }
@keyframes propagate { from { border-left-color:var(--eau); } to { border-left-color:var(--rupture); } }
@media (prefers-reduced-motion:reduce) { .spine-segment { animation:none !important; } }
@media (max-width:900px) { .block-container{padding:1rem .8rem}.spine{position:static;margin-top:1.5rem}.confidence-grid{grid-template-columns:1fr 1fr} }

/* Tableau de bord "Choisir sa culture" (Assolement.dc.html) */
.om-row:hover { background:#EFEEE9; }
[data-baseweb="button-group"] button { font-family:"IBM Plex Sans",sans-serif !important; font-size:13px !important; font-weight:500 !important; border-color:var(--craie) !important; }
[data-baseweb="button-group"] button[data-testid="stBaseButton-segmented_control"] { background:var(--papier) !important; color:var(--encre) !important; }
[data-baseweb="button-group"] button[data-testid="stBaseButton-segmented_controlActive"] { background:var(--encre) !important; color:var(--papier) !important; border-color:var(--encre) !important; }
[data-baseweb="button-group"] button[data-testid="stBaseButton-segmented_controlActive"] p { color:var(--papier) !important; }
.assolement-spine .spine { border-left:none; padding-left:0; position:static; }
.assolement-spine .spine h2 { display:none; }
.assolement-spine { border:1px solid var(--craie); border-left:3px solid var(--eau); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.9rem 1rem; position:sticky; top:1rem; }
.assolement-spine .spine { border:none; box-shadow:none; padding:0; background:transparent; }

/* Sous-section "Rapport" */
.report-section { border:1px solid var(--craie); border-left:3px solid var(--sur); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.9rem 1.1rem; margin-top:.6rem; }
.report-section-kicker { font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--sur); margin-bottom:.5rem; }
.assolement-spine .report-section-kicker { color:var(--eau); }
.report-subhead { font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.02em; opacity:.55; margin:.8rem 0 .3rem; border-top:1px solid var(--craie); padding-top:.6rem; }

/* Scène météo réactive — tension eau = soleil qui tape, jamais la pluie */
.weather-hero { position:relative; overflow:hidden; border-radius:var(--radius); height:92px; margin:0 0 .6rem; background:linear-gradient(165deg,var(--sky-top) 0%,var(--sky-mid) 55%,var(--sky-bottom) 100%); box-shadow:var(--shadow); }
.weather-hero .sun { position:absolute; border-radius:50%; box-shadow:0 0 40px 10px rgba(255,222,122,.5); animation:sunPulse 6s ease-in-out infinite; }
.weather-hero .sun.chaud { box-shadow:0 0 46px 14px rgba(255,155,74,.55); }
.weather-hero .sun .heat-line { position:absolute; bottom:-16px; width:2px; height:10px; background:rgba(255,155,74,.65); border-radius:1px; animation:heatRise 1.4s ease-in-out infinite; }
.weather-hero .sun .heat-line:first-child { left:14px; }
.weather-hero .sun .heat-line:last-child { left:28px; animation-delay:.5s; }
.weather-hero .cloud { position:absolute; background:#FFFFFF; opacity:.92; border-radius:40px; animation:cloudDrift linear infinite; }
.weather-hero .drop { position:absolute; width:2px; top:-10%; background:rgba(255,255,255,.7); border-radius:1px; animation:rainFall linear infinite; }
.weather-hero .flash { position:absolute; inset:0; background:#fff; opacity:0; animation:lightning 2.4s ease-in-out infinite; }
.weather-hero .hero-title { position:absolute; left:1.1rem; bottom:.6rem; }
.weather-hero .hero-title .eyebrow { color:#fff; opacity:.92; text-shadow:0 1px 6px rgba(0,0,0,.25); }
.weather-hero .hero-title h1 { color:#fff; margin:.1rem 0 0; font-size:18px; text-shadow:0 1px 6px rgba(0,0,0,.25); }
@keyframes sunPulse { 0%,100% { transform:scale(1); } 50% { transform:scale(1.06); } }
@keyframes heatRise { 0% { transform:translateY(0); opacity:.7; } 100% { transform:translateY(-14px); opacity:0; } }
@keyframes cloudDrift { from { transform:translateX(-20%); } to { transform:translateX(340%); } }
@keyframes rainFall { from { transform:translateY(0); opacity:.9; } to { transform:translateY(160px); opacity:.15; } }
@keyframes lightning { 0%,92%,100% { opacity:0; } 94% { opacity:.55; } 96% { opacity:0; } }

.crop-badge { display:inline-flex; align-items:center; gap:3px; margin-left:8px; vertical-align:middle; }
.crop-badge .mini-sun, .frise-sun { width:11px; height:11px; border-radius:50%; display:inline-block; }
.crop-badge .mini-sun.calme, .frise-sun.calme { background:#FFDE7A; box-shadow:0 0 6px 2px rgba(255,222,122,.4); }
.crop-badge .mini-sun.voile, .frise-sun.voile { background:#F2C879; opacity:.8; }
.crop-badge .mini-sun.chaud, .frise-sun.chaud { background:#FF9B4A; box-shadow:0 0 6px 2px rgba(255,155,74,.5); }

.grass-band { position:relative; height:26px; margin:.7rem 0 .5rem; overflow:hidden; }
.grass-band .blade { position:absolute; bottom:0; width:3px; background:var(--grass); border-radius:3px 3px 0 0; transform-origin:bottom; animation:growBlade .6s ease-out both; }
@keyframes growBlade { from { transform:scaleY(0); } to { transform:scaleY(1); } }

/* Indicateur d'étapes */
.step-indicator { display:flex; align-items:center; margin:0 0 .7rem; flex-wrap:wrap; background:var(--card); border:1px solid var(--craie); border-radius:999px; padding:.4rem .9rem; box-shadow:var(--shadow); width:fit-content; }
.step-item { display:flex; align-items:center; gap:.45rem; opacity:.5; transition:opacity .2s ease; }
.step-item.active, .step-item.done { opacity:1; }
.step-dot { width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font:600 11px ui-monospace,monospace; background:var(--craie); color:var(--encre); flex:none; transition:background .2s ease, transform .2s ease; }
.step-item.active .step-dot { background:var(--eau); color:#fff; transform:scale(1.08); box-shadow:0 0 0 4px var(--tint-eau); }
.step-item.done .step-dot { background:var(--sur); color:#fff; }
.step-label { font-size:12.5px; font-weight:500; white-space:nowrap; }
.step-item.active .step-label { font-weight:600; }
.step-sep { width:26px; height:2px; background:var(--craie); margin:0 .5rem; border-radius:1px; }
.step-sep.done { background:var(--sur); }

/* Frise du scénario météo */
.frise { margin:0 0 .7rem; }
.frise-crop { font:600 14px "IBM Plex Serif",serif; margin-bottom:.25rem; }
.frise-track { position:relative; display:flex; border:1px solid var(--craie); border-radius:var(--radius-sm); background:var(--card); box-shadow:var(--shadow); padding:.5rem .4rem 1.3rem; overflow:hidden; }
.frise-month { flex:1; display:flex; flex-direction:column; align-items:center; gap:.3rem; padding:0 .2rem; }
.frise-month.critical { background:rgba(166,61,47,.07); border-radius:6px; }
.frise-label { font:500 10px ui-monospace,monospace; opacity:.65; }
.frise-cursor { position:absolute; top:0; bottom:0; width:2px; background:var(--eau); left:0; animation-name:frisePlay; animation-timing-function:linear; animation-fill-mode:forwards; }
.frise-risk { position:absolute; bottom:2px; transform:translateX(-50%); font-size:11px; font-weight:600; color:var(--rupture); white-space:nowrap; }
@keyframes frisePlay { from { left:0%; } to { left:100%; } }

[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid var(--craie) !important; border-radius:var(--radius) !important; background:var(--card) !important; box-shadow:var(--shadow) !important; }

/* Tunnel interne "Choisir sa culture" (Assolement.dc.html) */
.om-tunnel-header { max-width:760px; margin:0 auto .7rem; }
.om-tunnel-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
.om-tunnel-title-row h1 { margin:0; }
.om-step-count { font-family:"IBM Plex Mono",monospace; font-size:13px; opacity:.55; }
.om-progress { display:flex; gap:4px; }
.om-progress-seg { flex:1; height:3px; border-radius:2px; background:var(--craie); transition:background .3s ease; }
.om-progress-seg.done { background:var(--encre); }
.om-kicker { font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.03em; opacity:.55; margin-bottom:10px; }
.st-key-om_screen { max-width:760px; margin:0 auto; animation:omFadeUp .4s ease; }
.st-key-om_screen .om-row { margin:0 !important; }
.st-key-om_screen [data-testid="stSelectbox"] [data-baseweb="select"] > div { font-size:16px !important; min-height:46px; }
.st-key-om_screen [data-testid="stSelectbox"] [role="option"] { font-size:16px !important; }
.st-key-om_screen > [data-testid="stElementContainer"] + [data-testid="stElementContainer"],
.st-key-om_wide > [data-testid="stElementContainer"] + [data-testid="stElementContainer"] { margin-top:.95rem; }
.st-key-om_screen [data-testid="stExpander"] { margin:.95rem 0 .3rem; }
.st-key-om_screen [data-testid="stExpander"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] + [data-testid="stElementContainer"] { margin-top:.8rem; }
@keyframes omFadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.assolement-spine-full .spine { border:none; box-shadow:none; padding:0; position:static; }
.assolement-spine-full .spine h2 { display:none; }

@media (prefers-reduced-motion:reduce) {
  .weather-hero .sun, .weather-hero .cloud, .weather-hero .drop, .weather-hero .flash, .weather-hero .sun .heat-line,
  .grass-band .blade, .frise-cursor { animation:none !important; }
  .grass-band .blade { transform:scaleY(1); }
  .frise-cursor { left:100%; }
  .st-key-om_screen { animation:none !important; }
}
</style>
"""
