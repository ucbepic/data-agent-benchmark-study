# 📄 UCB Query Benchmark Study

This project is a **benchmark study of data agents (LLM-based agents) in querying distributed databases**, evaluating the capabilities of LLM-driven agents in accessing and reasoning over diverse data sources.
The agent automatically reads database connection parameters from the `.env` file, detects and loads database files, and establishes connections as needed.

## 📋 Table of Contents

- [📄 UCB Query Benchmark Study](#-ucb-query-benchmark-study)
- [🚀 Installation](#installation)
  - [Clone the repository](#clone-the-repository)
  - [Create a virtual environment](#create-a-virtual-environment)
  - [Install dependencies](#install-dependencies)
- [🗄️ Database Setup](#database-setup)
- [🔧 Configure .env](#-configure-env)
- [🚀 Run the Benchmark](#-run-the-benchmark)
  - [📂 Run our provided agent on our datasets](#-run-our-provided-agent-on-our-datasets)
  - [📂 Run your own agent on our datasets](#-run-your-own-agent-on-our-datasets)
    - [How to load the databases in your own agent with our tools](#how-to-load-the-databases-in-your-own-agent)
    - [🔴 If you prefer not to use our agent_tools and db_utils](#-if-you-prefer-not-to-use-our-agent_tools-and-db_utils)
  - [📂 Run on your own datasets](#-run-on-your-own-datasets)

---
## Installation
### Clone the repository
```bash
git clone https://github.com/Ruiqi-Chen-0216/UCB_Query.git
cd UCB_Query

```
### Create a virtual environment
It is recommended to use a dedicated virtual environment named `ucb_query`:
Using conda:
```bash
conda create -n ucb_query python=3.9
conda activate ucb_query
```

### Install dependencies
Install Python dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```
---
## Database Setup
This project interacts with distributed databases, combining both server-based and file-based databases.
You need to ensure the required services are running and files are available.

#### ✅ PostgreSQL
- Requires a **local PostgreSQL server** to be installed and running.  
- Install [PostgreSQL](https://www.postgresql.org/) on your machine according to your operating system.
- After installation, start the PostgreSQL server. Verify that you can connect using:
  ```bash
  psql -U postgres
  ```
- The agent reads PostgreSQL connection parameters from the `.env` file.

#### ✅ MongoDB
- Requires a **local MongoDB server** to be installed and running.  
- Install [MongoDB Community Edition](https://www.mongodb.com/) on your machine according to your operating system.
- After installation, start the MongoDB server. Verify that you can connect.
- The agent reads the MongoDB connection string (`MONGO_URI`) from the `.env` file.

#### 📄 SQLite & DuckDB 
- Does **not** require a separate service.
- The agent automatically detects and loads the `.db` files directly from the filesystem.

Only **PostgreSQL** and **MongoDB** require you to have their respective servers running locally (or accessible on a specified host). Please make sure both database services are properly installed and configured **before running the project**. 
**SQLite** and **DuckDB** work as standalone files — no separate server installation is needed for them.
Although MySQL is no longer the default choice, it is still supported and can be used if desired.

---
## 🔧 Configure .env 
Create a `.env` file in the project root directory with your actual credentials.
Here is an example:

```env
# PostgreSQL configuration
PG_CLIENT=your_local_psql.exe_path
PG_USER=postgres
PG_PASSWORD=your_password
PG_HOST=localhost
PG_PORT=5432
PG_DB=mydb

# MongoDB configuration
MONGO_URI=mongodb://localhost:27017/
# If your MongoDB requires authentication, use a URI like:
MONGO_URI=mongodb://username:password@localhost:27017/?authSource=admin

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Azure
AZURE_API_BASE=https://your-resource-name.openai.azure.com/
AZURE_API_KEY=your_azure_api_key_here
AZURE_API_VERSION=2023-05-15

```
You only need to provide the API key for either OpenAI, Azure OpenAI, or another provider, depending on the service you’re using.

---
## 🚀 Run the Benchmark
This benchmark can be run in two ways:  
✅ Run on the provided datasets 
- Using our provided agent
- Using your own agent
  
✅ Run on your own custom dataset

### 📂 Run our provided agent on our datasets
We have prepared **five datasets** for this benchmark study: `GoogleLocal`, `BookReview`, `Yelp`, `StockIndex`, `StockMarket`.

Each dataset corresponds to a folder in the project directory.  
To run the benchmark on a specific dataset, simply execute the `run_experiments.py` script located in that folder.  

Example:
```bash
cd query_yelp
python run_experiments.py
```

### 📂 Run your own agent on our datasets

If you want to implement and run **your own agent** (instead of using the provided baseline agent), you can still leverage the built-in database loading and management logic from this project.  
We have already encapsulated all the database initialization and checking into a few utility functions under `common_scaffold/`, so you don’t need to manually connect or verify the databases.


####  How to load the databases in your own agent

You can simply include the following lines in your agent code:

```python
from common_scaffold.agent_tools import auto_ensure_databases
import yaml

with open("db_config.yaml", "r") as f:
    db_config = yaml.safe_load(f)

db_clients = db_config["db_clients"]
auto_ensure_databases(db_clients)

print(f"\n✅ DB connections ready: {db_clients.keys()}")
```
Just make sure to pass the path to the appropriate `db_config.yaml` file in your dataset folder.

After these three lines execute, all databases defined in `db_config.yaml` will be automatically initialized and connected.

Once done, you can also use `agent_tools.list_dbs()` and `agent_tools.query_db()` to interact with the databases seamlessly — they will use the correct connections under the hood.

You only need to make sure to **correctly fill in the MongoDB and PostgreSQL connection parameters in the `.env` file** — the rest is handled automatically.


#### What happens under the hood?

✅ **Load database configuration from `db_config.yaml`**  
Reads the file to get the database paths and formats.

✅ **Run `auto_ensure_databases`**  
This calls:
- `common_scaffold/agent_tools/auto_db_check.py` — detects the database format and checks if the database is ready.
- `common_scaffold/db_utils/loader.py: ensure_db()` — makes sure the database exists and a connection is established.
- `common_scaffold/db_utils/<db>_utils.py` — format-specific utilities that verify and establish the connection if it doesn’t already exist.

If the database is being used for the first time:
- It checks if the database files or connections exist.
- If not, it sets up the connections (for PostgreSQL/MongoDB) and imports the database if needed.


#### Notes

- You **do not need to manually connect to PostgreSQL, MySQL, MongoDB, SQLite, or DuckDB** — all handled automatically.
- If the required local services (PostgreSQL/MongoDB) are not running, the utilities will alert you.
- You can always refer to `common_scaffold/agent_tools/agent_baseline.py` as a full example.

#### 🔴 If you prefer not to use our `agent_tools` and `db_utils`
If you prefer to **only load the databases and run queries yourself** — without relying on the provided `agent_tools` and `db_utils` — you can still use the project’s database configurations and follow the standard connection methods.


**Steps to connect manually**

You still need to initialize the databases by reading the `db_config.yaml` and calling `auto_ensure_databases` (to ensure databases are ready and imported if needed).  
After that, you can use standard Python libraries to connect and query each database directly.


Step 1: Initialize the databases

```python
from common_scaffold.agent_tools import auto_ensure_databases
import yaml

with open("db_config.yaml", "r") as f:
    db_config = yaml.safe_load(f)

db_clients = db_config["db_clients"]
auto_ensure_databases(db_clients)

print(f"\n✅ DB connections ready: {db_clients.keys()}")
```
This ensures all the databases defined in `db_config.yaml` are ready.

Step 2: Query the databases manually

For SQLite: 
Load the config and use the path from `db_config["db_clients"]["review_dataset"]["db_path"]` to connect:
```python
import sqlite3
import pandas as pd

db_path = SQLITE_DB_PATH_FROM_CONFIG

conn = sqlite3.connect(db_path)
df = pd.read_sql_query(sql, conn)
conn.close()
```

For DuckDB: 
Similarly, load the DuckDB file path from the config and connect:
```python
import duckdb
from pathlib import Path

db_path = DUCKDB_PATH_FROM_CONFIG
db_file = Path(db_path)
if not db_file.exists():
    raise FileNotFoundError(f"DuckDB file not found: {db_path}")

conn = duckdb.connect(database=str(db_file))
df = conn.execute(sql).fetchdf()
conn.close()
```

For MongoDB: 
Use the `MONGO_URI` from your `.env` (or config) to connect:
```python
from pymongo import MongoClient

client = MongoClient(MONGO_URI)
db = client[db_name]

cursor = db[collection].find(query, projection).limit(limit)
data = list(cursor)

client.close()
```

For PostgreSQL:
Use the PostgreSQL config to construct the URI and connect:
```python
from sqlalchemy import create_engine, text
import pandas as pd

# fallback to config if db_name is not provided
db_name = PG_DB_FROM_CONFIG

uri = (
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}"
    f"@{PG_HOST}:{PG_PORT}/{db_name}"
)

engine = create_engine(uri)

with engine.connect() as conn:
    df = pd.read_sql(text(sql), conn, params=None)
```
**Notes**

- These examples assume you have already run `auto_ensure_databases()` to ensure databases and connections are properly set up.
- The `agent_tools` and `db_utils` already encapsulate these steps for you — if you use them, you don’t need to write these manually.
- You may refer to the respective `<db>_utils.py` under `common_scaffold/db_utils/` for implementation details.


### 📂 Run on your own datasets

You can also run our benchmark on your own dataset by following these steps:

1️⃣ Prepare your dataset folder

Create a new folder under the project root, e.g., `MyDataset`, with the following structure:
```
MyDataset/
    ├── query_dataset/               <- Your data, stored in a supported format (MySQL, MongoDB, SQLite, or DuckDB)
    ├── db_description.txt           <- A plain text description of the database
    ├── db_config.yaml               <- Basic database configuration (used for agent initialization and connection)
    ├── query_folder/
    │       ├── query.json           <- Benchmark queries
    │       ├── ground_truth.csv     <- Ground truth answers
    │       └── validation.py        <- Script to validate agent results against ground truth
    └──run_experiments.py            <- Copy an existing run_experiments.py here and adjust if needed
```
2️⃣ Notes

- Make sure your datasets in `query_dataset/` is in the supported database formats: **PostgreSQL**， **MySQL**, **MongoDB**, **SQLite**, or **DuckDB**. 
- You can use the existing datasets (`GoogleLocal`, `StockMarket`, etc.) as templates for all these files.
- The `run_experiments.py` script and related modules in `common_scaffold/agent_tools` and `common_scaffold/db_utils` already implement the core logic — you just need to prepare your data and config.

3️⃣ Run the benchmark
Once everything is ready, run:
```bash
cd MyDataset
python run_experiments.py
```
