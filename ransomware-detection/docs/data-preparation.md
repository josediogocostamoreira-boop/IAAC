# Data Preparation

## Pipeline proposto

1. Ler `ransom.csv` com `encoding="utf-8-sig"`.
2. Validar nomes, cardinalidade, rótulos e tipos.
3. Remover linhas sem `md5`/`Class` e reportar a contagem removida.
4. Verificar conflitos de rótulo por `md5`.
5. Deduplicar por `md5`, mantendo uma linha apenas quando o rótulo é
   consistente.
6. Excluir `md5`, `sha1`, `Class`, `Category` e `Family` das features do
   classificador binário. `Category` e `Family` são alvos de tarefas futuras,
   não preditores.
7. Converter strings hexadecimais que sejam valores numéricos; manter como
   categóricas as descrições (`PEType`, `Subsystem`, flags, etc.).
8. Aplicar `log1p` a valores numéricos não negativos com skewness absoluta > 1,
   aprendendo a seleção no fold de treino.
9. Imputar valores numéricos com a mediana calculada no treino.
10. Imputar categorias com a moda e aplicar one-hot encoding, ignorando
   categorias desconhecidas.
11. Selecionar features com `SelectKBest(f_classif)` dentro do pipeline; o
    número de features é afinado na validação cruzada.
12. Usar `StandardScaler` apenas quando o modelo o exigir.
13. Dividir de forma estratificada e agrupada por `md5` (ou depois da
    deduplicação, com `train_test_split` estratificado).
14. Guardar o pipeline e o esquema de colunas usado no treino.

## Validações

- Confirmar que `X_train` e `X_test` não partilham hashes.
- Confirmar que não existem `NaN` após o transformador.
- Confirmar que o alvo contém apenas `Benign` e `Malware`.
- Comparar a distribuição dos alvos entre treino, validação e teste.
- Registar todas as linhas removidas e conflitos.

## Decisões que não devem ser tomadas na EDA

Não remover outliers automaticamente apenas por regra IQR: tamanhos e contagens
extremas podem ser sinais de malware. A decisão deve ser comparada com e sem
transformação, usando validação e métricas orientadas ao risco.

## Sprint 2 — execução

O relatório executável [`data_preparation_report.py`](../src/data_preparation_report.py)
implementa as verificações do Module 4:

```powershell
python src/data_preparation_report.py --data ransom.csv --output results
```

Produz:

- `data_preparation_report.json`: decisões e contagens de todas as etapas;
- `feature_quality.csv`: missing values, skewness e outliers IQR por feature;
- `high_correlation_pairs.csv`: pares com |Spearman| >= 0,95.
- `src/roadmap_eda.py` gera em `results/roadmap/eda/` sumários univariados,
  distribuições, testes bivariados com correção FDR, correlações
  Pearson/Spearman e PCA exploratória.

O split é estratificado (`random_state=42`), a imputação, a transformação
`log1p`, a seleção e a escala são ajustadas apenas dentro do treino/fold. Os
outliers são reportados sem serem apagados.
