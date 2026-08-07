"""Feuille de style locale conforme au brief."""

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Serif:wght@600&display=swap');
:root {
  --papier:#F4F6F2; --encre:#1A231D; --craie:#DEE2D9; --eau:#2B6C8F;
  --sur:#3F7A5A; --vigilance:#B9852A; --rupture:#A63D2F;
  --card:#FFFFFF; --radius:16px; --radius-sm:11px;
  --shadow:0 1px 2px rgba(15,23,20,.04), 0 8px 24px rgba(15,23,20,.06);
  --shadow-hover:0 2px 4px rgba(15,23,20,.05), 0 14px 32px rgba(15,23,20,.10);
  --shadow-md:0 2px 6px rgba(15,23,20,.05), 0 12px 28px rgba(15,23,20,.08);
  --tint-eau:rgba(43,108,143,.07); --tint-sur:rgba(63,122,90,.07);
  --sky-top:#4A90D9; --sky-mid:#8FB8D8; --sky-bottom:#FFD37A; --grass:#3F7A5A; --grass-dark:#2E5940;
}
html, body, [class*="st-"] { font-family: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, sans-serif; color:var(--encre); line-height:1.45; }
.stMain, .stMainBlockContainer, .report-section, .report-subhead { overflow-anchor:none; }
.stApp { background:
  radial-gradient(1100px 480px at 85% -8%, rgba(43,108,143,.07), transparent 60%),
  radial-gradient(900px 420px at -10% 12%, rgba(63,122,90,.06), transparent 55%),
  var(--papier); }
h1, h2 { font-family:"IBM Plex Serif", Georgia, serif; font-weight:600; letter-spacing:-.01em; }
h1 { font-size:23px; }
h2 { font-size:17.5px; }
p, .stMarkdown p { line-height:1.5; }
code, pre, time, .mono, [data-testid="stMetricValue"], td { font-family:"IBM Plex Mono", ui-monospace, SFMono-Regular, Consolas, monospace !important; }
.block-container { max-width:1500px; padding:.9rem 1.6rem 1.3rem; }
[data-testid="stVerticalBlock"] { gap:.35rem; }
[data-testid^="stBaseButton"] { padding:.45rem 1rem !important; font-size:13.5px !important; font-weight:500 !important; border-radius:12px !important; transition:background .15s ease, border-color .15s ease, color .15s ease, transform .12s ease, box-shadow .15s ease; }
[data-testid^="stBaseButton"]:not([kind="primary"]) { background:var(--card) !important; border:1px solid var(--craie) !important; color:var(--encre) !important; }
[data-testid^="stBaseButton"]:not([kind="primary"]):hover { border-color:var(--eau) !important; color:var(--eau) !important; background:var(--tint-eau) !important; transform:translateY(-1px); box-shadow:var(--shadow-md); }
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
.final-warning a { color:var(--eau); font-size:13.5px; font-weight:500; margin-top:.45rem; display:inline-flex; }
.section-kicker { font-size:12px; letter-spacing:.1em; font-weight:600; }
.section-kicker::before, .article-divider span::before, .expert-divider > span::before, .report-section-kicker::before { content:""; display:inline-block; width:6px; height:6px; border-radius:50%; background:currentColor; margin-right:.4em; opacity:.8; vertical-align:middle; }
.soil-compact,.parcel-line { display:flex; gap:1.2rem; row-gap:.3rem; flex-wrap:wrap; align-items:baseline; padding:.55rem 0; }.soil-compact span,.parcel-line span { padding-right:1.2rem; border-right:1px solid var(--craie); }.soil-compact span:last-child,.parcel-line span:last-child { border-right:none; padding-right:0; }.soil-compact b,.parcel-line span { font-family:ui-monospace,monospace; }
.soil-compact { border-top:1px solid var(--craie); margin:.5rem 0 0; color:var(--encre); opacity:.9; font-size:13.5px; }
.om-soil-card { border:1px solid var(--craie); border-left:3px solid var(--eau); border-radius:var(--radius); background:var(--card); box-shadow:var(--shadow); padding:.9rem 1.1rem; margin:.6rem 0; transition:box-shadow .18s ease, transform .18s ease; }
.om-soil-card:hover { box-shadow:var(--shadow-hover); }
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
/* Cascade de panne cinématique — propagation séquentielle le long du lineage */
.failure-cascade { margin:.4rem 0; }
.cascade-impact {
  display: flex;
  align-items: baseline;
  gap: .35rem;
  font-size: 12.5px;
  letter-spacing: .04em;
  color: var(--rupture);
  font-weight: 600;
  margin-bottom: .35rem;
}
.cascade-impact b { font: 600 20px ui-monospace, monospace; }
.cascade-node,
.cascade-arrow {
  opacity: 0;
  animation: cascadeIn 520ms var(--anim-ease-out) calc(var(--fc-i) * 560ms) forwards;
}
@keyframes cascadeIn {
  0%   { opacity: 0; transform: translateX(-14px) scale(.92); }
  25%  { opacity: 1; transform: none; box-shadow: 0 0 0 5px rgb(220 38 38 / .22); }
  100% { opacity: 1; transform: none; box-shadow: var(--shadow); }
}
.trust-banner { display:flex; align-items:center; justify-content:space-between; gap:1rem; border:1px solid var(--craie); border-left:5px solid var(--sur); border-radius:var(--radius); background:linear-gradient(180deg,var(--card),#FBFCF9); box-shadow:var(--shadow); padding:.7rem 1rem; margin:.3rem 0 .6rem; }.trust-banner span { display:block; font-size:12px; letter-spacing:.08em; }.trust-banner strong { font:600 16px "IBM Plex Serif",Georgia,serif; }.trust-banner p { margin:.2rem 0 0; }.trust-seal { min-width:80px; text-align:center; color:var(--sur); font:600 22px ui-monospace,monospace; }.trust-seal small { display:block; font:11px system-ui; }
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
button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background:var(--eau) !important; border-color:var(--eau) !important; color:#fff !important; transform:translateY(-1px); box-shadow:0 4px 14px rgba(46,111,142,.28); }
button[kind="primary"] p, [data-testid="stBaseButton-primary"] p { color:var(--papier) !important; }
button[kind="primary"]:hover p, [data-testid="stBaseButton-primary"]:hover p { color:#fff !important; }
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
.weather-hero { position:relative; overflow:hidden; border-radius:var(--radius); height:118px; margin:0 0 .7rem; background:linear-gradient(168deg,var(--sky-top) 0%,var(--sky-mid) 52%,var(--sky-bottom) 100%); box-shadow:var(--shadow-md); }
.weather-hero::after { content:""; position:absolute; inset:0; background:linear-gradient(180deg,rgba(20,40,60,.08),transparent 55%,rgba(20,40,60,.16)); }
.weather-hero .sun { position:absolute; border-radius:50%; box-shadow:0 0 40px 10px rgba(255,222,122,.5); animation:sunPulse 6s ease-in-out infinite; }
.weather-hero .sun.chaud { box-shadow:0 0 46px 14px rgba(255,155,74,.55); }
.weather-hero .sun .heat-line { position:absolute; bottom:-16px; width:2px; height:10px; background:rgba(255,155,74,.65); border-radius:1px; animation:heatRise 1.4s ease-in-out infinite; }
.weather-hero .sun .heat-line:first-child { left:14px; }
.weather-hero .sun .heat-line:last-child { left:28px; animation-delay:.5s; }
.weather-hero .cloud { position:absolute; background:#FFFFFF; opacity:.92; border-radius:40px; animation:cloudDrift linear infinite; }
.weather-hero .drop { position:absolute; width:2px; top:-10%; background:rgba(255,255,255,.7); border-radius:1px; animation:rainFall linear infinite; }
.weather-hero .flash { position:absolute; inset:0; background:#fff; opacity:0; animation:lightning 2.4s ease-in-out infinite; }
.weather-hero .hero-title { position:absolute; left:1.3rem; bottom:.8rem; z-index:1; }
.weather-hero .hero-title .eyebrow { color:#fff; opacity:.94; text-shadow:0 1px 6px rgba(0,0,0,.25); }
.weather-hero .hero-title h1 { color:#fff; margin:.15rem 0 0; font-size:21px; text-shadow:0 1px 6px rgba(0,0,0,.28); }
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
.step-indicator { display:flex; align-items:center; margin:0 0 .8rem; flex-wrap:wrap; background:var(--card); border:1px solid var(--craie); border-radius:999px; padding:.45rem .95rem; box-shadow:var(--shadow); width:fit-content; gap:.15rem; }
.step-item { display:flex; align-items:center; gap:.45rem; opacity:.55; transition:opacity .2s ease; }
.step-item.active, .step-item.done { opacity:1; }
.step-dot { width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font:600 11px ui-monospace,monospace; background:var(--craie); color:var(--encre); flex:none; transition:background .2s ease, transform .2s ease; }
.step-item.active .step-dot { background:var(--eau); color:#fff; transform:scale(1.08); box-shadow:0 0 0 5px var(--tint-eau); }
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

/* ============================================================================
   ANIMATION SYSTEM — 15 Animation Primitives
   Applied via utility classes on st.markdown containers
   ============================================================================ */

:root {
  --anim-duration-fast: 200ms;
  --anim-duration-base: 400ms;
  --anim-duration-slow: 700ms;
  --anim-ease: cubic-bezier(0.16, 1, 0.3, 1);
  --anim-ease-out: cubic-bezier(0, 0, 0.2, 1);
  --anim-ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* 1. Masked Text Reveal — text appears through a moving mask */
@keyframes maskReveal {
  from { clip-path: inset(0 100% 0 0); }
  to { clip-path: inset(0 0 0 0); }
}
.animate-mask-reveal {
  display: inline-block;
  animation: maskReveal var(--anim-duration-slow) var(--anim-ease-out) both;
}
.animate-mask-reveal-delay-1 { animation-delay: 100ms; }
.animate-mask-reveal-delay-2 { animation-delay: 200ms; }
.animate-mask-reveal-delay-3 { animation-delay: 300ms; }

/* 2. Split-line Text Reveal — lines slide up from below */
@keyframes splitLineReveal {
  from { transform: translateY(110%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.animate-split-line {
  overflow: hidden;
}
.animate-split-line > * {
  display: block;
  animation: splitLineReveal var(--anim-duration-slow) var(--anim-ease-out) both;
}
.animate-split-line > *:nth-child(1) { animation-delay: 0ms; }
.animate-split-line > *:nth-child(2) { animation-delay: 80ms; }
.animate-split-line > *:nth-child(3) { animation-delay: 160ms; }
.animate-split-line > *:nth-child(4) { animation-delay: 240ms; }
.animate-split-line > *:nth-child(5) { animation-delay: 320ms; }

/* 3. Fade-up on Scroll (IntersectionObserver via JS) */
.animate-fade-up {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity var(--anim-duration-base) var(--anim-ease-out),
              transform var(--anim-duration-base) var(--anim-ease-out);
}
.animate-fade-up.is-visible {
  opacity: 1;
  transform: translateY(0);
}
.animate-fade-up-delay-1 { transition-delay: 100ms; }
.animate-fade-up-delay-2 { transition-delay: 200ms; }
.animate-fade-up-delay-3 { transition-delay: 300ms; }
.animate-fade-up-delay-4 { transition-delay: 400ms; }

/* 11. Animated Underline — soulignement animé au survol des intitulés de section */
.om-kicker,
.report-section-kicker,
.section-kicker,
.eyebrow {
  position: relative;
}
.om-kicker::after,
.report-section-kicker::after,
.section-kicker::after,
.eyebrow::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -3px;
  width: 0;
  height: 2px;
  background: currentColor;
  opacity: .7;
  transition: width var(--anim-duration-base) var(--anim-ease),
              left var(--anim-duration-base) var(--anim-ease);
}
.om-kicker:hover::after,
.report-section-kicker:hover::after,
.section-kicker:hover::after,
.eyebrow:hover::after {
  width: 100%;
  left: 0;
}

/* 4. Staggered Scroll Reveal — children animate in sequence */
.animate-stagger > * {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity var(--anim-duration-base) var(--anim-ease-out),
              transform var(--anim-duration-base) var(--anim-ease-out);
}
.animate-stagger.is-visible > *:nth-child(1)  { transition-delay: 0ms;   }
.animate-stagger.is-visible > *:nth-child(2)  { transition-delay: 60ms;  }
.animate-stagger.is-visible > *:nth-child(3)  { transition-delay: 120ms; }
.animate-stagger.is-visible > *:nth-child(4)  { transition-delay: 180ms; }
.animate-stagger.is-visible > *:nth-child(5)  { transition-delay: 240ms; }
.animate-stagger.is-visible > *:nth-child(6)  { transition-delay: 300ms; }
.animate-stagger.is-visible > *:nth-child(7)  { transition-delay: 360ms; }
.animate-stagger.is-visible > *:nth-child(8)  { transition-delay: 420ms; }
.animate-stagger.is-visible > * {
  opacity: 1;
  transform: translateY(0);
}

/* 5. Vertical Image Mask Reveal — image uncovered top to bottom */
@keyframes verticalMaskReveal {
  from { clip-path: polygon(0 100%, 100% 100%, 100% 100%, 0 100%); }
  to { clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%); }
}
.animate-vertical-mask {
  overflow: hidden;
}
.animate-vertical-mask > img,
.animate-vertical-mask > .image-wrapper,
.animate-vertical-mask > * {
  animation: verticalMaskReveal var(--anim-duration-slow) var(--anim-ease-out) both;
}

/* 6. Image Scale-down Reveal — zoom out from 1.15x to 1x */
@keyframes scaleDownReveal {
  from { transform: scale(1.15); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.animate-scale-down {
  overflow: hidden;
}
.animate-scale-down > img,
.animate-scale-down > .image-wrapper,
.animate-scale-down > * {
  animation: scaleDownReveal 1s var(--anim-ease-out) both;
}

/* 7. Subtle Image Parallax — slight translate on scroll */
.parallax-container {
  overflow: hidden;
}
.parallax-image {
  transition: transform 0.1s linear;
  will-change: transform;
}

/* 8. Image Zoom on Hover — gentle scale on hover */
.animate-zoom-hover {
  overflow: hidden;
}
.animate-zoom-hover > img,
.animate-zoom-hover > .image-wrapper,
.animate-zoom-hover > * {
  transition: transform var(--anim-duration-slow) var(--anim-ease);
}
.animate-zoom-hover:hover > img,
.animate-zoom-hover:hover > .image-wrapper,
.animate-zoom-hover:hover > * {
  transform: scale(1.04);
}

/* 9. Card Hover Micro-interaction — lift + shadow + border */
.animate-card-hover {
  transition: transform var(--anim-duration-fast) var(--anim-ease),
              box-shadow var(--anim-duration-fast) var(--anim-ease),
              border-color var(--anim-duration-fast) var(--anim-ease);
}
.animate-card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(15,23,20,.12), 0 4px 16px rgba(15,23,20,.08);
  border-color: var(--eau);
}

/* 10. Arrow Slide on Hover — icon slides right */
.animate-arrow-slide {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.animate-arrow-slide .arrow {
  transition: transform var(--anim-duration-fast) var(--anim-ease);
}
.animate-arrow-slide:hover .arrow {
  transform: translateX(6px);
}

/* 11. Animated Underline — expands from center */
.animated-underline {
  position: relative;
  text-decoration: none;
}
.animated-underline::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 50%;
  width: 0;
  height: 2px;
  background: currentColor;
  transition: width var(--anim-duration-base) var(--anim-ease),
              left var(--anim-duration-base) var(--anim-ease);
}
.animated-underline:hover::after {
  width: 100%;
  left: 0;
}

/* 12. Horizontal Divider Reveal — line draws from center */
@keyframes dividerReveal {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
.animate-divider {
  position: relative;
  overflow: hidden;
}
.animate-divider::before {
  content: "";
  display: block;
  height: 1px;
  background: currentColor;
  transform-origin: center;
  animation: dividerReveal var(--anim-duration-slow) var(--anim-ease-out) both;
}

/* 13. Count-up Animation — numbers count up (JS, déclenché à l'intersection) */
.animate-count-up {
  opacity: 0;
  transition: opacity var(--anim-duration-base) var(--anim-ease);
}
.animate-count-up.counting {
  opacity: 1;
}

/* 14. Page-load Intro Sequence — orchestrates multiple animations */
.page-intro {
  opacity: 0;
  animation: pageIntro var(--anim-duration-slow) var(--anim-ease-out) forwards;
}
@keyframes pageIntro {
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
}
.page-intro > *:nth-child(1) { animation: maskReveal 600ms var(--anim-ease-out) 100ms both; }
.page-intro > *:nth-child(2) { animation: maskReveal 600ms var(--anim-ease-out) 200ms both; }
.page-intro > *:nth-child(3) { animation: maskReveal 600ms var(--anim-ease-out) 300ms both; }
.page-intro > *:nth-child(4) { animation: maskReveal 600ms var(--anim-ease-out) 400ms both; }

/* 12. Horizontal Divider Reveal — line draws from center (revoir l'espacement) */
.animate-divider {
  margin: .7rem 0;
}

/* 15. Smooth Page Fade Transition — for multi-step flows */
.page-transition-enter {
  opacity: 0;
  transform: translateX(20px);
  will-change: opacity, transform;
}
.page-transition-enter-active {
  opacity: 1;
  transform: translateX(0);
  transition: opacity var(--anim-duration-base) var(--anim-ease),
              transform var(--anim-duration-base) var(--anim-ease);
}
.page-transition-exit {
  opacity: 1;
  transform: translateX(0);
}
.page-transition-exit-active {
  opacity: 0;
  transform: translateX(-20px);
  transition: opacity var(--anim-duration-fast) var(--anim-ease),
              transform var(--anim-duration-fast) var(--anim-ease);
}

/* Graphe de lineage — DAG animé des sources vers la décision */
.lineage {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 600ms var(--anim-ease-out),
              transform 600ms var(--anim-ease-out);
}
.lineage.is-visible {
  opacity: 1;
  transform: none;
}
.lineage-stage {
  position: relative;
  aspect-ratio: var(--lg-ratio, 5 / 3);
  margin: .3rem 0;
}
.lineage-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.lineage-edge {
  fill: none;
  stroke: var(--craie);
  stroke-width: 2;
  stroke-dasharray: 7 7;
  animation: lineageFlow 1.6s linear infinite;
}
.lineage-edge:nth-of-type(2n) { animation-delay: .4s; }
.lineage-edge:nth-of-type(3n) { animation-delay: .8s; }
@keyframes lineageFlow {
  to { stroke-dashoffset: -14; }
}
.lineage-node {
  position: absolute;
  display: flex;
  flex-direction: column;
  gap: 2px;
  box-sizing: border-box;
  border: 1px solid var(--craie);
  border-left: 4px solid var(--craie);
  border-radius: var(--radius-sm);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: .4rem .55rem;
  text-decoration: none;
  color: var(--encre);
  opacity: 0;
  transform: translateY(14px) scale(.96);
  transition: opacity 450ms var(--anim-ease-out),
              transform 450ms var(--anim-ease-out),
              box-shadow 300ms var(--anim-ease);
  transition-delay: calc(var(--lg-i) * 90ms);
  z-index: 1;
}
.lineage.is-visible .lineage-node {
  opacity: 1;
  transform: none;
}
.lineage-node:hover {
  box-shadow: var(--shadow-lift, 0 8px 24px rgb(0 0 0 / .16));
  z-index: 2;
}
.lineage-node.ok { border-left-color: var(--sur); }
.lineage-node.stale { border-left-color: var(--rupture); }
.lineage-node.unknown { border-left-color: var(--craie); }
.lineage-dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--craie);
}
.lineage-node.ok .lineage-dot { background: var(--sur); }
.lineage-node.stale .lineage-dot { background: var(--rupture); }
.lineage-node.pulse .lineage-dot {
  animation: lineagePulse 1.6s ease-in-out infinite;
}
@keyframes lineagePulse {
  0%, 100% { box-shadow: 0 0 0 0 rgb(220 38 38 / .45); }
  50% { box-shadow: 0 0 0 7px rgb(220 38 38 / 0); }
}
.lineage-name {
  font: 600 12.5px "IBM Plex Serif", Georgia, serif;
  line-height: 1.2;
}
.lineage-proof {
  font-size: 10.5px;
  letter-spacing: .04em;
  color: var(--encre);
  opacity: .75;
}
.lineage-legend {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 11.5px;
  color: var(--encre);
  margin: .2rem 0 .5rem;
}
.lineage-legend i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: .3rem;
  background: var(--craie);
}
.lineage-legend.ok i { background: var(--sur); }
.lineage-legend.stale i { background: var(--rupture); }
.lineage-details {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(215px, 1fr));
  gap: .5rem;
  margin-top: .4rem;
}
.lineage-card {
  border: 1px solid var(--craie);
  border-radius: var(--radius-sm);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 0 .6rem;
}
.lineage-card summary {
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  padding: .55rem 0;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .5rem;
}
.lineage-card summary::-webkit-details-marker { display: none; }
.lineage-card summary::after {
  content: "＋";
  font-weight: 600;
  color: var(--eau);
  transition: transform 300ms var(--anim-ease);
}
.lineage-card[open] summary::after { transform: rotate(45deg); }
.lineage-card-layer {
  font-size: 10.5px;
  font-weight: 500;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--encre);
  opacity: .7;
  white-space: nowrap;
}
.lineage-card dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: .2rem .7rem;
  margin: 0 0 .55rem;
  font-size: 12px;
}
.lineage-card dt { opacity: .75; }
.lineage-card dd { margin: 0; text-align: right; }
.lineage-card a { scroll-margin-top: 90px; }

/* Console de supervision live de l'agent */
.supervision-console {
  border: 1px solid var(--craie);
  border-left: 4px solid var(--eau);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: .7rem .9rem;
  margin: .3rem 0 .6rem;
}
.console-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: .5rem;
  font-size: 11px;
  letter-spacing: .12em;
  font-weight: 600;
  color: var(--eau);
}
.console-head small {
  color: var(--encre);
  opacity: .6;
  letter-spacing: .05em;
  white-space: nowrap;
}
.console-steps {
  display: flex;
  flex-direction: column;
  gap: .45rem;
  margin-top: .55rem;
}
.console-step {
  display: flex;
  gap: .6rem;
  align-items: flex-start;
  border: 1px solid var(--craie);
  border-left: 4px solid var(--craie);
  border-radius: var(--radius-sm);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: .45rem .6rem;
  opacity: 0;
  transform: translateY(8px);
  animation: consoleIn 380ms var(--anim-ease-out) calc(var(--cs-i) * 160ms) forwards;
}
.console-step.ok { border-left-color: var(--sur); }
.console-step.warn { border-left-color: var(--vigilance); }
.console-step.action { border-left-color: var(--rupture); }
.console-step.ok .console-icon { color: var(--sur); }
.console-step.warn .console-icon { color: var(--vigilance); }
.console-step.action .console-icon { color: var(--rupture); }
.console-icon {
  font-weight: 700;
  line-height: 1.25;
  min-width: 14px;
}
.console-step b { display: block; font-size: 13px; }
.console-step small {
  display: block;
  color: var(--encre);
  opacity: .82;
  font-size: 12px;
  line-height: 1.4;
}
.console-time {
  margin-left: auto;
  font: 11px ui-monospace, monospace;
  color: var(--encre);
  opacity: .55;
  white-space: nowrap;
  padding-top: .15rem;
}
@keyframes consoleIn {
  to { opacity: 1; transform: none; }
}

/* Graphique lame d'eau : barres qui poussent en séquence */
.water-bar {
  transform-box: fill-box;
  transform-origin: bottom center;
  animation: waterGrow 700ms var(--anim-ease-out) calc(var(--wc-i) * 130ms) both;
}
@keyframes waterGrow {
  from { transform: scaleY(0); opacity: 0; }
  to { transform: scaleY(1); opacity: 1; }
}

/* Carte parcelle : parcelles RPG + stations d'eau */
.parcel-map {
  border: 1px solid var(--craie);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: .5rem .6rem;
  margin: .4rem 0;
}
.parcel-map svg polygon {
  transition: fill 300ms var(--anim-ease), opacity 300ms var(--anim-ease);
}
.parcel-map svg a:hover polygon {
  fill: var(--eau);
  opacity: 1;
}
.station-marker {
  transform-box: fill-box;
  transform-origin: center;
  animation: stationIn 520ms var(--anim-ease-out) calc(var(--st-i) * 140ms) both;
}
@keyframes stationIn {
  from { opacity: 0; transform: scale(.4); }
  to { opacity: 1; transform: scale(1); }
}
.parcel-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: .45rem;
  margin-top: .45rem;
}
.parcel-card {
  border: 1px solid var(--craie);
  border-radius: var(--radius-sm);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 0 .6rem;
}
.parcel-card[open] { border-left: 4px solid var(--eau); }
.parcel-card summary {
  cursor: pointer;
  font-weight: 600;
  font-size: 12.5px;
  padding: .5rem 0;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .5rem;
}
.parcel-card summary::-webkit-details-marker { display: none; }
.parcel-card summary::after {
  content: "＋";
  color: var(--eau);
  transition: transform 300ms var(--anim-ease);
}
.parcel-card[open] summary::after { transform: rotate(45deg); }
.parcel-card-area {
  font-size: 11px;
  font-weight: 500;
  color: var(--encre);
  opacity: .7;
  white-space: nowrap;
}
.parcel-card dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: .2rem .6rem;
  margin: 0 0 .5rem;
  font-size: 12px;
}
.parcel-card dt { opacity: .75; }
.parcel-card dd { margin: 0; text-align: right; }
.parcel-card a { scroll-margin-top: 90px; }

/* Tableau de bord KPI — Confiance, Produit, IA */
.kpi-dashboard { display:flex; flex-direction:column; gap:.7rem; margin:.4rem 0 .8rem; }
.kpi-group {
  border:1px solid var(--craie);
  border-top:3px solid var(--kpi-accent, var(--eau));
  border-radius:var(--radius);
  background:var(--card);
  box-shadow:var(--shadow);
  padding:.8rem .9rem .9rem;
}
.kpi-group-head { display:flex; align-items:flex-start; justify-content:space-between; gap:.6rem; margin-bottom:.6rem; }
.kpi-kicker { font-size:11px; font-weight:700; letter-spacing:.11em; text-transform:uppercase; color:var(--kpi-accent, var(--eau)); }
.kpi-group-head p { margin:.15rem 0 0; font-size:12.5px; opacity:.7; }
.kpi-group-badge { width:9px; height:9px; border-radius:50%; background:var(--kpi-accent, var(--eau)); margin-top:.4rem; box-shadow:0 0 0 5px color-mix(in srgb, var(--kpi-accent, var(--eau)) 15%, transparent); }
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(168px, 1fr)); gap:.55rem; }
.kpi-tile {
  position:relative;
  border:1px solid var(--craie);
  border-radius:var(--radius-sm);
  background:var(--card);
  box-shadow:var(--shadow);
  padding:.6rem .7rem .65rem .85rem;
  overflow:hidden;
  opacity:0;
  transform:translateY(14px) scale(.97);
  animation:kpiIn 480ms var(--anim-ease-out) calc(var(--kpi-i) * 90ms + var(--kpi-g) * 220ms) forwards;
}
.kpi-tile .kpi-label { display:block; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; opacity:.6; margin-bottom:.3rem; line-height:1.3; }
.kpi-value { display:flex; align-items:baseline; gap:.3rem; margin-bottom:.25rem; }
.kpi-value b { font:600 22px "IBM Plex Mono", ui-monospace, monospace; font-variant-numeric:tabular-nums; }
.kpi-value .kpi-unit { font:500 11px ui-monospace, monospace; opacity:.65; }
.kpi-static { color:var(--encre); }
.kpi-caption { display:block; font-size:11px; line-height:1.4; opacity:.72; }
.kpi-accent { position:absolute; left:0; top:.85rem; bottom:.85rem; width:3px; border-radius:2px; }
.kpi-tile.sur .kpi-value b { color:var(--sur); }
.kpi-tile.vigilance .kpi-value b { color:var(--vigilance); }
.kpi-tile.rupture .kpi-value b { color:var(--rupture); }
.kpi-tile.eau .kpi-value b { color:var(--eau); }
.kpi-tile:hover { box-shadow:var(--shadow-md); }
@keyframes kpiIn {
  from { opacity:0; transform:translateY(14px) scale(.97); }
  to { opacity:1; transform:none; }
}
.kpi-note { font-size:11px; opacity:.6; display:flex; gap:.4rem; align-items:center; letter-spacing:.02em; }
.kpi-note span { color:var(--eau); }

/* ============================================================================
   SITE VITRINE — navbar, hero, sections (format consilium-bsf.fr/vision)
   ============================================================================ */
.block-container { padding-top: 132px; }
.site-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 900;
  background: rgba(250, 251, 248, .92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--craie);
}
.site-navbar-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: .55rem 1.6rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.site-brand { display: flex; align-items: center; gap: .55rem; }
.site-brand-name {
  font: 600 15px "IBM Plex Serif", Georgia, serif;
  letter-spacing: .01em;
  white-space: nowrap;
}
.site-brand-name em { font-style: normal; color: var(--eau); }
.site-nav-dots { display: flex; gap: .2rem; flex-wrap: wrap; }
.site-nav-item {
  font-size: 13px;
  font-weight: 500;
  padding: .4rem .85rem;
  border-radius: 999px;
  color: var(--encre);
  opacity: .65;
  text-decoration: none;
  transition: background .15s ease, color .15s ease, opacity .15s ease;
}
.site-nav-item:hover { background: var(--tint-eau); color: var(--eau); opacity: 1; }
.site-nav-item.active { background: var(--encre); color: var(--papier); opacity: 1; }

/* Hero */
.site-hero { padding: 2.2rem 0 1.6rem; }
.site-hero-inner {
  display: grid;
  grid-template-columns: 1.05fr .95fr;
  gap: 2.4rem;
  align-items: center;
  max-width: 1280px;
  margin: 0 auto;
}
.site-eyebrow {
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: .14em;
  color: var(--eau);
  text-transform: uppercase;
  margin-bottom: .8rem;
}
.site-hero-title {
  font: 600 44px/1.12 "IBM Plex Serif", Georgia, serif;
  letter-spacing: -.02em;
  margin: 0 0 1rem;
  max-width: 620px;
}
.site-hero-title em { font-style: normal; color: var(--eau); }
.site-hero-lead {
  font-size: 16.5px;
  line-height: 1.6;
  opacity: .85;
  max-width: 560px;
  margin: 0 0 1.4rem;
}
.site-hero-cta { display: flex; gap: .7rem; flex-wrap: wrap; margin-bottom: 1.2rem; }

/* Hero de la vue Application : carte SVG à la place du collage photos */
.site-hero-card {
  border: 1px solid var(--craie);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 1rem;
}
.site-hero-card p {
  font-size: 12.5px;
  opacity: .75;
  margin: .6rem .2rem 0;
  line-height: 1.5;
}
.site-hero-app { padding-bottom: 2.4rem; }

/* En-têtes de section fonctionnelle (même grammaire que l'accueil) */
.site-section-head {
  max-width: 1280px;
  margin: 0 auto 1.2rem;
  padding-top: .4rem;
}
.site-section-head h2 {
  font: 600 30px/1.2 "IBM Plex Serif", Georgia, serif;
  margin: 0 0 .4rem;
}
.site-section-lead { font-size: 14.5px; opacity: .82; max-width: 760px; margin: 0; }

.site-btn {
  display: inline-block;
  padding: .7rem 1.4rem;
  border-radius: 12px;
  font-size: 14.5px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
}
.site-btn:hover { transform: translateY(-2px); }
.site-btn-primary { background: var(--encre); color: var(--papier); box-shadow: 0 4px 14px rgba(26,35,29,.2); }
.site-btn-primary:hover { background: var(--eau); color: #fff; box-shadow: 0 6px 18px rgba(43,108,143,.3); }
.site-btn-ghost { border: 1px solid var(--craie); background: var(--card); color: var(--encre); }
.site-btn-ghost:hover { border-color: var(--eau); color: var(--eau); box-shadow: var(--shadow-md); }
.site-btn-lg { padding: .85rem 1.7rem; font-size: 15.5px; }
.site-hero-chips { display: flex; gap: .55rem; flex-wrap: wrap; }
.site-chip {
  display: inline-flex;
  align-items: center;
  gap: .4rem;
  font-size: 12.5px;
  font-weight: 500;
  border: 1px solid var(--craie);
  background: var(--card);
  border-radius: 999px;
  padding: .35rem .8rem;
  box-shadow: var(--shadow);
}
.chip-dot { width: 8px; height: 8px; border-radius: 50%; }
.chip-dot.sur { background: var(--sur); }
.chip-dot.eau { background: var(--eau); }
.chip-dot.vigilance { background: var(--vigilance); }
.site-hero-visual { position: relative; }
.site-collage { position: relative; padding-top: 66%; }
.site-collage-main {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius);
  box-shadow: var(--shadow-hover);
}
.site-collage-card {
  position: absolute;
  width: 42%;
  border-radius: var(--radius-sm);
  overflow: hidden;
  box-shadow: var(--shadow-hover);
  border: 4px solid var(--card);
  top: -14%;
  right: -6%;
  transform: rotate(3deg);
  transition: transform .3s var(--anim-ease);
}
.site-collage-card:hover { transform: rotate(0deg) translateY(-4px); }
.site-collage-card.bottom {
  top: auto;
  bottom: -12%;
  right: auto;
  left: -8%;
  transform: rotate(-3deg);
}
.site-collage-card.bottom:hover { transform: rotate(0deg) translateY(-4px); }
.site-collage-side { width: 100%; display: block; }

/* Bande de chiffres clés */
.site-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: .8rem;
  max-width: 1280px;
  margin: 0 auto 1.2rem;
}
.site-stat {
  border: 1px solid var(--craie);
  border-top: 3px solid var(--sur);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: .9rem 1rem;
}
.site-stat.eau { border-top-color: var(--eau); }
.site-stat.vigilance { border-top-color: var(--vigilance); }
.site-stat b { font: 600 30px "IBM Plex Mono", ui-monospace, monospace; color: var(--sur); }
.site-stat.eau b { color: var(--eau); }
.site-stat.vigilance b { color: var(--vigilance); }
.site-stat-unit { font: 500 12px ui-monospace, monospace; opacity: .6; margin-left: .25rem; }
.site-stat small { display: block; font-size: 12.5px; opacity: .75; margin-top: .2rem; }

/* Sections */
.site-section { max-width: 1280px; margin: 0 auto 2.6rem; }
.site-section-grid.two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2.4rem;
  align-items: center;
}
.site-figure-frame {
  border: 1px solid var(--craie);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow-hover);
  padding: .7rem;
}
.site-figure-caption { font-size: 11.5px; opacity: .6; margin-top: .5rem; }
.site-section-text h2, .site-kicker-row h2 {
  font: 600 30px/1.2 "IBM Plex Serif", Georgia, serif;
  letter-spacing: -.01em;
  margin: 0 0 1rem;
  max-width: 560px;
}
.site-section-text p { font-size: 15px; line-height: 1.65; opacity: .88; margin: 0 0 .9rem; }
.site-checklist { list-style: none; padding: 0; margin: 1.2rem 0 0; display: grid; gap: .5rem; }
.site-checklist li {
  display: flex;
  gap: .6rem;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
}
.site-checklist i {
  font-style: normal;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--tint-sur);
  color: var(--sur);
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex: none;
}
.site-kicker-row { margin-bottom: 1.4rem; }
.site-kicker-row h2 { max-width: 640px; margin-bottom: 0; }

/* Valeurs */
.site-value-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .9rem; }
.site-value-card {
  border: 1px solid var(--craie);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 1.2rem 1.2rem 1.3rem;
  color: var(--eau);
  transition: box-shadow .18s ease, transform .18s ease;
}
.site-value-card:hover { box-shadow: var(--shadow-hover); transform: translateY(-3px); }
.site-value-card h3 { font: 600 18px "IBM Plex Serif", Georgia, serif; color: var(--encre); margin: .7rem 0 .35rem; }
.site-value-card p { font-size: 13.5px; line-height: 1.55; opacity: .8; margin: 0; }

/* Expertise */
.site-expertise-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .9rem; }
.site-expertise-card {
  border: 1px solid var(--craie);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: box-shadow .18s ease, transform .18s ease;
}
.site-expertise-card:hover { box-shadow: var(--shadow-hover); transform: translateY(-4px); }
.site-expertise-media { padding: .7rem .7rem 0; }
.site-expertise-media svg { border-radius: var(--radius-sm); }
.site-expertise-body { padding: .9rem 1rem 1.1rem; display: flex; flex-direction: column; flex: 1; }
.site-expertise-body h3 { font: 600 18px "IBM Plex Serif", Georgia, serif; margin: 0 0 .4rem; }
.site-expertise-body p { font-size: 13.5px; line-height: 1.55; opacity: .82; margin: 0 0 .8rem; flex: 1; }
.site-expertise-link { font-size: 13px; font-weight: 600; color: var(--eau); text-decoration: none; }
.site-expertise-link:hover { text-decoration: underline; }

/* Approche */
.site-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.4rem; }
.site-step { border-top: 2px solid var(--craie); padding-top: 1rem; }
.site-step-num { font: 600 26px "IBM Plex Mono", ui-monospace, monospace; color: var(--eau); opacity: .8; }
.site-step h3 { font: 600 17px "IBM Plex Serif", Georgia, serif; margin: .4rem 0 .3rem; }
.site-step p { font-size: 13.5px; line-height: 1.55; opacity: .8; margin: 0; }

/* CTA */
.site-cta {
  max-width: 1280px;
  margin: 0 auto 2.4rem;
  border-radius: calc(var(--radius) * 1.3);
  background: linear-gradient(135deg, var(--encre), #23384B 55%, var(--eau));
  color: var(--papier);
  box-shadow: var(--shadow-hover);
  overflow: hidden;
  position: relative;
}
.site-cta::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(500px 200px at 88% -10%, rgba(74,144,217,.35), transparent 60%);
}
.site-cta-inner { position: relative; padding: 2.4rem 2.6rem; max-width: 720px; }
.site-cta-inner h2 { font: 600 28px "IBM Plex Serif", Georgia, serif; color: #fff; margin: 0 0 .6rem; }
.site-cta-inner p { font-size: 14.5px; line-height: 1.6; opacity: .85; margin: 0 0 1.3rem; }
.site-cta .site-btn-primary { background: var(--papier); color: var(--encre); }
.site-cta .site-btn-primary:hover { background: #fff; color: var(--eau); }

/* Footer */
.site-footer { border-top: 1px solid var(--craie); background: var(--card); }
.site-footer-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem 1.6rem 1.2rem;
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  gap: 2rem;
}
.site-footer h4 { font-size: 12px; text-transform: uppercase; letter-spacing: .1em; opacity: .6; margin: 0 0 .7rem; }
.site-footer p { font-size: 13.5px; line-height: 1.6; opacity: .85; margin: 0 0 .5rem; }
.site-footer a { color: var(--eau); text-decoration: none; }
.site-footer a:hover { text-decoration: underline; }
.site-live { display: flex; align-items: center; gap: .45rem; }
.site-live i { width: 8px; height: 8px; border-radius: 50%; background: var(--sur); box-shadow: 0 0 0 4px var(--tint-sur); flex: none; }
.site-foot-link {
  display: block;
  font-size: 13.5px;
  color: var(--eau);
  text-decoration: none;
  padding: .2rem 0;
  cursor: pointer;
}
.site-foot-link:hover { text-decoration: underline; }
.site-footer-legal {
  border-top: 1px solid var(--craie);
  font-size: 11.5px;
  opacity: .55;
  padding: .9rem 1.6rem;
  text-align: center;
}

/* Contact */
.site-contact { max-width: 720px; margin: 0 auto 2.4rem; text-align: center; }
.site-contact h1 { font: 600 34px "IBM Plex Serif", Georgia, serif; margin: 0 0 .6rem; }
.site-contact p { font-size: 15px; opacity: .85; line-height: 1.65; }
.site-contact-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .9rem; margin-top: 1.6rem; }
.site-contact-card {
  border: 1px solid var(--craie);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 1.2rem;
}
.site-contact-card h3 { font: 600 15px "IBM Plex Serif", Georgia, serif; margin: 0 0 .3rem; }
.site-contact-card p { font-size: 13px; opacity: .8; margin: 0; }
.site-contact-card a { color: var(--eau); text-decoration: none; }
.site-contact-card a:hover { text-decoration: underline; }

/* Vue « Graphe & IA » : bandeau d'intro */
.site-view-head { max-width: 1280px; margin: 0 auto 1.4rem; }
.site-view-head h1 { font: 600 30px "IBM Plex Serif", Georgia, serif; margin: 0 0 .4rem; }
.site-view-head p { font-size: 14.5px; opacity: .82; max-width: 760px; margin: 0; }

/* Responsive */
@media (max-width: 1024px) {
  .site-hero-inner { grid-template-columns: 1fr; gap: 1.6rem; }
  .site-hero-title { font-size: 34px; }
  .site-stats { grid-template-columns: repeat(2, 1fr); }
  .site-expertise-grid, .site-value-grid, .site-steps { grid-template-columns: 1fr; }
  .site-section-grid.two { grid-template-columns: 1fr; }
  .site-footer-inner { grid-template-columns: 1fr; gap: 1.4rem; }
  .site-collage-card { width: 38%; }
}
@media (max-width: 640px) {
  .block-container { padding-top: 118px; }
  .site-navbar-inner { padding: .5rem 1rem; }
  .site-nav-item { padding: .3rem .6rem; font-size: 12px; }
  .site-stats { grid-template-columns: 1fr; }
  .site-contact-grid { grid-template-columns: 1fr; }
  .site-hero-title { font-size: 28px; }
}

/* Reduced motion support for new animations */
@media (prefers-reduced-motion: reduce) {
  .animate-mask-reveal,
  .animate-split-line > *,
  .animate-fade-up,
  .animate-stagger > *,
  .animate-vertical-mask > *,
  .animate-scale-down > *,
  .animate-zoom-hover > *,
  .animate-card-hover,
  .animate-arrow-slide .arrow,
  .animated-underline::after,
  .animate-divider::before,
  .animate-count-up,
  .page-intro,
  .lineage,
  .lineage.is-visible .lineage-node,
  .lineage-node,
  .lineage-edge,
  .lineage-node .lineage-dot,
  .lineage-card summary::after,
  .console-step,
  .cascade-node,
  .cascade-arrow,
  .water-bar,
  .kpi-tile,
  .site-btn,
  .site-collage-card,
  .site-value-card,
  .site-expertise-card,
  .page-transition-enter-active,
  .page-transition-exit-active {
    animation: none !important;
    transition: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
  .animate-fade-up,
  .animate-stagger > * {
    opacity: 1 !important;
    transform: none !important;
  }
}
</style>
"""
