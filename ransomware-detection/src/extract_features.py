"""Extract static PE features from Windows executables and ZIP archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import zipfile
from pathlib import Path
from typing import BinaryIO

import pandas as pd
import pefile

MAX_PE_SIZE = 50 * 1024 * 1024
MAX_ARCHIVE_SIZE = 250 * 1024 * 1024
MAX_ARCHIVE_MEMBER_SIZE = 50 * 1024 * 1024
MAX_ARCHIVE_TOTAL_SIZE = 500 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 500

DOS_FEATURES = {
    "bytes_on_last_page": "e_cblp",
    "pages_in_file": "e_cp",
    "relocations": "e_crlc",
    "size_of_header": "e_cparhdr",
    "min_extra_paragraphs": "e_minalloc",
    "max_extra_paragraphs": "e_maxalloc",
    "init_ss_value": "e_ss",
    "init_sp_value": "e_sp",
    "init_ip_value": "e_ip",
    "init_cs_value": "e_cs",
    "over_lay_number": "e_ovno",
    "oem_identifier": "e_oemid",
    "address_of_ne_header": "e_lfanew",
}

OPTIONAL_FEATURES = {
    "SizeOfCode": "SizeOfCode",
    "SizeOfInitializedData": "SizeOfInitializedData",
    "SizeOfUninitializedData": "SizeOfUninitializedData",
    "AddressOfEntryPoint": "AddressOfEntryPoint",
    "BaseOfCode": "BaseOfCode",
    "BaseOfData": "BaseOfData",
    "ImageBase": "ImageBase",
    "SectionAlignment": "SectionAlignment",
    "FileAlignment": "FileAlignment",
    "OperatingSystemVersion": "MajorOperatingSystemVersion",
    "ImageVersion": "MajorImageVersion",
    "SizeOfImage": "SizeOfImage",
    "SizeOfHeaders": "SizeOfHeaders",
    "Checksum": "CheckSum",
    "Subsystem": "Subsystem",
    "DllCharacteristics": "DllCharacteristics",
    "SizeofStackReserve": "SizeOfStackReserve",
    "SizeofStackCommit": "SizeOfStackCommit",
    "SizeofHeapCommit": "SizeOfHeapCommit",
    "SizeofHeapReserve": "SizeOfHeapReserve",
    "LoaderFlags": "LoaderFlags",
}

SECTION_FEATURES = (
    "VirtualSize",
    "VirtualAddress",
    "SizeOfRawData",
    "PointerToRawData",
    "PointerToRelocations",
    "PointerToLineNumbers",
    "Characteristics",
)

MACHINE_TYPES = {
    0x014C: "Intel 386 or later, and compatibles",
    0x8664: "AMD AMD64",
    0x01C0: "ARM little endian",
    0x01C4: "ARM Thumb-2 little endian",
    0xAA64: "ARM64 little endian",
}


def _numeric(value: object) -> int | float:
    if isinstance(value, float) and not math.isfinite(value):
        return math.nan
    return int(value) if value is not None else math.nan


def _read_bytes(stream: BinaryIO, size: int) -> bytes:
    if size > MAX_PE_SIZE:
        raise ValueError(f"Executável excede o limite de {MAX_PE_SIZE // (1024 * 1024)} MiB.")
    data = stream.read(MAX_PE_SIZE + 1)
    if len(data) > MAX_PE_SIZE:
        raise ValueError(f"Executável excede o limite de {MAX_PE_SIZE // (1024 * 1024)} MiB.")
    return data


def _parse_pe(data: bytes, filename: str) -> dict[str, object]:
    if len(data) < 2 or data[:2] != b"MZ":
        raise ValueError(f"{filename} não tem cabeçalho MZ de executável Windows.")
    try:
        pe = pefile.PE(data=data, fast_load=True)
    except (pefile.PEFormatError, IndexError, struct.error) as exc:
        raise ValueError(f"Não foi possível ler o formato PE de {filename}: {exc}") from exc

    features: dict[str, object] = {
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "file_extension": "exe",
        "EntryPoint": math.nan,
        "PEType": "Unknown",
        "MachineType": "Unknown",
        "magic_number": "MZ",
        "Magic": "Unknown",
    }

    for feature, attribute in DOS_FEATURES.items():
        features[feature] = _numeric(getattr(pe.DOS_HEADER, attribute, None))

    machine = int(pe.FILE_HEADER.Machine)
    features["MachineType"] = MACHINE_TYPES.get(machine, f"Unknown ({machine})")

    optional = pe.OPTIONAL_HEADER
    magic = int(optional.Magic)
    pe_type = {0x10B: "PE32", 0x20B: "PE32+"}.get(magic, f"Unknown (0x{magic:X})")
    features["PEType"] = pe_type
    features["Magic"] = pe_type
    features["EntryPoint"] = _numeric(optional.AddressOfEntryPoint)
    for feature, attribute in OPTIONAL_FEATURES.items():
        features[feature] = _numeric(getattr(optional, attribute, None))

    for section in pe.sections:
        raw_name = section.Name.split(b"\0", 1)[0].decode("ascii", errors="ignore")
        name = raw_name.lstrip(".").lower()
        if name not in {"text", "rdata"}:
            continue
        for attribute in SECTION_FEATURES:
            pe_attribute = {
                "VirtualSize": "Misc_VirtualSize",
                "PointerToLineNumbers": "PointerToLinenumbers",
            }.get(attribute, attribute)
            features[f"{name}_{attribute}"] = _numeric(
                getattr(section, pe_attribute, None)
            )

    return features


def _feature_row(data: bytes, source_file: str, schema: list[str]) -> dict[str, object]:
    values = _parse_pe(data, source_file)
    return {
        "source_file": source_file,
        "md5": values["md5"],
        "sha1": values["sha1"],
        **{column: values.get(column, math.nan) for column in schema},
    }


def load_schema(schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if (
        not isinstance(schema, list)
        or not schema
        or any(not isinstance(column, str) for column in schema)
        or len(schema) != len(set(schema))
    ):
        raise ValueError(f"Schema de features inválido: {schema_path}")
    return schema


def extract_file(input_path: Path, schema: list[str]) -> pd.DataFrame:
    if not input_path.is_file():
        raise FileNotFoundError(f"Ficheiro não encontrado: {input_path}")

    rows: list[dict[str, object]] = []
    if input_path.suffix.lower() == ".zip":
        if input_path.stat().st_size > MAX_ARCHIVE_SIZE:
            raise ValueError("O ZIP excede o limite de 250 MiB.")
        try:
            with zipfile.ZipFile(input_path) as archive:
                members = archive.infolist()
                if len(members) > MAX_ARCHIVE_MEMBERS:
                    raise ValueError(
                        f"O ZIP excede o limite de {MAX_ARCHIVE_MEMBERS} entradas."
                    )
                total_size = 0
                for member in members:
                    if member.is_dir() or Path(member.filename).suffix.lower() != ".exe":
                        continue
                    if member.file_size > MAX_ARCHIVE_MEMBER_SIZE:
                        raise ValueError(
                            f"{member.filename} excede o limite de 50 MiB."
                        )
                    total_size += member.file_size
                    if total_size > MAX_ARCHIVE_TOTAL_SIZE:
                        raise ValueError("O tamanho descomprimido do ZIP excede 500 MiB.")
                    data = archive.read(member)
                    source_file = f"{input_path.name}!{member.filename}"
                    rows.append(_feature_row(data, source_file, schema))
        except zipfile.BadZipFile as exc:
            raise ValueError(f"Arquivo ZIP inválido: {input_path}") from exc
    elif input_path.suffix.lower() == ".exe":
        if input_path.stat().st_size > MAX_PE_SIZE:
            raise ValueError("O executável excede o limite de 50 MiB.")
        with input_path.open("rb") as stream:
            data = _read_bytes(stream, input_path.stat().st_size)
        rows.append(_feature_row(data, input_path.name, schema))
    else:
        raise ValueError("Formato não suportado. Seleciona um .exe ou um .zip.")

    if not rows:
        raise ValueError("Não foram encontrados executáveis .exe no ficheiro ZIP.")
    feature_columns = [
        column
        for column in schema
        if column not in {"source_file", "md5", "sha1"}
    ]
    return pd.DataFrame(
        rows, columns=["source_file", "md5", "sha1", *feature_columns]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrai features estáticas PE de executáveis .exe e ZIPs."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("models/ransomware/feature_schema.json"),
    )
    args = parser.parse_args()

    schema = load_schema(args.schema)
    features = extract_file(args.input, schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(args.output, index=False)
    print(f"Extraídas {len(features)} amostras PE para {args.output}")
    print(
        "Aviso: as features comportamentais (rede, registo e processos) "
        "não são observadas pela análise estática e ficam em falta."
    )


if __name__ == "__main__":
    main()
