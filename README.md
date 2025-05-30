# FELChat – Localhost Setup Guide

This guide provides step-by-step instructions to set up the FELChat project locally, leveraging Docker and Python virtual environments.

## Prerequisites

Ensure your system has the following:

- **Python**: 3.12
- **Docker**: Installed and running
- **NVIDIA CUDA**: Installed for GPU support
- **GPU**: Available with at least 30GB of free space
- **Disk Space**: At least 30GB free

## Installation Steps

### 1. Clone the Repository

```bash
git clone -b localhost_setup2 https://github.com/navarlu/FELChat.git
cd FELChat
```

### 2. Start Docker Services

Make sure Docker is running, then start the services:

```bash
docker-compose up
```

This builds and launches the required containers.

### 3. Set Up Python Virtual Environment

Navigate to the `rag_service` folder:

```bash
cd rag_service
```

Create and activate a virtual environment called `Felchat_env`:

```bash
python3.12 -m venv Felchat_env
source Felchat_env/bin/activate  # On Windows: Felchat_env\Scripts\activate
```

### 4. Install Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Run the Server

With the virtual environment activated, run:

```bash
python server.py
```

The server should now be running and ready for use.

## Notes and Customization

### 🔧 Modify the LLM Model

You can change the model used by editing the `server.py` file located in the `rag_service` directory.

### 🌐 Running on a Remote GPU Server

If you want to deploy `server.py` on a GPU server (e.g., cloud or remote):

1. **Expose the Server**  
   Use a tunneling tool like [ngrok](https://ngrok.com/) to expose your remote server.

2. **Edit the URL**  
   Open `server.py` and update the `LLM_CHAT_SERVER_URL` variable to point to the new public address.

3. **Rebuild the Docker Service**  
   After updating the URL, rebuild the `rag-service` container:

   ```bash
   docker-compose build rag-service
   ```

4. **Restart Docker Compose**  
   Apply the changes by restarting:

   ```bash
   docker-compose up
   ```

Your FELChat instance should now be fully functional, locally or remotely.

---

For source code and more information, visit the [FELChat GitHub Repository](https://github.com/navarlu/FELChat/tree/localhost_setup2).