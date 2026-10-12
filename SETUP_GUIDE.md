# Setup Guide for Autonomous Data Analyst

## Quick Setup

### 1. Configure API Keys

The system requires Google Gemini API keys for AI-powered analysis.

**Option A: Using Environment Variables (Recommended)**

Create a file named `.env` in the `backend` directory:

```bash
cd backend
copy .env.example .env
```

Edit the `.env` file and add your Gemini API key:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Option B: Using System Environment Variables**

Set the environment variable in your system:

```bash
set GEMINI_API_KEY=your_gemini_api_key_here
```

**Note**: Without API keys, the system will still function using rule-based analysis, but AI-powered features will be disabled.

### 2. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Start the Application

**Windows - Quick Start:**

```bash
# Terminal 1 - Backend
start-backend.bat

# Terminal 2 - Frontend
start-frontend.bat
```

**Manual Start:**

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 4. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Using the System

### Step 1: Upload Dataset
1. Open http://localhost:3000
2. Click "Select File" and choose a CSV or Excel file
3. Click "Upload Dataset"
4. Review the automatically generated dataset profile and quality report

### Step 2: Define Analysis Goal
1. Enter your analysis goal in natural language
   - Example: "Analyze this sales dataset and find why sales decreased in some regions"
2. Click "Start Analysis"

### Step 3: Monitor Progress
The system will:
- ✅ Profile the dataset
- ✅ Analyze data quality
- ✅ Create an AI-powered analysis plan
- ✅ Generate multiple hypotheses
- ✅ Execute analysis tools (Python, SQL, Statistics)
- ✅ Generate visualizations
- ✅ Detect anomalies
- ✅ Verify results
- ✅ Generate final report

### Step 4: Review Results
- **Analysis Plan**: See the AI-generated plan
- **Hypotheses**: View all generated hypotheses
- **Evidence**: See tool execution results
- **Visualizations**: View interactive charts
- **Report**: Read the comprehensive final report with findings and recommendations

## Features

### AI-Powered Analysis
- **Natural Language Understanding**: Describe goals in plain English
- **Intelligent Planning**: AI creates detailed analysis plans
- **Smart Hypotheses**: Multiple testable hypotheses generated automatically
- **Tool Selection**: AI selects the best tools for each analysis
- **Result Interpretation**: AI interprets statistical results
- **Recommendations**: Actionable insights based on analysis

### Complete Pipeline
1. Dataset Profiling → Structure, types, missing values, distributions
2. Data Quality → Quality report with recommendations
3. Analysis Planning → AI-driven plan creation
4. Hypothesis Generation → Multiple testable hypotheses
5. Tool Execution → Python, SQL, Statistics, ML
6. Evidence Collection → Complete traceability
7. Verification → Cross-check and validation
8. Revision → Automatic re-analysis if needed
9. Report Generation → Comprehensive findings

### Real-Time Updates
- WebSocket connections provide live progress updates
- See each step as it completes
- Real-time status indicators

## Troubleshooting

### API Key Issues
If you see "No Gemini API key configured":
- Ensure `.env` file exists in `backend` directory
- Check that the API key is correctly formatted
- Try setting the environment variable directly

### Backend Won't Start
- Ensure Python 3.8+ is installed
- Run `pip install -r requirements.txt` in backend directory
- Check if port 8000 is already in use

### Frontend Won't Start
- Ensure Node.js 18+ is installed
- Run `npm install` in frontend directory
- Check if port 3000 is already in use

### Analysis Fails
- Check backend logs for errors
- Ensure dataset is valid CSV or Excel
- Verify API key is working
- Try with a smaller dataset first

## Sample Dataset

A sample sales dataset is provided in `sample-data/sales.csv` with 100 records including:
- Order information
- Regional data
- Product categories
- Sales and profit metrics
- Customer segments

Use this to test the system before using your own data.

## Architecture

```
User → Next.js Dashboard → FastAPI Backend → Analysis Pipeline
                                     ↓
                            Gemini AI (LLM Services)
                                     ↓
                            Analysis Modules
                                     ↓
                            Evidence Store
                                     ↓
                            Verification Engine
                                     ↓
                            Report Generator
```

## Support

For issues or questions:
1. Check the logs in both backend and frontend terminals
2. Review the API documentation at http://localhost:8000/docs
3. Ensure all dependencies are installed correctly
4. Verify API key configuration
