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
        "function": lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").strftime("%Y-%m-%d"),
    },
    "Data końca zużycia": {
        "source": "DataOdczytu",
        "function": lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").strftime("%Y-%m-%d"),
    },
    "Wskazanie na początek": {
        "source": ["WskazanieLicznika", "ZuzycieM3"],
        "function": lambda x, y: str(int(x) - int(y)),
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


def parse_row_data(row_data, input_file):
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
        default="*.csv",
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

    all_files = glob.glob(args.input)

    this_file = Path(__file__).resolve()
    all_files = [Path(f) for f in all_files]
    all_files_except_this_one = [p for p in all_files if p != this_file and p.is_file()]

    out_dir = Path(args.input).parent / args.out
    out_dir.mkdir(exist_ok=True)

    for input_file in all_files_except_this_one:

        with open(input_file, "rt", encoding="utf8", errors="ignore") as f_in, open(
            out_dir / input_file.name, "wt", encoding="utf-8"
        ) as f_out:

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
                    input_data.append({key: value for key, value in zip(header, row)})

            writer.writerow(MATCHING.keys())
            for row_data in input_data:

                try:
                    write_row = parse_row_data(row_data, input_file)

                except Exception as e:
                    write_row = None
                    warn(f"Input file {input_file} causes an error: {e}")

                if write_row is None:
                    writer.writerow([])
                else:
                    writer.writerow(write_row)

    input("Press ENTER to close...")
