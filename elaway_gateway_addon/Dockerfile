FROM jvik/elaway-gateway-api:latest

# Installer jq for å lese konfigurasjon
USER root
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Kopier inn startskriptet vårt
COPY run.sh /run.sh
RUN chmod a+x /run.sh

ENTRYPOINT ["/run.sh"]
