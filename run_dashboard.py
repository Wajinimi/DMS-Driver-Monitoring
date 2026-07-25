import yaml
from src.phase8.dashboard_server import app

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["dashboard"]

if __name__ == "__main__":
    print("Open http://%s:%s in your browser" % (cfg["host"], cfg["port"]))
    app.run(host=cfg["host"], port=cfg["port"], debug=True, use_reloader=False)