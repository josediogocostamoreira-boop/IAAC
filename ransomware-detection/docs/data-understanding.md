# Data Understanding

## Fonte e dimensão

O projeto usa o dataset `ransom.csv`, disponibilizado no contexto do dataset
Ransomware Dataset 2024. A inspeção local encontrou:

| Medida | Valor |
|---|---:|
| Linhas | 21.752 |
| Colunas | 77 |
| Classe `Benign` | 10.876 |
| Classe `Malware` | 10.876 |
| Categorias | 5 |
| Famílias | 27 |
| Valores ausentes | 0 |
| Linhas totalmente duplicadas | 0 |
| MD5 repetidos | 7.849 |

## Variáveis

- Identificadores: `md5`, `sha1`.
- Metadados/categorias: `file_extension`, `PEType`, `MachineType`,
  `magic_number`, `Class`, `Category`, `Family`.
- Características PE e comportamentais: tamanhos, endereços, secções,
  características de execução, registry, rede, processos, ficheiros, DLLs e
  APIs.

Muitos campos PE estão representados como texto hexadecimal (`0x...`) e alguns
campos são descrições categóricas. O tipo inferido pelo pandas não deve ser
aceite sem validação semântica.

## Distribuições relevantes

`Category` contém 10.876 benignas, 4.762 ransomware, 2.647 RAT, 2.018
stealer e 1.449 trojan. As famílias incluem 26 famílias de malware e a classe
`Benign`.

## Qualidade e riscos

Não há valores ausentes nem linhas duplicadas completas. Contudo, os MD5
repetidos mostram que várias linhas podem representar o mesmo artefacto. A
deduplicação por `md5` e a divisão por grupos são obrigatórias para evitar
leakage. Quando a mesma hash tiver rótulos incompatíveis, o conflito deve ser
reportado e removido ou resolvido com uma regra documentada.

## Perguntas para a EDA

1. Que características diferenciam `Benign` de `Malware`?
2. Quais as diferenças entre `Ransomware` e as restantes categorias?
3. Que pares de características têm correlação elevada?
4. Que variáveis apresentam assimetria e outliers suficientes para exigir
   transformação ou clipping?
5. O desempenho mantém-se quando o teste contém artefactos não vistos?
