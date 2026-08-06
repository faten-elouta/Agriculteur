"""Animation utilities for Streamlit - scroll-triggered animations via IntersectionObserver."""

from __future__ import annotations

import streamlit as st
from streamlit.components.v1 import html


SCROLL_ANIMATION_SCRIPT = """
<script>
// IntersectionObserver for scroll-triggered animations
(function() {
  'use strict';

  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -10% 0px',
    threshold: 0.1
  };

  const fadeUpObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        fadeUpObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  const staggerObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        staggerObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Initialize on DOM ready
  function initObservers() {
    document.querySelectorAll('.animate-fade-up').forEach(el => {
      fadeUpObserver.observe(el);
    });
    document.querySelectorAll('.animate-stagger').forEach(el => {
      staggerObserver.observe(el);
    });
  }

  // Handle Streamlit's dynamic content
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initObservers);
  } else {
    initObservers();
  }

  // Re-observe when Streamlit re-renders
  const observer = new MutationObserver((mutations) => {
    let shouldReinit = false;
    mutations.forEach(mutation => {
      if (mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === 1) { // Element node
            if (node.matches?.('.animate-fade-up, .animate-stagger') ||
                node.querySelector?.('.animate-fade-up, .animate-stagger')) {
              shouldReinit = true;
            }
          }
        });
      }
    });
    if (shouldReinit) {
      initObservers();
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  // Parallax effect for images
  function handleParallax() {
    document.querySelectorAll('.parallax-image').forEach(img => {
      const rect = img.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const distanceFromCenter = rect.top + rect.height / 2 - viewportHeight / 2;
      const translateY = distanceFromCenter * 0.15; // 15% parallax factor
      img.style.transform = `translateY(${translateY}px)`;
    });
  }

  // Throttled parallax on scroll
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        handleParallax();
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });

  // Count-up animation for numbers
  function animateCountUp(element) {
    const target = parseFloat(element.dataset.target || element.textContent);
    const duration = 1000; // ms
    const startTime = performance.now();
    const isDecimal = target % 1 !== 0;
    const decimals = isDecimal ? (target.toString().split('.')[1]?.length || 0) : 0;

    function updateCount(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;
      element.textContent = isDecimal ? current.toFixed(decimals) : Math.round(current);

      if (progress < 1) {
        requestAnimationFrame(updateCount);
      }
    }

    requestAnimationFrame(updateCount);
  }

  const countUpObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCountUp(entry.target);
        countUpObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.animate-count-up').forEach(el => {
    countUpObserver.observe(el);
  });

  // Page transition handling for multi-step flows
  window.addEventListener('beforeunload', () => {
    document.body.classList.add('page-transition-exit');
    document.body.classList.remove('page-transition-enter-active');
  });

  // Expose for manual triggering
  window.TerroirAnimations = {
    initObservers,
    animateCountUp,
    handleParallax
  };
})();
</script>
"""


def inject_scroll_animations() -> None:
    """Inject the scroll animation JavaScript into the page.
    Call once at the top of your Streamlit app."""
    html(SCROLL_ANIMATION_SCRIPT, height=0, width=0)


def mask_reveal(text: str, delay: int = 0, tag: str = "span") -> str:
    """Wrap text in masked reveal animation."""
    delay_class = f" animate-mask-reveal-delay-{delay}" if delay else ""
    return f'<{tag} class="animate-mask-reveal{delay_class}">{text}</{tag}>'


def split_line_reveal(lines: list[str], tag: str = "div") -> str:
    """Wrap lines in split-line reveal animation."""
    inner = "".join(f"<{tag}>{line}</{tag}>" for line in lines)
    return f'<div class="animate-split-line">{inner}</div>'


def fade_up(content: str, delay: int = 0, tag: str = "div") -> str:
    """Wrap content in fade-up on scroll animation."""
    delay_class = f" animate-fade-up-delay-{delay}" if delay else ""
    return f'<{tag} class="animate-fade-up{delay_class}">{content}</{tag}>'


def stagger_container(items: list[str], tag: str = "div", item_tag: str = "div") -> str:
    """Wrap items in staggered scroll reveal container."""
    inner = "".join(f"<{item_tag}>{item}</{item_tag}>" for item in items)
    return f'<{tag} class="animate-stagger">{inner}</{tag}>'


def vertical_mask_reveal(image_url: str, alt: str = "") -> str:
    """Wrap image in vertical mask reveal."""
    return f'<div class="animate-vertical-mask"><img src="{image_url}" alt="{alt}" loading="lazy"></div>'


def scale_down_reveal(image_url: str, alt: str = "") -> str:
    """Wrap image in scale-down reveal."""
    return f'<div class="animate-scale-down"><img src="{image_url}" alt="{alt}" loading="lazy"></div>'


def parallax_image(image_url: str, alt: str = "") -> str:
    """Wrap image in parallax container."""
    return f'<div class="parallax-container"><img class="parallax-image" src="{image_url}" alt="{alt}" loading="lazy"></div>'


def zoom_hover_image(image_url: str, alt: str = "") -> str:
    """Wrap image in zoom-on-hover."""
    return f'<div class="animate-zoom-hover"><img src="{image_url}" alt="{alt}" loading="lazy"></div>'


def card_hover(content: str, tag: str = "div") -> str:
    """Wrap content in card hover micro-interaction."""
    return f'<{tag} class="animate-card-hover">{content}</{tag}>'


def arrow_slide(label: str, arrow: str = "→", href: str = "#") -> str:
    """Create arrow slide on hover link."""
    return f'<a class="animate-arrow-slide animated-underline" href="{href}">{label}<span class="arrow">{arrow}</span></a>'


def animated_divider(color: str = "currentColor") -> str:
    """Create animated horizontal divider."""
    return f'<div class="animate-divider" style="color: {color};"></div>'


def count_up_number(value: float, decimals: int = 0, prefix: str = "", suffix: str = "") -> str:
    """Create count-up animated number."""
    formatted = f"{value:,.{decimals}f}".replace(",", " ")
    return f'<span class="animate-count-up" data-target="{value}">{prefix}{formatted}{suffix}</span>'


def page_intro(children: list[str]) -> str:
    """Wrap children in page-load intro sequence."""
    inner = "".join(children)
    return f'<div class="page-intro">{inner}</div>'


def page_transition(content: str, is_entering: bool = True) -> str:
    """Wrap content in page transition animation."""
    cls = "page-transition-enter-active" if is_entering else "page-transition-exit-active"
    return f'<div class="page-transition-enter {cls}">{content}</div>'


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