
import os
import sys
import configparser
from dataclasses import dataclass

@dataclass
class Logging:
    log_path: os.PathLike
    file_storage_path: os.PathLike
    file_storage_time: int

@dataclass
class Printer:
    color_printer_name: str
    bw_printer_name: str

@dataclass
class PrintLimitations:
    max_pages: int
    discord_threshold: int

@dataclass
class Database:
    username: str
    password: str
    database: str
    table: str

@dataclass
class IPA:
    username: str
    password: str
    ip: str

@dataclass
class Config:
    logging: Logging
    printer: Printer
    print_limitations: PrintLimitations
    database: Database
    ipa: IPA

def load_config(config_path: os.PathLike):
    try:
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
    except Exception as e:
        print(f"Failed to load config file from {config_path}: {e}", file=sys.stderr)
        exit(1)
    try:
        logging = Logging(log_path=cfg.get("logging","log_path"), file_storage_path=cfg.get("logging","file_storage_path"), file_storage_time=cfg.getint("logging","file_storage_time"))
        printer = Printer(color_printer_name=cfg.get("printer","color_printer_name"), bw_printer_name=cfg.get("printer","bw_printer_name"))
        print_limitations = PrintLimitations(max_pages=cfg.getint("print_limitations","max_pages"), discord_threshold=cfg.getint("print_limitations", "discord_threshold"))
        database = Database(username=cfg.get("database", "username"), password=cfg.get("database", "password"), database=cfg.get("database", "database"), table=cfg.get("database", "table"))
        ipa = IPA(username=cfg.get("ipa","username"), password=cfg.get("ipa","password"),ip=cfg.get("ipa","ip"))
        config = Config(logging=logging, printer=printer, print_limitations=print_limitations, database=database, ipa=ipa)
    except Exception as e:
        print(f"Error in config file {config_path}: {e}", file=sys.stderr)
        exit(1)
    return config
