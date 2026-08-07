"""Animation utilities for Streamlit - scroll-triggered animations via IntersectionObserver.

Les helpers HTML injectent des classes CSS (définies dans ui/styles.py) et ce
module injecte le JavaScript qui pilote les animations par intersection.

Contrainte Streamlit : st.components.v1.html rend le script dans une iframe
isolée. Le DOM de l'application vit dans l'iframe parente — le script cible
donc window.parent.document (même origine : fonctionne en local, Streamlit
Cloud, Render et Vercel).
"""

from __future__ import annotations

import streamlit as st
from streamlit.components.v1 import html


SCROLL_ANIMATION_SCRIPT = """
<script>
(function() {
  'use strict';
  var doc = window.parent.document;

  var observerOptions = { root: null, rootMargin: '0px 0px -10% 0px', threshold: 0.1 };
  var countOptions = { root: null, rootMargin: '0px 0px -5% 0px', threshold: 0.4 };

  function observeAll() {
    var els;
    els = doc.querySelectorAll('.animate-fade-up:not(.is-visible)');
    els.forEach(function(el) { fadeObserver.observe(el); });
    els = doc.querySelectorAll('.animate-stagger:not(.is-visible)');
    els.forEach(function(el) { staggerObserver.observe(el); });
    els = doc.querySelectorAll('.animate-count-up:not(.counting):not([data-done])');
    els.forEach(function(el) { countObserver.observe(el); });
    els = doc.querySelectorAll('.page-transition-enter:not(.page-transition-enter-active)');
    els.forEach(function(el) {
      requestAnimationFrame(function() { el.classList.add('page-transition-enter-active'); });
    });
  }

  var fadeObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        fadeObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  var staggerObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        staggerObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Count-up : remplit un nombre depuis 0 vers data-target (ease-out cubique).
  function animateCountUp(element) {
    element.classList.add('counting');
    element.dataset.done = '1';
    var target = parseFloat(element.dataset.target || element.textContent) || 0;
    var prefix = element.dataset.prefix || '';
    var suffix = element.dataset.suffix || '';
    var duration = 1100;
    var startTime = null;
    var isDecimal = target % 1 !== 0;
    var decimals = isDecimal ? ((target.toString().split('.')[1] || '').length) : 0;

    function render(elapsed) {
      if (startTime === null) startTime = elapsed;
      var progress = Math.min((elapsed - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = target * eased;
      element.textContent = prefix + (isDecimal ? current.toFixed(decimals) : Math.round(current)) + suffix;
      if (progress < 1) { requestAnimationFrame(render); }
      else { element.dataset.done = '1'; }
    }
    requestAnimationFrame(render);
  }

  var countObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        animateCountUp(entry.target);
        countObserver.unobserve(entry.target);
      }
    });
  }, countOptions);

  // Parallax léger sur les éléments .parallax-image (throttlé par rAF).
  function handleParallax() {
    doc.querySelectorAll('.parallax-image').forEach(function(img) {
      var rect = img.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.parent.innerHeight) return;
      var viewportHeight = window.parent.innerHeight;
      var distanceFromCenter = rect.top + rect.height / 2 - viewportHeight / 2;
      img.style.transform = 'translateY(' + (distanceFromCenter * 0.12).toFixed(1) + 'px)';
    });
  }
  var ticking = false;
  window.parent.addEventListener('scroll', function() {
    if (!ticking) {
      window.parent.requestAnimationFrame(function() { handleParallax(); ticking = false; });
      ticking = true;
    }
  }, { passive: true });

  // Filet de sécurité : rien ne doit rester invisible si un observateur échoue.
  window.parent.setTimeout(function() {
    doc.querySelectorAll('.animate-fade-up, .animate-stagger').forEach(function(el) {
      el.classList.add('is-visible');
    });
    doc.querySelectorAll('.animate-count-up:not(.counting)').forEach(function(el) {
      animateCountUp(el);
    });
  }, 4000);

  // Re-pilotage quand Streamlit re-rend (nouveaux nœuds à chaque rerun).
  var reinitTimer = null;
  function scheduleReinit() {
    if (reinitTimer) window.parent.clearTimeout(reinitTimer);
    reinitTimer = window.parent.setTimeout(function() { observeAll(); }, 150);
  }
  var mutationObserver = new MutationObserver(function(mutations) {
    var hit = false;
    mutations.forEach(function(mutation) {
      mutation.addedNodes.forEach(function(node) {
        if (node.nodeType === 1) {
          if (node.matches && node.matches(
              '.animate-fade-up, .animate-stagger, .animate-count-up, .page-transition-enter, .parallax-image') ||
              (node.querySelector && node.querySelector(
              '.animate-fade-up, .animate-stagger, .animate-count-up, .page-transition-enter, .parallax-image'))) {
            hit = true;
          }
        }
      });
    });
    if (hit) scheduleReinit();
  });
  mutationObserver.observe(doc.body, { childList: true, subtree: true });

  // Transition de sortie douce avant rechargement.
  window.parent.addEventListener('beforeunload', function() {
    doc.body.classList.add('page-transition-exit');
  });

  if (doc.readyState === 'loading') {
    doc.addEventListener('DOMContentLoaded', function() { observeAll(); handleParallax(); });
  } else {
    observeAll();
    handleParallax();
  }

  window.TerroirAnimations = { observeAll: observeAll, animateCountUp: animateCountUp, handleParallax: handleParallax };
})();
</script>
"""


def inject_scroll_animations() -> None:
    """Injecte le JavaScript d'animations dans la page.
    À appeler une fois après le CSS, en haut de l'application."""
    if hasattr(st, "iframe"):  # streamlit >= 1.50 (remplace st.components.v1.html)
        st.iframe(SCROLL_ANIMATION_SCRIPT, height=1)
    else:
        html(SCROLL_ANIMATION_SCRIPT, height=0, width=0)


def mask_reveal(text: str, delay: int = 0, tag: str = "span") -> str:
    """1. Masque animé : le texte apparaît de gauche à droite."""
    delay_class = f" animate-mask-reveal-delay-{delay}" if delay else ""
    return f'<{tag} class="animate-mask-reveal{delay_class}">{text}</{tag}>'


def split_line_reveal(lines: list[str], tag: str = "div") -> str:
    """2. Révélation ligne par ligne (glissent depuis le bas)."""
    inner = "".join(f"<{tag}>{line}</{tag}>" for line in lines)
    return f'<div class="animate-split-line">{inner}</div>'


def fade_up(content: str, delay: int = 0, tag: str = "div") -> str:
    """3. Apparition en fondu + translation au scroll."""
    delay_class = f" animate-fade-up-delay-{delay}" if delay else ""
    return f'<{tag} class="animate-fade-up{delay_class}">{content}</{tag}>'


def stagger_container(items: list[str], tag: str = "div", item_tag: str = "div") -> str:
    """4. Révélation échelonnée : chaque enfant apparaît en séquence."""
    inner = "".join(f"<{item_tag}>{item}</{item_tag}>" for item in items)
    return f'<{tag} class="animate-stagger">{inner}</{tag}>'


def vertical_mask_reveal(image_url: str, alt: str = "") -> str:
    """5. Masque vertical : l'image se découvre de haut en bas."""
    return f'<div class="animate-vertical-mask"><img src="{image_url}" alt="{alt}" loading="lazy"></div>'


def scale_down_reveal(image_url: str, alt: str = "") -> str:
    """6. Zoom arrière : l'image passe de 1.15x à 1x en apparaissant."""
    return f'<div class="animate-scale-down"><img src="{image_url}" alt="{alt}" loading="lazy"></div>'


def parallax_image(image_url: str, alt: str = "") -> str:
    """7. Parallaxe subtile au scroll (translation douce)."""
    return f'<div class="parallax-container"><img class="parallax-image" src="{image_url}" alt="{alt}" loading="lazy"></div>'


def zoom_hover_image(image_url: str, alt: str = "") -> str:
    """8. Zoom doux de l'image au survol."""
    return f'<div class="animate-zoom-hover"><img src="{image_url}" alt="{alt}" loading="lazy"></div>'


def card_hover(content: str, tag: str = "div") -> str:
    """9. Micro-interaction au survol : soulèvement + ombre + bordure."""
    return f'<{tag} class="animate-card-hover">{content}</{tag}>'


def arrow_slide(label: str, arrow: str = "→", href: str = "#") -> str:
    """10. Lien dont la flèche glisse au survol (+ soulignement animé)."""
    return f'<a class="animate-arrow-slide animated-underline" href="{href}" target="_blank" rel="noopener">{label}<span class="arrow">{arrow}</span></a>'


def animated_divider(color: str = "currentColor") -> str:
    """12. Trait horizontal qui se dessine depuis le centre."""
    return f'<div class="animate-divider" style="color: {color};" aria-hidden="true"></div>'


def count_up_number(value: float, decimals: int = 0, prefix: str = "", suffix: str = "") -> str:
    """13. Nombre qui compte de 0 jusqu'à sa valeur quand il entre à l'écran."""
    formatted = f"{value:,.{decimals}f}".replace(",", " ")
    return (
        f'<span class="animate-count-up" data-target="{value}" data-prefix="{prefix}" '
        f'data-suffix="{suffix}">{prefix}{formatted}{suffix}</span>'
    )


def page_intro(children: list[str]) -> str:
    """14. Séquence d'introduction au chargement de page (enfants échelonnés)."""
    inner = "".join(children)
    return f'<div class="page-intro">{inner}</div>'


def page_transition(content: str, is_entering: bool = True) -> str:
    """15. Transition douce de page (fondu + translation légère).

    Le JS ajoute la classe -active juste après l'insertion pour déclencher le
    fondu à chaque re-rendu de contenu.
    """
    cls = "page-transition-enter" if is_entering else "page-transition-exit-active page-transition-enter"
    return f'<div class="{cls}">{content}</div>'


# Convenience functions for common patterns in the app
def animate_metric_card(label: str, value: str, delta: str | None = None, help_text: str = "") -> str:
    """Create an animated metric card."""
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""
    help_html = f'<div class="metric-help">{help_text}</div>' if help_text else ""
    return f"""
    <div class="animate-card-hover animate-fade-up" style="padding: 1rem; border: 1px solid var(--craie); border-radius: var(--radius); background: var(--card);">
        <div class="metric-label" style="font-size: 12px; opacity: 0.6; text-transform: uppercase; letter-spacing: 0.05em;">{label}</div>
        <div class="metric-value" style="font: 600 28px 'IBM Plex Mono', monospace; margin: 0.25rem 0;">{value}</div>
        {delta_html}
        {help_html}
    </div>
    """


def animate_crop_row(crop_name: str, overlap_days: int, margin: float, status: str, levers: list[dict]) -> str:
    """Create an animated crop comparison row."""
    status_colors = {"sûr": "var(--sur)", "vigilance": "var(--vigilance)", "rupture": "var(--rupture)"}
    status_color = status_colors.get(status, "var(--encre)")

    levers_html = ""
    if levers:
        levers_html = '<div class="levers-preview">'
        for lever in levers[:2]:
            levers_html += f'<span class="lever-tag" style="background: var(--tint-eau); color: var(--eau); padding: 2px 8px; border-radius: 999px; font-size: 11px; margin-right: 4px;">{lever.get("action", "")[:30]}</span>'
        levers_html += '</div>'

    return f"""
    <div class="animate-card-hover animate-stagger" style="padding: 1rem; border: 1px solid var(--craie); border-left: 4px solid {status_color}; border-radius: var(--radius); background: var(--card); margin-bottom: 0.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div>
                <div style="font: 600 16px 'IBM Plex Serif', serif;">{crop_name}</div>
                <div style="font-size: 12px; opacity: 0.7; margin-top: 2px;">{overlap_days} j de recouvrement • {margin:,.0f} €/ha</div>
            </div>
            <div style="text-align: right;">
                <span style="background: {status_color}; color: white; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 500;">{status}</span>
            </div>
        </div>
        {levers_html}
    </div>
    """


def animate_timeline_month(month: str, is_critical: bool, weather_icon: str, crop_bars: list[dict]) -> str:
    """Create an animated timeline month cell."""
    critical_class = " frise-month-critical" if is_critical else ""
    bars_html = ""
    for bar in crop_bars:
        color = bar.get("color", "var(--encre)")
        height = bar.get("height", 50)
        bars_html += f'<div class="frise-bar" style="height: {height}%; background: {color}; border-radius: 2px 2px 0 0;"></div>'

    return f"""
    <div class="frise-month{critical_class} animate-fade-up" style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 4px; min-width: 80px;">
        <div style="font: 500 10px 'IBM Plex Mono', monospace; opacity: 0.6;">{month}</div>
        <div style="font-size: 18px;">{weather_icon}</div>
        <div class="frise-bars" style="display: flex; gap: 3px; width: 100%; height: 60px; align-items: flex-end; justify-content: center;">
            {bars_html}
        </div>
    </div>
    """


def animate_spine_segment(name: str, date_str: str, status: str, is_risk: bool = False, level: int = 0) -> str:
    """Create an animated spine segment."""
    status_colors = {"ok": "var(--sur)", "warning": "var(--vigilance)", "error": "var(--rupture)", "unknown": "var(--craie)"}
    dot_color = status_colors.get(status, "var(--craie)")
    risk_class = " risk" if is_risk else ""

    return f"""
    <div class="spine-segment{risk_class}" style="--i: {level}; border-bottom: 1px solid var(--craie); padding: 0.5rem 0;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="dot" style="background: {dot_color};"></span>
            <div style="flex: 1;">
                <div style="font: 500 13px 'IBM Plex Sans', sans-serif;">{name}</div>
                <div style="font: 11px 'IBM Plex Mono', monospace; opacity: 0.6;">{date_str}</div>
            </div>
            <span style="font: 500 11px 'IBM Plex Mono', monospace; color: {dot_color}; text-transform: uppercase;">{status}</span>
        </div>
    </div>
    """


def animate_confidence_badge(level: str, label: str) -> str:
    """Create an animated confidence badge."""
    colors = {"haute": "var(--sur)", "degradee": "var(--vigilance)", "insuffisante": "var(--rupture)"}
    color = colors.get(level, "var(--encre)")

    return f"""
    <span class="animate-mask-reveal" style="
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: {color}15;
        border: 1px solid {color};
        border-radius: 999px;
        color: {color};
        font-weight: 500;
        font-size: 13px;
    ">
        <span style="width: 8px; height: 8px; border-radius: 50%; background: {color};"></span>
        {label}
    </span>
    """


# Export all animation utilities
__all__ = [
    "inject_scroll_animations",
    "mask_reveal",
    "split_line_reveal",
    "fade_up",
    "stagger_container",
    "vertical_mask_reveal",
    "scale_down_reveal",
    "parallax_image",
    "zoom_hover_image",
    "card_hover",
    "arrow_slide",
    "animated_divider",
    "count_up_number",
    "page_intro",
    "page_transition",
    "animate_metric_card",
    "animate_crop_row",
    "animate_timeline_month",
    "animate_spine_segment",
    "animate_confidence_badge",
]
