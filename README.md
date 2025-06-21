# AWS FinOps Application

A comprehensive FinOps solution for AWS cost management and optimization using Azure OpenAI, Microsoft Phi-4 SLM, Hugging Face, and LangChain.

## Overview

This application provides a full-featured AWS cost management and optimization platform with:

- AWS cost monitoring and analysis by service, region, and usage type
- AI-powered cost forecasting using both Azure OpenAI and local Microsoft Phi-4 models
- Intelligent cost optimization recommendations
- Interactive chat assistant for natural language queries about your AWS costs
- PostgreSQL database for historical cost data storage and analysis
- Streamlit UI for an intuitive user experience

## Features

- **AWS Cost Analysis**
  - Real-time cost data retrieval using the AWS Cost Explorer API
  - Cost breakdown by service, region, and usage type
  - Interactive visualizations and reports

- **AI-Powered Forecasting**
  - Cost forecasting using both AWS Cost Explorer and AI models
  - Historical trend analysis
  - Anomaly detection

- **Cost Optimization**
  - Intelligent recommendations for cost savings
  - Resource right-sizing suggestions
  - Reserved instance and Savings Plans analysis

- **Natural Language Chat Interface**
  - Query your AWS cost data using natural language
  - Get insights and recommendations through conversation
  - Powered by Azure OpenAI and Microsoft Phi-4 models

- **Local LLM with GPU Acceleration**
  - Utilizes macOS M3 GPU acceleration for Phi-4 model
  - Privacy-friendly option for cost analysis without sending data to external APIs

## Technology Stack

- **Backend**: Python 3.12
- **Frontend**: Streamlit
- **Database**: PostgreSQL (via Docker)
- **AI Models**:
  - Microsoft Phi-4 (local inference with GPU acceleration)
  - Azure OpenAI (cloud-based inference)
- **Frameworks**:
  - LangChain for LLM orchestration
  - SQLAlchemy for database operations
  - Pandas for data manipulation
  - Plotly for visualizations

## Prerequisites

- Python 3.12
- Docker and Docker Compose (for PostgreSQL)
- AWS account with Cost Explorer API access
- Azure OpenAI API access (optional)
- macOS with M3 chip for local LLM GPU acceleration

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/cloud-finops-with-llm.git
cd cloud-finops-with-llm
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your AWS credentials, Azure OpenAI keys, etc.
```

5. Start the PostgreSQL database:

```bash
docker-compose up -d
```

6. Run the application:

```bash
# Option 1: Using the shell script (recommended)
./run_app.sh

# Option 2: Using the Python launcher
python3 launch_app.py

# Option 3: Using main.py (which calls the launcher)
python3 main.py
```

## Configuration

Edit the `.env` file to configure:

- AWS credentials
- Azure OpenAI API settings
- PostgreSQL connection details
- Local LLM settings

## Usage

1. Access the web interface at http://localhost:8501
2. Login with your AWS credentials
3. Navigate the dashboard to explore your AWS costs
4. Use the chat assistant to ask natural language questions about your costs
5. View and implement cost optimization recommendations

## Production Readiness Testing

A comprehensive testing procedure has been developed to ensure this application is production-ready. The testing covers all critical components and confirms their functionality in a local environment before deployment.

### Testing Requirements

- **Hardware**:
  - Python 3.12
  - Docker and Docker Compose
  - macOS with M3 chip (for GPU acceleration)
  - Minimum 8GB RAM
  - At least 10GB free disk space

- **Accounts & Credentials**:
  - AWS account with Cost Explorer API access
  - Azure OpenAI account (optional)

### Testing Process

1. **Environment Verification**
   - Python version and dependency installation
   - Docker and Docker Compose availability
   - System resource verification

2. **Database Testing**
   - PostgreSQL container startup and health check
   - Schema initialization
   - Connection verification
   - Data persistence validation

3. **LLM Setup & Testing**
   - Model download and storage
   - Inference testing with GPU acceleration
   - Response quality validation
   - Memory usage optimization

4. **AWS Integration Testing**
   - Credential validation
   - API connectivity testing
   - Cost data retrieval
   - Data storage in PostgreSQL

5. **Application Functionality**
   - UI rendering and responsiveness
   - Authentication flow
   - Cost visualization accuracy
   - LLM-powered recommendations quality
   - Chat interface functionality

6. **Security & Performance**
   - Authentication mechanism verification
   - API key management
   - Response time benchmarking
   - Load testing with large datasets

### Testing Results

Detailed testing results are available in [testing_logs/test_results.md](testing_logs/test_results.md)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
