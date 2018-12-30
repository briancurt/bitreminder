import logging
import os
import random
import requests
import time
import yaml
from slackclient import SlackClient


slack_token = os.environ["SLACK_API_TOKEN"]
sc = SlackClient(slack_token)
config = yaml.safe_load(open("config.yaml"))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rcol():
    return random.randint(0, 255)


def reminder():
    bb_user = os.environ["BITBUCKET_USER"]
    bb_pass = os.environ["BITBUCKET_PASS"]
    server_url = config["general"]["server_url"]
    default_title = str(config["general"]["default_title"])

    for project_name, this_project in config["projects"].items():

        attr = []
        slack_channel = this_project["channel"]
        project_url = f"{server_url}/rest/api/1.0/projects?name={project_name}"
        r = requests.get(project_url, auth=(bb_user, bb_pass))
        project_key = r.json()["values"][0]["key"]

        for repo in this_project["repos"]:

            repo_link = f"<{server_url}/projects/{project_key}/repos/{repo}/browse|{repo}/>"
            prs_endpoint = f"{server_url}/rest/api/1.0/projects/{project_key}/repos/{repo}/pull-requests?state=OPEN"
            subtext = ""

            r = requests.get(prs_endpoint, auth=(bb_user, bb_pass))
            result_json = r.json()

            if result_json["values"]:
                for pr in result_json["values"]:

                    seconds_ago = int(time.time()) - int(str(pr["createdDate"])[:10])
                    days_ago = int(seconds_ago / 86400)
                    hours_ago = int((seconds_ago / (60 * 60)) % 24)

                    if days_ago > 1:
                        time_ago = f"{str(days_ago)} days ago"
                    elif days_ago == 1:
                        time_ago = f"{str(days_ago)} day ago"
                    elif hours_ago > 1:
                        time_ago = f"{str(hours_ago)} hours ago"
                    elif hours_ago <= 1:
                        time_ago = "Just created"

                    author = pr["author"]["user"]["name"]
                    pr_link = pr["links"]["self"][0]["href"]
                    pr_title = pr["title"]

                    subtext += f"_*{author}*, {time_ago}_ | " f"<{pr_link}|{pr_title}>\n"

                attr.append(
                    {
                        "color": "#%02X%02X%02X" % (rcol(), rcol(), rcol()),
                        "title": repo_link,
                        "text": subtext,
                        "mrkdwn_in": ["text"],
                    }
                )

        if not attr:
            default_title = "There are no pending PRs! :star:"

        sc.api_call("chat.postMessage", channel=slack_channel, text=default_title, attachments=attr)
