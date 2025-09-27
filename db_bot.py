import json
from openai import OpenAI
import os
import pymysql
from time import time

print("Running db_bot.py!")

fdir = os.path.dirname(__file__)


def getPath(fname):
    return os.path.join(fdir, fname)


# SQL FILES
setupSqlPath = getPath("setup_tables.sql")
setupSqlDataPath = getPath("setup_data.sql")

# Read setup scripts
with open(setupSqlPath) as setupSqlFile, open(setupSqlDataPath) as setupSqlDataFile:
    setupSqlScript = setupSqlFile.read()
    setupSQlDataScript = setupSqlDataFile.read()

# ---- MySQL connection (PyMySQL) ----
configPath = getPath("config.json")
print(configPath)
with open(configPath) as configFile:
    config = json.load(configFile)

mysql_cfg = config["mysql"]
conn = pymysql.connect(
    host=mysql_cfg.get("host", "localhost"),
    port=int(mysql_cfg.get("port", 3306)),
    user=mysql_cfg["user"],
    password=mysql_cfg["password"],
    database=mysql_cfg["database"],
    autocommit=False,  # we'll commit after running setup scripts
    charset="utf8mb4",
    cursorclass=pymysql.cursors.Cursor,
)
cur = conn.cursor()


# Helper to run a multi-statement SQL script (naive splitter by ';')
def run_script(script: str):
    # Strip MySQL DELIMITER lines if present (not expected in your schema, but safe)
    cleaned = []
    for line in script.splitlines():
        if line.strip().upper().startswith("DELIMITER "):
            continue
        cleaned.append(line)
    script = "\n".join(cleaned)

    # Split on semicolons that end statements
    for stmt in script.split(";"):
        if stmt.strip():
            cur.execute(stmt)
    conn.commit()


# Build schema and seed data
run_script(setupSqlScript)
run_script(setupSQlDataScript)


def runSql(query):
    cur.execute(query)
    return cur.fetchall()


# OPENAI
configPath = getPath("config.json")
print(configPath)

openAiClient = OpenAI(api_key=config["openaiKey"])
openAiClient.models.list()  # check if the key is valid (update in config.json)


def getChatGptResponse(content):
    stream = openAiClient.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        stream=True,
    )

    responseList = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            responseList.append(chunk.choices[0].delta.content)

    result = "".join(responseList)
    return result


# strategies
commonSqlOnlyRequest = " Give me a MySQL select statement that answers the question. Only respond with SQL. If there is an error do not explain it! (Note: In golf, lower scores are better, and higher scores are worse.)"
strategies = {
    "zero_shot": setupSqlScript + commonSqlOnlyRequest,
    "single_domain_double_shot": (
        setupSqlScript
        + "EXAMPLE:\n"
        + " How many left-handed golfers own any TaylorMade golf clubs? "
        + " \nSELECT COUNT(DISTINCT p.player_id) AS left_handed_taylormade_owners\n"
        + "FROM Player p\n"
        + "JOIN GolfBag gb ON gb.bag_id = p.golf_bag_id\n"
        + "JOIN GolfClub gc ON gc.bag_id = gb.bag_id\n"
        + "JOIN Brand b ON b.brand_id = gc.brand_id\n"
        + "WHERE p.handedness = 'Left'\n"
        + "  AND LOWER(b.name) LIKE '%taylormade%'\n "
        + commonSqlOnlyRequest
    ),
}


questions = [
    "Which player had the best overall score in the first match?",
    "Which team had the best overall score?",
    "Which player should be kicked off of each team based on their scores?",
    "Which golf brand is the most popular?",
    "Which match had the most birdies (one stroke below par)?",
    "Which players (if any) didn't participate in any matches?",
    "Does golf ball hardness have a significant effect in players' scores?",
    "Which golf course seems to be the most difficult for players with Callaway drivers?",
]


def sanitizeForJustSql(value):
    gptStartSqlMarker = "```sql"
    gptEndSqlMarker = "```"
    if gptStartSqlMarker in value:
        value = value.split(gptStartSqlMarker)[1]
    if gptEndSqlMarker in value:
        value = value.split(gptEndSqlMarker)[0]

    return value


for strategy in strategies:
    responses = {"strategy": strategy, "prompt_prefix": strategies[strategy]}
    questionResults = []
    print("########################################################################")
    print(f"Running strategy: {strategy}")
    for question in questions:

        print(
            "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        )
        print("Question:")
        print(question)
        error = "None"
        try:
            getSqlFromQuestionEngineeredPrompt = strategies[strategy] + " " + question
            sqlSyntaxResponse = getChatGptResponse(getSqlFromQuestionEngineeredPrompt)
            sqlSyntaxResponse = sanitizeForJustSql(sqlSyntaxResponse)
            print("SQL Syntax Response:")
            print(sqlSyntaxResponse)
            queryRawResponse = str(runSql(sqlSyntaxResponse))
            print("Query Raw Response:")
            print(queryRawResponse)
            friendlyResultsPrompt = (
                'I asked a question "'
                + question
                + '" and the response was "'
                + queryRawResponse
                + '" Please, just give a concise response in a more friendly way? Please do not give any other suggests or chatter.'
            )
            betterFriendlyResultsPrompt = (
                'I asked a question: "'
                + question
                + '" and I queried this database '
                + setupSqlScript
                + " with this query "
                + sqlSyntaxResponse
                + '. The query returned the results data: "'
                + queryRawResponse
                + '". Could you concisely answer my question using the results data?'
            )
            friendlyResponse = getChatGptResponse(betterFriendlyResultsPrompt)
            print("Friendly Response:")
            print(friendlyResponse)
        except Exception as err:
            error = str(err)
            print(err)

        questionResults.append(
            {
                "question": question,
                "sql": sqlSyntaxResponse,
                "queryRawResponse": queryRawResponse,
                "friendlyResponse": friendlyResponse,
                "error": error,
            }
        )

    responses["questionResults"] = questionResults

    with open(getPath(f"response_{strategy}_{time()}.json"), "w") as outFile:
        json.dump(responses, outFile, indent=2)


cur.close()
conn.close()
print("Done!")
