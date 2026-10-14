FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=none \
    STREAMLIT_THEME_BASE=light \
    STREAMLIT_THEME_PRIMARY_COLOR=#B64B32 \
    STREAMLIT_THEME_BACKGROUND_COLOR=#F6F8F6 \
    STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR=#E9EFEC \
    STREAMLIT_THEME_TEXT_COLOR=#202A27 \
    STREAMLIT_THEME_BORDER_COLOR=#D3DDD8 \
    STREAMLIT_THEME_SHOW_WIDGET_BORDER=true \
    STREAMLIT_THEME_SHOW_SIDEBAR_BORDER=true \
    STREAMLIT_THEME_BASE_RADIUS=6px \
    STREAMLIT_THEME_BUTTON_RADIUS=6px \
    STREAMLIT_THEME_SIDEBAR_BACKGROUND_COLOR=#203B35 \
    STREAMLIT_THEME_SIDEBAR_SECONDARY_BACKGROUND_COLOR=#2B4942 \
    STREAMLIT_THEME_SIDEBAR_TEXT_COLOR=#F3F6F4 \
    STREAMLIT_THEME_SIDEBAR_BORDER_COLOR=#45645C \
    STREAMLIT_THEME_SIDEBAR_PRIMARY_COLOR=#D96948

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser app.py ./
COPY --chown=appuser:appuser core ./core

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os; from urllib.request import urlopen; urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8501') + '/_stcore/health', timeout=3)" || exit 1

CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.headless=true --server.address=0.0.0.0"]
