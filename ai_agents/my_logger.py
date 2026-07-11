import logging
import yaml,os,sys

def read_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)  # safe_load prevents code execution
            return config
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error reading file: {e}")
        sys.exit(1)
config_data = read_config("config.yaml")

logger = logging.getLogger(__name__)

log_file_name = config_data["log_file"]["name"]

logging.basicConfig(filename=log_file_name, encoding='utf-8', level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").disabled = True
logging.getLogger("httpcore").disabled = True