# Projeto Big Brother para artigo
**Baseado no golpe do pix, que ocorreu devido a backdoor gerado atraves de engenharia social e baseado no livro 1984 de George Owell a ideia surgiu apra simular um conxtexto totalmente ficcional onde um sistema de segurança baseado em IA analisa padrões e detecta falhas de segurança corriqueiras em funcionarios de um banco**

## Objetivo do sistema:
- Identificar funcionários com base no rosto, estilo de roupas, acessórios.
- Detectar anomalias em rotinas diárias: horários, movimentação, ausência de crachá.
- Gerar alertas com base nos padrões aprendidos.

### Estrutura do Projeto:
````
projeto_vigilancia_cnn/
│
├── _DOCS_/                 # Documentação 
├── data/                   # Dataset de imagens e metadados
│   ├── imagens/
│   ├── horarios.csv
│   └── rotinas.json
│
├── models/
│   └── cnn_model.py       # Arquitetura CNN
│
├── train.py               # Script de treinamento
├── inference.py           # Inferência + geração de relatório
├── utils.py               # Funções auxiliares
└── config.yaml            # Hiperparâmetros
````

