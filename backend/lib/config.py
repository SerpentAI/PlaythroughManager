import yaml
import yaml.scanner

config = dict()

try:
    with open("config/config.yml", "r") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.scanner.ScannerError as e:
            raise Exception("Configuration file at 'config/config.yml' contains invalid YAML...")
        except Exception as e:
            print(type(e))
except FileNotFoundError as e:
    raise Exception("Configuration file not found at: 'config/config.yml'...")
