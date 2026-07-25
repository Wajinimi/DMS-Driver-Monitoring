import yaml
from src.phase8.dashboard_server import app

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["dashboard"] #loading the dashboard configuration from the configuration file
print("Step 1 OK -  Flask app created")  #this is the text messahge to confirm the app is created
print("Dashbaord will run at http://%s:%s" % (cfg["host"], cfg["port"])) 

with app.test_client() as client: #testing the health endpoint
    resp = client.get("/health") #this is the endpoint i created in the dashboard_server.py file
    print("Health check:", resp.get_json()) #this is the response from the health endpoint