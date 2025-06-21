# Getting Started with AWS FinOps Dashboard

This guide will help you set up and start using the AWS FinOps Dashboard with AI capabilities.

## Prerequisites

Before getting started, make sure you have the following installed:

1. **Python 3.12**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure you can run it with `python3.12 --version`

2. **Docker and Docker Compose**
   - For running PostgreSQL database
   - Follow the [Docker installation guide](https://docs.docker.com/get-docker/)

3. **AWS Account with Cost Explorer API Access**
   - You'll need an AWS IAM user with permissions to access Cost Explorer API
   - Generate an access key and secret key for this user

4. (Optional) **Azure OpenAI API Access**
   - For cloud-based AI analysis
   - You can use just the local Microsoft Phi-4 model if preferred

## Installation Steps

### 1. Clone the Repository

If you haven't already, clone this repository to your local machine:

```bash
git clone https://github.com/yourusername/cloud-finops-with-llm.git
cd cloud-finops-with-llm
```

### 2. Set Up the Environment

The easiest way to get started is to use the provided script:

```bash
./run_app.sh
```

This script will:
- Create a virtual environment
- Install dependencies
- Set up the initial configuration file
- Start the PostgreSQL database
- Run the Streamlit application

### 3. Manual Setup (Alternative)

If you prefer to set up manually:

1. Create a virtual environment and install dependencies:
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure your environment variables:
```bash
cp .env.example .env
# Edit the .env file with your credentials
```

3. Start the PostgreSQL database:
```bash
docker-compose up -d
```

4. Initialize the database:
```bash
python utils/init_db.py
```

5. Download the Microsoft Phi-4 model:
```bash
python utils/download_model.py
```

6. Start the application:
```bash
streamlit run main.py
```

## Using the Dashboard

1. **Login**:
   - When you first access the dashboard, you'll need to provide your AWS access key and secret key
   - This authenticates you to retrieve your AWS cost data

2. **Dashboard Navigation**:
   - **Dashboard**: Overview of your AWS costs
   - **Cost Explorer**: Detailed analysis of costs by service, region, etc.
   - **Forecast**: Cost projections using AWS and AI models
   - **Recommendations**: Cost optimization suggestions
   - **Chat Assistant**: Natural language interface for cost queries

3. **LLM Selection**:
   - In the sidebar, you can choose between:
     - **Local (Phi-4)**: Uses the local Microsoft Phi-4 model with M3 GPU acceleration
     - **Azure OpenAI**: Uses Azure's cloud-based OpenAI models (requires Azure credentials)

4. **Date Range Selection**:
   - Use the date pickers in the sidebar to select the time period for analysis

## Troubleshooting

### Database Issues
- Ensure Docker is running
- Check docker logs: `docker logs finops-postgres`
- Restart database: `docker-compose restart`

### AWS Access Issues
- Verify your IAM user has Cost Explorer permissions
- Ensure the correct access key and secret key are entered

### Model Issues
- If the Phi-4 model doesn't load, try running the download script again:
  ```bash
  python utils/download_model.py
  ```
- Check you have enough disk space (the model requires about 2GB)

## Next Steps

After getting comfortable with the basic features:

1. **Custom Dashboards**: Use the Settings page to customize your views
2. **Budget Alerts**: Configure alerts for cost thresholds
3. **API Integration**: Integrate with other services using the provided utilities
4. **Custom Analysis**: Use the chat interface for advanced cost queries

For any issues or questions, please refer to the project documentation or open an issue on GitHub.

Happy cost optimizing!
