FROM grafana/grafana:10.2.2

# Configurações do Grafana
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_USERS_ALLOW_SIGN_UP=false
ENV GF_SECURITY_ALLOW_EMBEDDING=true
ENV GF_AUTH_ANONYMOUS_ENABLED=false
ENV GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel,grafana-clock-panel

# Criar usuário grafana
USER root
RUN mkdir -p /etc/grafana/provisioning/datasources \
    && mkdir -p /etc/grafana/provisioning/dashboards \
    && mkdir -p /var/lib/grafana/dashboards \
    && chown -R grafana:grafana /etc/grafana \
    && chown -R grafana:grafana /var/lib/grafana

# Copiar configurações
COPY provisioning/ /etc/grafana/provisioning/
COPY dashboards/ /var/lib/grafana/dashboards/
COPY grafana.ini /etc/grafana/grafana.ini

# Voltar para usuário grafana
USER grafana

# Expor porta
EXPOSE 3000

# Comando padrão
CMD ["grafana-server", "--config=/etc/grafana/grafana.ini"] 