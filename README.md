# IAAC — Projetos de deteção e análise de malware

Este repositório reúne os projetos desenvolvidos no âmbito da unidade
curricular de Inteligência Artificial e Análise de Dados (IAAC).

Os projetos são mantidos em **branches independentes** para evitar que os
ficheiros, ambientes e decisões de um projeto interfiram nos restantes.

## Projetos

### Deteção de ransomware

Branch: [`feature/ransomware-detection`](https://github.com/josediogocostamoreira-boop/IAAC/tree/feature/ransomware-detection)

Projeto de classificação de amostras benignas e malware, com foco na análise
de características PE e comportamentais. Inclui:

- Business Understanding e Data Understanding;
- EDA univariada, bivariada e multivariada;
- Data Preparation reproduzível;
- prevenção de data leakage por MD5;
- modelos baseline e métricas;
- interface de previsão por linha de comandos;
- backlog de produto e documentação SCRUM.

### Deteção de malware

Branch: [`feature/malware-detection`](https://github.com/josediogocostamoreira-boop/IAAC/tree/feature/malware-detection)

Projeto independente de deteção de malware, com o seu próprio código, dados,
modelos, resultados e requisitos.

## Organização do Git

- `main`: introdução e informação comum do repositório;
- `feature/ransomware-detection`: desenvolvimento exclusivo do projeto de
  ransomware;
- `feature/malware-detection`: desenvolvimento exclusivo do projeto de
  malware.

Para trabalhar num projeto, muda para a respetiva branch:

```powershell
git switch feature/ransomware-detection
```

ou:

```powershell
git switch feature/malware-detection
```

Cada projeto tem instruções próprias no seu `README.md`. A branch `main` não
contém os ficheiros dos projetos; serve como ponto de entrada e organização do
trabalho do grupo.
