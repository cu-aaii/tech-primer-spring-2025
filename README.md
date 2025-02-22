# Streamlit Template

This repository contains a development environment that is provided as an easy starting point for AI Innovation Lab members to use throughout their time with the lab

Use of this dev environment is required to allow lab members to all easily work together. It also offers great standard rapid prototyping tools that will accelerate your development while not having to think about fine details like how to build a UI or API backend. You can also be assured that your teammates will all have the same environment and spend less time troubleshooting, and more time hacking!

The other advantage is that the staff team can easily deploy these prototypes to the cloud so that any of our customers can access and test them.

# Getting Started

## Prerequisites

Using this development environment has a few prerequisites:

1. [Install Docker Desktop](https://www.docker.com/get-started/) on your computer (no need to create an account)
2. [Install VS Code](https://code.visualstudio.com/download) on your computer
3. Install the "Dev Containers" extension inside VS Code
4. [Install the AWS CLI V2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) on your computer (v2 is required, v1 will not work)

## Starting the Dev Container

1. Open VS Code, clone this repository to your local machine and open it
2. **Before doing anything** create a .env file in the root of the repo, it can just be empty with a comment like the following, or you can add other environment variables if you'd like

```
# my .env file


```

3. In the bottom left corner of VS Code, click the green button and select "Reopen in Container" from the menu
4. Wait for some time while the Dev Container environment is built on your machine
5. Once the process is complete, you should see a file tree and open a terminal within the Dev Container workspace!

⛔️ if you get an error like the following, you likely did not create a `.env` file in step 2. You will need to delete the .env directories that got created under the following directories:

```
Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error mounting "/host_mnt/Users/mjs472/repos/ai-hackathon-2025/.env" to rootfs at "/code/.env": mount /host_mnt/Users/mjs472/repos/ai-hackathon-2025/.env:/code/.env (via /proc/self/fd/6), flags: 0x5000: not a directory: unknown: Are you trying to mount a directory onto a file (or vice-versa)? Check if the specified host path exists and is the expected type
```

1. the repo root directory (./.env)
2. the streamlit-app directory (./streamlit-app/.env)
3. the fastapi-app directory (./fastapi-app/.env)

Once you delete these, try to "Reopen in Container" again.

*Additional Note:* When working with Docker to build or deploy applications, it’s essential to ensure your system has sufficient resources allocated, such as memory and disk space. Resource limitations can lead to issues like "At least one invalid signature was encountered", failed builds, or repository update errors. These problems might not necessarily relate to the image, dependencies, or your code, but rather insufficient memory or storage constraints causing corruption/errors during downloads or signature verifications.

1. Allocate More Memory and CPU to Docker (When Using Docker Desktop):
    - Go to Docker Desktop → Settings → Resources.
    - Adjust Memory limit and Disk usage limit appropriately.
2. Free Up Docker-Related Disk Space:
    - If your disk space is limited, Docker might fail to allocate space leading to unexpected errors. Run the following commands to clean up unused images and containers: `docker image prune -f`, `docker container prune -f`.
    - These commands help reclaim storage by removing unused Docker images, dangling containers, unused volumes, and stale build caches.
3. Check Overall System Resources:
    - Ensure that your host system (Mac, Windows, or Linux) has sufficient available memory free during builds (especially on systems with less than 8 GB of RAM). If needed, close unused applications or processes to free up resources.

*Example:* If you encounter an error like this during `apt-get update` or package installation:

`W: GPG error: http://deb.debian.org/debian buster InRelease: At least one invalid signature was encountered.`

`E: The repository 'http://deb.debian.org/debian buster InRelease' is not signed.`, then cleaning Docker system resources as mentioned above can help fix this issue potentially.

## Making code available to all components

The `thisapp` directory is set up so that all running components will have access to the python code underneath as a module.

For example, if you wanted to create a FastAPI backend and Streamlit frontend that both use a common Pydantic model named `MyModel`, you could define it under the `thisapp` directory in a python file named `thisapp/my_model.py` and then both apps can simply do `from thisapp.my_model import MyModel` and have access to the same code!

## Available Technologies

### Jupyter Notebooks

Under the `notebooks/` directory, you can create python notebooks. Simply create a new file named `<filename>.ipynb` and you can open it from the file navigator. This will allow you to edit and run code in the notebook right inside VS Code!

⚠️ Be sure to choose the correct Kernel in the Jupyter Notebook, it should be something similar to `Python 3.12.8`

### Streamlit

Streamlit is a powerful web UI prototyping tool that works in pure python. You can create chatbots, forms with a rich set of inputs, complex layouts, etc. all that work within a web browser!

The dev environment has a separate container running the streamlit app in the background. It will be running on a random port assigned by Docker Desktop on your local machine so you can open your browser and navigate to `http://localhost:<port-from-docker-desktop>/` to test it out.

The code for the Streamlit app is under `streamlit-app/app`. Any updates to the `streamlit-app/app/Home.py` or adjacent files will be automatically detected and reload the streamlit server, so you can easily make changes and test them live!

### FastAPI

FastAPI is a powerful asynchronous API building library. You can build a custom API for your application with this!

Documentation: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)

The dev environment has a separate container running the FastAPI server in the background. It will be running on a random port assigned by Docker Desktop on your local machine so you can open your browser and navigate to `http://localhost:<port-from-docker-desktop>/docs` to see the available endpoints and to test them out! You can also use something like `curl` from your local machine too to call the api endpoints via CLI, or obviously, you can call them with something like the requests module in python!

The code for the FastAPI app is under `fastapi-app/app`. Any updates to the `fastapi-app/app/server.py` or adjacent files will be automatically detected and reload the FastAPI server, so you can easily make changes and test them live!

⚠️ If you try to connect to FastAPI from within another container, like the Streamlit app, you need to use the container name as the hostname and its native port of 8000 instead of `localhost:<port-from-docker-desktop>`. e.g. `https://fastapi:8000/my-api-endpoint`

### Neo4j

Neo4j is a graph database that allows us to store and query data in a graph format. This can be useful for storing data that has relationships between entities, such as social networks, recommendation systems, and knowledge graphs.

Documentation: [https://neo4j.com/docs/](https://neo4j.com/docs/)

The dev environment has a separate container running the Neo4j server in the background. The graph db server that you can connect to from code is running on port 7687. The db web interface that you can access via your browser is running on a random port assigned by Docker Desktop (open the dashboard to find a link to it). You can navigate to `http://localhost:<port-from-docker-desktop>` and log in!

Username: `neo4j`
Password: `secretpassword`

⚠️ If you try to connect to the neo4j server from within another container, like the streamlit app or the fastapi app, you need to use the container name as the hostname instead of `localhost` and the native port inside the container of 7687. e.g. `neo4j://neo4j:7687`

### Available Python Modules

Many common frameworks and libraries are already installed in the dev environment for your use. These include things like:

* Pydantic
* LangChain
* LangGraph
* Llama-Index 
* ChromaDB (for in-memory vector db)
* Neo4j (for graph db, see above for how to connect)
* PyTorch & Ray
* Matplotlib, Plotly, Seaborn (for visualization)
* Pandas
* GeoPandas, CartoPy, GDAL (for maps / geospatial data)
* Huggingface Transformers and Diffusers
* NumPy, SciPy, Dask
* Scikit-learn
* FFMPEG
* OpenCV-Python
* Mediapipe
* xgboost, nltk (and other various ML-related modules)
* Others, check out `pyproject.toml` for the full list

If you are missing a Python module you would like to use, it can be added as a dependency in the `pyproject.toml` file, running `poetry lock`, and rebuilding the Dev Container. 

To add native libraries, the `Dockerfile` can be updated to install via the `apt` package manager and rebuilding the Dev Container. You could also update the Dockerfile to download, build and install something from source in a pinch.

Feel free to ask hackathon staff for assistance.
