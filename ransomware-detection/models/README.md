# Modelos treinados

Executa o benchmark para gerar `models/ransomware/` com todos os pipelines
scikit-learn e o schema de features:

```powershell
python src/supervised_learning.py --data ransom.csv --output results --model-dir models/ransomware
```

Os modelos `.joblib` e o cache dos pesos Hugging Face são artefactos locais
ignorados pelo Git. Carrega apenas modelos serializados de fontes confiáveis.
