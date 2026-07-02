#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Central CSS for the SafePLC Streamlit frontend."""

from __future__ import annotations

import streamlit as st


def apply_global_style() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.35rem; padding-bottom: 2.5rem; max-width: 1500px; }
        .safeplc-hero, .safeplc-panel {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 16px 18px;
            background: #ffffff;
            margin-bottom: 14px;
        }
        .safeplc-hero h1 { margin: 0; font-size: 30px; line-height: 1.25; color: #111827; }
        .safeplc-hero p { margin: 8px 0 0; color: #4b5563; line-height: 1.65; }
        .safeplc-kicker {
            color: #6b7280;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .safeplc-card {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 14px;
            background: #ffffff;
            margin-bottom: 10px;
        }
        .safeplc-title { font-weight: 900; color: #111827; margin-bottom: 5px; }
        .safeplc-muted { color: #6b7280; font-size: 13px; line-height: 1.55; }
        .tone-trusted, .tone-passed {
            background: #ecfdf5; border-color: #10b981; color: #065f46;
        }
        .tone-suspicious, .tone-warning, .tone-safe_template {
            background: #fffbeb; border-color: #f59e0b; color: #92400e;
        }
        .tone-blocked, .tone-blocked_poison, .tone-refuse {
            background: #fef2f2; border-color: #ef4444; color: #991b1b;
        }
        .tone-info, .tone-clarify {
            background: #eff6ff; border-color: #3b82f6; color: #1e40af;
        }
        .tone-neutral, .tone-disabled {
            background: #f9fafb; border-color: #d1d5db; color: #374151;
        }
        .tone-blocked_multi_attack {
            background: #fff1f2; border-color: #be123c; color: #881337;
        }
        .safeplc-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 9px;
            font-size: 12px;
            font-weight: 900;
            border: 1px solid currentColor;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 14px 14px 10px;
        }
        div[data-testid="stMetric"] label { color: #6b7280; }
        .stButton button { border-radius: 8px; font-weight: 800; }
        </style>
        """,
        unsafe_allow_html=True,
    )
