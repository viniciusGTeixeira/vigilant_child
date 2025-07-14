# Documento de Requisitos Não-Funcionais (NFR)

## 1. Performance

### NFR001 - Tempo de Resposta
- **Descrição**: Tempo máximo para processamento de frames
- **Métrica**: < 200ms por frame
- **Medição**: 95º percentil
- **Monitoramento**: Prometheus + Grafana

### NFR002 - Throughput
- **Descrição**: Capacidade de processamento
- **Métrica**: 30 FPS por câmera
- **Medição**: Média em 5 minutos
- **Monitoramento**: Custom metrics

### NFR003 - Latência
- **Descrição**: Atraso máximo end-to-end
- **Métrica**: < 1s total
- **Medição**: 99º percentil
- **Monitoramento**: APM tools

## 2. Escalabilidade

### NFR004 - Horizontal Scaling
- **Descrição**: Capacidade de adicionar nós
- **Métrica**: Linear até 100 nós
- **Medição**: Throughput/nó
- **Implementação**: Kubernetes

### NFR005 - Carga Máxima
- **Descrição**: Limite de processamento
- **Métrica**: 1000 câmeras/cluster
- **Medição**: Monitoramento contínuo
- **Alertas**: 80% threshold

## 3. Disponibilidade

### NFR006 - Uptime
- **Descrição**: Tempo de funcionamento
- **Métrica**: 99.9% mensal
- **Medição**: Healthchecks
- **Monitoramento**: Pingdom/Uptime Robot

### NFR007 - Failover
- **Descrição**: Tempo de recuperação
- **Métrica**: < 30 segundos
- **Medição**: Testes automáticos
- **Implementação**: Active-Active

## 4. Segurança

### NFR008 - Criptografia
- **Descrição**: Proteção de dados
- **Requisito**: AES-256
- **Escopo**: Dados em repouso e trânsito
- **Validação**: Auditorias periódicas

### NFR009 - Autenticação
- **Descrição**: Controle de acesso
- **Requisito**: OAuth 2.0 + 2FA
- **Implementação**: Keycloak
- **Logs**: Audit trail completo

### NFR010 - Autorização
- **Descrição**: Controle de permissões
- **Requisito**: RBAC
- **Granularidade**: Por recurso
- **Auditoria**: Logs detalhados

## 5. Manutenibilidade

### NFR011 - Código
- **Descrição**: Qualidade de código
- **Métrica**: Sonar A rating
- **Cobertura**: > 80% testes
- **Ferramentas**: SonarQube

### NFR012 - Documentação
- **Descrição**: Documentação técnica
- **Requisito**: Swagger/OpenAPI
- **Cobertura**: 100% APIs
- **Formato**: Markdown

## 6. Usabilidade

### NFR013 - Interface
- **Descrição**: UX/UI design
- **Requisito**: Material Design
- **Responsividade**: Mobile-first
- **Acessibilidade**: WCAG 2.1

### NFR014 - Tempo de Aprendizado
- **Descrição**: Curva de aprendizado
- **Métrica**: < 4 horas treinamento
- **Validação**: User testing
- **Feedback**: NPS > 8

## 7. Confiabilidade

### NFR015 - Backup
- **Descrição**: Backup de dados
- **Frequência**: Diário
- **Retenção**: 90 dias
- **RPO**: 1 hora

### NFR016 - Recuperação
- **Descrição**: Disaster recovery
- **RTO**: 2 horas
- **Teste**: Trimestral
- **Documentação**: Runbooks

## 8. Compatibilidade

### NFR017 - Browsers
- **Descrição**: Suporte navegadores
- **Requisito**: últimas 2 versões
- **Browsers**: Chrome, Firefox, Safari
- **Teste**: Cross-browser

### NFR018 - Integração
- **Descrição**: APIs externas
- **Padrão**: REST/GraphQL
- **Formato**: JSON
- **Versionamento**: Semantic

## 9. Compliance

### NFR019 - LGPD/GDPR
- **Descrição**: Conformidade legal
- **Requisito**: 100% compliance
- **Auditoria**: Semestral
- **Documentação**: DPIAs

### NFR020 - Logs
- **Descrição**: Registro de eventos
- **Retenção**: 12 meses
- **Formato**: Structured logging
- **Indexação**: Elasticsearch

## 10. Monitoramento

### NFR021 - Métricas
- **Descrição**: Coleta de métricas
- **Frequência**: Real-time
- **Storage**: Time series DB
- **Dashboards**: Grafana

### NFR022 - Alerting
- **Descrição**: Sistema de alertas
- **Latência**: < 1 minuto
- **Canais**: Email, SMS, Slack
- **Priorização**: Severity levels

## 11. Recursos

### NFR023 - CPU
- **Descrição**: Uso de processador
- **Limite**: < 80% médio
- **Monitoramento**: cAdvisor
- **Scaling**: Auto-scaling

### NFR024 - Memória
- **Descrição**: Uso de RAM
- **Limite**: < 85% total
- **Garbage Collection**: Tuned
- **Leak Detection**: Automated

### NFR025 - Storage
- **Descrição**: Armazenamento
- **Tipo**: SSD
- **IOPS**: > 3000
- **Latência**: < 10ms

## 12. Rede

### NFR026 - Bandwidth
- **Descrição**: Largura de banda
- **Requisito**: 10 Mbps/câmera
- **QoS**: Implementado
- **Monitoramento**: SNMP

### NFR027 - Conexões
- **Descrição**: Conexões simultâneas
- **Limite**: 1000/node
- **Timeout**: Configurável
- **Keep-alive**: Enabled 