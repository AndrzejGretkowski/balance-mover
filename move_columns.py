import csv
import glob
import datetime
from argparse import ArgumentParser
from pathlib import Path
from warnings import warn


MATCHING = {
    "Numer ewidencyjny": {"source": "POD", "type": str},
    "Nazwa odbiorcy": {"value": "Kowalski Jan"},
    "Adres instalacji": {"value": "Bajkowa 1, 75-555 Bajka"},
    "Grupa Taryfowa OSD": {
        "source": "Taryfa",
        "function": lambda x: x.replace("_", ""),
    },
    "Symbol ORCS": {"value": "ORCS070002"},
    "Rodzaj urządzenia pomiarowego": {"value": "GAZOMIERZ"},
    "Numer fabryczny": {"source": "NrGazomierza"},
    "Rodzaj odczytu": {"value": "RZEC"},
    "Data początku zużycia": {
        "source": "DataOdczytuPoprz",
    },
    "Data końca zużycia": {
        "source": "DataOdczytu",
    },
    "Wskazanie na początek": {
        "source": ["WskazanieLicznika", "ZuzycieM3"],
        "function": lambda x, y: str(float(x) - float(y)).replace(".", ","),
    },
    "Wskazanie na koniec": {"source": "WskazanieLicznika"},
    "Zużycie M3": {"source": "ZuzycieM3"},
    "Współczynnik konwersji M3 na kWh": {"source": "WspKonwersji"},
    "Zużycie kWh": {"source": "ZuzycieKWH"},
    "Data zatwierdzenia": {
        "function": lambda x: datetime.date.today().strftime("%d.%m.%Y")
    },
    "Wyliczenie współczynnika konwersji": {"value": "ORCS070002"},
}


def parse_row_data(row_data):
    write_row = []
    for key, match_rule in MATCHING.items():
        cell = None
        if "value" in match_rule:
            cell = match_rule["value"]

        if "source" in match_rule:
            if isinstance(match_rule["source"], list):
                cell = [row_data[k] for k in match_rule["source"]]
            else:
                cell = row_data[match_rule["source"]]

        if "function" in match_rule:
            if isinstance(cell, list):
                cell = match_rule["function"](*cell)
            else:
                cell = match_rule["function"](cell)

        if "type" in match_rule:
            cell = match_rule["type"](cell)

        if cell is None:
            warn(
                f"Cell {key} could not be parsed for file {input_file} -- SKIPPING FILE!"
            )
            return None

        write_row.append(cell)

    return write_row


def parse_args():
    parser = ArgumentParser(description="This does... something.")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="./*.csv",
        help="Pattern to match the files: ex. `dir/OSDN_*.dat`",
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        default="PLIKI GAZ",
        help="Output dir name",
    )
    args, _ = parser.parse_known_args()
    return args


if __name__ == "__main__":
    args = parse_args()

    out_dir = Path(args.input_path).parent / args.out
    out_dir.mkdir(exist_ok=True)
    all_files = [Path(f) for f in glob.glob(args.input)]
    this_file = Path(__file__).resolve()
    all_files_except_this_one = [p for p in all_files if p != this_file and p.is_file()]

    for input_file in all_files_except_this_one:

        with open(input_file, "rt") as f_in, open(
            out_dir / input_file.name, "wt", encoding="utf-8"
        ) as f_out:

            skip_file = False
            reader = csv.reader(f_in, delimiter=";")
            writer = csv.writer(f_out, delimiter=";", lineterminator="\n")

            header = []
            input_data = []
            for i, row in enumerate(reader):
                if i == 0:
                    header = row
                else:
                    if len(header) != len(row):
                        warn(
                            f"Input file {input_file} has a different number of columns in row {i} -- SKIPPING FILE!"
                        )
                        skip_file = True
                        break
                    input_data.append({key: value for key, value in zip(header, row)})

            if not skip_file:
                writer.writerow(MATCHING.keys())
                for row_data in input_data:
                    write_row = parse_row_data(row_data)

                    if write_row is None:
                        skip_file = True
                        break

                    writer.writerow(write_row)

        if skip_file:
            out_file = Path(out_dir / input_file.name)
            if out_file.exists():
                out_file.unlink()

    input("Press ENTER to close...")
