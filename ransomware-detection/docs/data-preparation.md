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
8. Imputar valores numéricos com a mediana calculada no treino.
9. Imputar categorias com a moda e aplicar one-hot encoding, ignorando
   categorias desconhecidas.
10. Usar `StandardScaler` apenas quando o modelo o exigir.
11. Dividir de forma estratificada e agrupada por `md5` (ou depois da
    deduplicação, com `train_test_split` estratificado).
12. Guardar o pipeline e o esquema de colunas usado no treino.

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

O split é estratificado (`random_state=42`), a imputação e a escala são
ajustadas apenas no treino através do pipeline, e os outliers são reportados
sem serem apagados. Features `log1p` são apresentadas como candidatos e só
devem ser aplicadas se melhorarem as métricas em validação.
