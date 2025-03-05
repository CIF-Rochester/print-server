
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
    printer_name: str

@dataclass
class PrintLimitations:
    max_pages: int
    discord_threshold: int

@dataclass
class Nauticock:
    username: str
    password: str
    ip: str
    command: str

@dataclass
class Citadel:
    username: str
    password: str
    ip: str

@dataclass
class Config:
    logging: Logging
    printer: Printer
    print_limitations: PrintLimitations
    nauticock: Nauticock
    citadel: Citadel

def load_config(config_path: os.PathLike):
    try:
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
    except Exception as e:
        print(f"Failed to load config file from {config_path}: {e}", file=sys.stderr)
        exit(1)
    try:
        logging = Logging(log_path=cfg.get("logging","log_path"), file_storage_path=cfg.get("logging","file_storage_path"), file_storage_time=cfg.getint("logging","file_storage_time"))
        printer = Printer(printer_name=cfg.get("printer","printer_name"))
        print_limitations = PrintLimitations(max_pages=cfg.getint("print_limitations","max_pages"), discord_threshold=cfg.getint("print_limitations", "discord_threshold"))
        nauticock = Nauticock(username=cfg.get("nauticock", "username"), password=cfg.get("nauticock","password"),ip=cfg.get("nauticock","ip"),command=cfg.get("nauticock","command"))
        citadel = Citadel(username=cfg.get("citadel","username"), password=cfg.get("citadel","password"),ip=cfg.get("citadel","ip"))
        config = Config(logging=logging, printer=printer, print_limitations=print_limitations, nauticock=nauticock, citadel=citadel)
    except Exception as e:
        print(f"Error in config file {config_path}: {e}", file=sys.stderr)
        exit(1)
    return config