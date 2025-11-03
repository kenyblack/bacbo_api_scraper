FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates unzip gnupg2 xz-utils tzdata \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdbus-1-3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango1.0-0 libxss1 libnss3 procps curl \
    && rm -rf /var/lib/apt/lists/*
# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update && apt-get install -y google-chrome-stable --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*
# Install chromedriver matching chrome
RUN CHROME_VER=$(google-chrome-stable --version | awk '{print $3}' | cut -d. -f1) \
    && BASE_URL="https://chromedriver.storage.googleapis.com" \
    && LATEST=$(wget -qO- ${BASE_URL}/LATEST_RELEASE_${CHROME_VER}) \
    && wget -q ${BASE_URL}/${LATEST}/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip
WORKDIR /app
COPY . /app
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:5000"]
